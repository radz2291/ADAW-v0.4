"""Killable native backend. No project database access; only job staging paths."""
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import sys
import time
import traceback

from app.contracts import RenderGraph, catalog_hash, digest, file_hash
from app.errors import AdawError


def report_safe(value, path="result", warnings=None):
    """Represent invalid native metadata explicitly; never coerce it to success/0.

    Controls and audio are separately required finite before this reporting step.
    """
    warnings = warnings if warnings is not None else []
    if isinstance(value, float) and not math.isfinite(value):
        warnings.append({"code": "NATIVE_METADATA_NONFINITE", "path": path, "value": str(value)})
        return {"status": "UNAVAILABLE", "native_value": str(value)}
    if isinstance(value, dict):
        return {k: report_safe(v, path+"."+str(k), warnings) for k,v in value.items()}
    if isinstance(value, list):
        return [report_safe(v, path+f"[{i}]", warnings) for i,v in enumerate(value)]
    return value


class DawDreamerBackend:
    def __init__(self):
        started = time.perf_counter()
        # Native import is deliberately confined to this module's worker entrypoint.
        import dawdreamer
        self.daw = dawdreamer
        self.import_seconds = time.perf_counter() - started

    def environment(self):
        return {"os": platform.platform(), "machine": platform.machine(),
                "python": sys.version, "executable": sys.executable,
                "packages": {n: importlib.metadata.version(n) for n in
                             ("dawdreamer", "numpy", "scipy", "soundfile", "pyloudnorm")},
                "native_module_sha256": file_hash(self.daw.dawdreamer.__file__),
                "import_seconds": self.import_seconds,
                "isolation": "native subprocess crash containment only; same-user filesystem/network rights"}

    def probe(self, request):
        e = self.daw.RenderEngine(request["sample_rate"], request["block_size"])
        start = time.perf_counter()
        p = e.make_plugin_processor("probe", request["plugin_path"])
        return {"parameters": p.get_parameters_description(),
                "inputs": p.get_num_input_channels(), "outputs": p.get_num_output_channels(),
                "load_seconds": time.perf_counter() - start,
                "values": {str(d["index"]): p.get_parameter(d["index"]) for d in p.get_parameters_description()},
                "environment": self.environment()}

    def render(self, request, stage):
        import numpy as np
        import soundfile as sf
        g = RenderGraph.parse(request["graph"]).value
        started = time.perf_counter()
        e = self.daw.RenderEngine(g["sample_rate"], g["block_size"])
        graph, processors, reports, source_hashes = [], {}, {}, {}
        for n in g["nodes"]:
            c, node_started = n["config"], time.perf_counter()
            if n["kind"] == "tone":
                t = np.arange(g["frames"], dtype=np.float64) / g["sample_rate"]
                mono = c["amplitude"] * np.sin(2 * np.pi * c["frequency_hz"] * t)
                mono[:c["onset_frame"]] = 0
                pcm = np.tile(mono.astype(np.float32), (n["channels"], 1))
                source_hashes[n["id"]] = digest(pcm.astype("<f4").tobytes())
                p = e.make_playback_processor(n["id"], pcm)
                catalog = []
            elif n["kind"] == "samples":
                pcm = np.zeros((2, g["frames"]), dtype=np.float32)
                cache = {}
                for event in c["events"]:
                    sha = event["asset_sha256"]
                    if sha not in cache:
                        path = stage / (sha + ".wav")
                        if file_hash(path) != sha:
                            raise AdawError("ASSET_MISSING", "Staged sample hash mismatch")
                        sample, rate = sf.read(path, dtype="float32", always_2d=True)
                        if rate != g["sample_rate"] or sample.shape[1] not in (1, 2) or not np.isfinite(sample).all():
                            raise AdawError("VALIDATION_ERROR", "Sample requires matching rate, mono/stereo finite audio")
                        cache[sha] = np.repeat(sample, 2, axis=1) if sample.shape[1] == 1 else sample
                    sample = cache[sha]
                    length = min(len(sample), event["duration_frames"])
                    segment = sample[:length].T.copy()
                    fade = min(event["fade_frames"], length // 2)
                    if fade:
                        segment[:, :fade] *= np.linspace(0, 1, fade)
                        segment[:, -fade:] *= np.linspace(1, 0, fade)
                    # Balance pan: center is unity; no implicit center attenuation.
                    segment *= np.array([min(1, 1-event["pan"]), min(1, 1+event["pan"])])[:, None] * event["gain"]
                    start = event["start_frame"]
                    pcm[:, start:start+length] += segment
                source_hashes[n["id"]] = digest(pcm.astype("<f4").tobytes())
                p = e.make_playback_processor(n["id"], pcm)
                catalog = []
            elif n["kind"] in ("faust", "faust_synth"):
                p = e.make_faust_processor(n["id"])
                p.set_dsp_string(c["source"])
                if n["kind"] == "faust_synth":
                    p.num_voices = c["voices"]
                    p.release_length = c["release_seconds"]
                try:
                    if not p.compile():
                        raise RuntimeError("Faust compile returned false")
                except Exception as exc:
                    raise AdawError("MODULE_COMPILE_FAILED", str(exc), node=n["id"]) from exc
                source_hashes[n["id"]] = digest(c["source"].encode())
                catalog = p.get_parameters_description()
                addresses = {d["name"]: d for d in catalog}
                for key, value in c["parameters"].items():
                    if key not in addresses:
                        raise AdawError("VALIDATION_ERROR", "Faust binding missing", binding=key)
                    d = addresses[key]
                    if not d["min"] <= value <= d["max"]:
                        raise AdawError("VALIDATION_ERROR", "Faust value outside exposed range", binding=key)
                    p.set_parameter(key, value)
                for key, points in c.get("automation", {}).items():
                    if key not in addresses:
                        raise AdawError("VALIDATION_ERROR", "Faust automation binding missing", binding=key)
                    descriptor = addresses[key]
                    lane = np.empty(g["frames"], dtype=np.float32)
                    for i, (frame, value) in enumerate(points):
                        if not descriptor["min"] <= value <= descriptor["max"]:
                            raise AdawError("VALIDATION_ERROR", "Faust automation outside exposed range", binding=key)
                        end = points[i + 1][0] if i + 1 < len(points) else g["frames"]
                        lane[frame:end] = value
                    p.set_automation(key, lane)
                for note in c.get("midi", []):
                    p.add_midi_note(note["note"], note["velocity"], note["start_frame"] / g["sample_rate"], note["duration_frames"] / g["sample_rate"])
            else:
                resolved = request["plugins"][c["registry_id"]]
                p = e.make_plugin_processor(n["id"], resolved["path"])
                catalog = p.get_parameters_description()
                if catalog_hash(catalog) != resolved["catalog_sha256"]:
                    raise AdawError("PLUGIN_CAPABILITY_UNVERIFIED", "Parameter catalog changed", catalog=catalog,
                                    expected_sha256=resolved["catalog_sha256"], actual_sha256=catalog_hash(catalog))
                if c["state_sha256"]:
                    state = stage / (c["state_sha256"] + ".state")
                    if file_hash(state) != c["state_sha256"]:
                        raise AdawError("VALIDATION_ERROR", "Plugin state hash mismatch")
                    try:
                        p.load_state(str(state))
                    except Exception as exc:
                        raise AdawError("PLUGIN_CAPABILITY_UNVERIFIED", "Opaque state restore failed: " + str(exc)) from exc
                    catalog = p.get_parameters_description()
                    if catalog_hash(catalog) != resolved["catalog_sha256"]:
                        raise AdawError("PLUGIN_CAPABILITY_UNVERIFIED", "Restored state changed parameter interface")
                indices = {d["index"] for d in catalog}
                for key, value in c["parameters"].items():
                    if int(key) not in indices:
                        raise AdawError("VALIDATION_ERROR", "Missing VST parameter", binding=key)
                    p.set_parameter(int(key), value)
                    if not math.isfinite(p.get_parameter(int(key))):
                        raise AdawError("PLUGIN_CAPABILITY_UNVERIFIED", "Active VST control returned nonfinite value", binding=key)
                for note in c["midi"]:
                    p.add_midi_note(note["note"], note["velocity"], note["start_frame"] / g["sample_rate"],
                                    note["duration_frames"] / g["sample_rate"])
                for key, points in c["automation"].items():
                    if int(key) not in indices:
                        raise AdawError("VALIDATION_ERROR", "Missing automation parameter")
                    lane = np.empty(g["frames"], dtype=np.float32)
                    for i, (frame, value) in enumerate(points):
                        end = points[i + 1][0] if i + 1 < len(points) else g["frames"]
                        lane[frame:end] = value
                    p.set_automation(int(key), lane)
            channels_in = sum(processors[i].get_num_output_channels() for i in n["inputs"])
            if n["kind"] not in ("tone", "samples") and channels_in != p.get_num_input_channels():
                raise AdawError("ROUTING_UNSUPPORTED", "Input channel mismatch", node=n["id"], supplied=channels_in, expected=p.get_num_input_channels())
            if p.get_num_output_channels() != n["channels"]:
                raise AdawError("ROUTING_UNSUPPORTED", "Output channel mismatch", node=n["id"])
            reports[n["id"]] = {"catalog": catalog, "prepare_seconds": time.perf_counter() - node_started}
            if n["kind"] == "vst":
                # Capture pre-render state, before MIDI/tails can change transient state.
                state_path = stage / (n["id"] + ".state")
                p.save_state(str(state_path))
                reports[n["id"]]["state_file"] = state_path.name
                reports[n["id"]]["state_sha256"] = file_hash(state_path)
                reports[n["id"]]["values"] = {str(d["index"]): p.get_parameter(d["index"]) for d in catalog}
            processors[n["id"]] = p
            if n["id"] in request.get("record_nodes", []):
                p.record = True
            graph.append((p, n["inputs"]))
        e.load_graph(graph)
        prepare_seconds = time.perf_counter() - started
        start = time.perf_counter()
        seconds = g["frames"] / g["sample_rate"]
        if seconds * g["sample_rate"] < g["frames"]:
            # DawDreamer truncates duration * sample rate to a frame count.
            seconds = math.nextafter(seconds, math.inf)
        if not e.render(seconds):
            raise AdawError("RENDER_FAILED", "Engine returned false")
        cold = time.perf_counter() - start
        audio = e.get_audio().T.copy()
        stems = {}
        for node_id in request.get("record_nodes", []):
            stem_path = stage / (node_id + ".wav")
            sf.write(stem_path, e.get_audio(node_id).T, g["sample_rate"], subtype="FLOAT")
            stems[node_id] = {"file": stem_path.name, "sha256": file_hash(stem_path)}
        start = time.perf_counter()
        if request.get("benchmark", True):
            e.render(seconds)
        warm = time.perf_counter() - start if request.get("benchmark", True) else None
        second = e.get_audio().T
        if audio.shape != (g["frames"], g["nodes"][-1]["channels"]) or not np.isfinite(audio).all():
            raise AdawError("RENDER_FAILED", "Unexpected shape or invalid samples", shape=list(audio.shape))
        sf.write(stage / "output.wav", audio, g["sample_rate"], subtype="FLOAT")
        return {"file": "output.wav", "audio_sha256": file_hash(stage / "output.wav"),
                "pcm_sha256": digest(audio.astype("<f4").tobytes()),
                "source_hashes": source_hashes, "nodes": reports, "stems": stems,
                "timing": {"prepare_seconds": prepare_seconds, "cold_render_seconds": cold, "warm_render_seconds": warm},
                "warm_pcm_identical": bool(np.array_equal(audio, second)) if request.get("benchmark", True) else None,
                "warm_max_abs_delta": float(np.max(np.abs(audio - second))) if request.get("benchmark", True) else None,
                "environment": self.environment()}


def main():
    request_path = Path(sys.argv[1]).resolve()
    stage = request_path.parent
    request = json.loads(request_path.read_text(encoding="utf-8"))
    try:
        if request["operation"] == "fault_crash":
            os._exit(73)  # explicit synthetic abrupt-exit fixture, not a real VST crash
        if request["operation"] == "fault_timeout":
            time.sleep(request["sleep_seconds"])
        backend = DawDreamerBackend()
        if request["operation"] == "doctor":
            data = backend.environment()
        elif request["operation"] == "probe":
            data = backend.probe(request)
        elif request["operation"] == "render":
            data = backend.render(request, stage)
        elif request["operation"] == "module_validate":
            e = backend.daw.RenderEngine(request["sample_rate"], request["block_size"])
            p = e.make_faust_processor("validation")
            p.set_dsp_string(request["source"])
            try:
                if not p.compile():
                    raise RuntimeError("Faust compilation returned false")
            except Exception as exc:
                raise AdawError("MODULE_COMPILE_FAILED", str(exc)) from exc
            data = {"source_sha256": digest(request["source"].encode()), "catalog": p.get_parameters_description(),
                    "inputs": p.get_num_input_channels(), "outputs": p.get_num_output_channels()}
        else:
            raise AdawError("NOT_IMPLEMENTED", "Unknown worker operation")
        result = {"ok": True, "data": data}
    except Exception as exc:
        traceback.print_exc()
        result = {"ok": False, "error": {"code": getattr(exc, "code", "RENDER_FAILED"),
                  "message": str(exc), "details": getattr(exc, "details", {})}}
    warnings = []
    result = report_safe(result, warnings=warnings)
    result["warnings"] = warnings
    (stage / "result.json").write_text(json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())

