"""Execute retained real-audio G0 checks. Every PASS follows actual assertions."""
import argparse
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import shutil
import traceback

import numpy as np
import pyloudnorm as pyln
import soundfile as sf

from app.contracts import canonical, digest, file_hash
from app.errors import AdawError
from app.service import Service
from tools.fixtures import faust_fixture, graph, node, notes, tone, vst_node


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def pcm(result):
    return sf.read(result["audio_path"], always_2d=True)[0]


def compact(result):
    r = copy.deepcopy(result)
    for n in r["data"]["nodes"].values():
        catalog = n.pop("catalog")
        n["catalog_count"] = len(catalog)
        n["catalog_sha256"] = digest(canonical(catalog))
        values = n.pop("values", {})
        n["selected_values"] = {k: v for k, v in values.items() if k in ("0", "1", "4", "12")}
    return r


def harmonic_ratio(result):
    # Integer-cycle steady sine bins: 220 Hz fundamental and 660 Hz third harmonic.
    audio = pcm(result)[48000:96000, 0]
    spec = abs(np.fft.rfft(audio))
    return float(spec[660] / spec[220])


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True)
    p.add_argument("--timeout", type=float, required=True)
    p.add_argument("--report", required=True)
    args = p.parse_args()
    s = Service(args.root)
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = {"scope": "G0 bounded engineering proof; fixture VSTs; no full permanent-test acceptance",
              "time_utc": datetime.now(timezone.utc).isoformat(), "checks": [], "renders": {},
              "listening": "NOT_EVALUATED", "sidechain": "NOT_EVALUATED", "owner_plugin_collection": "UNTESTED"}
    report["known_limitations"] = ["PurestGain VST2 opaque state restore fails in DawDreamer 0.9.0 because its loader creates a plugin editor. Original failure retained in run-001.json. No exception suppressed or parameter-only restore substituted.",
        "Consolidated default wet processor has nonidentical fresh/warm PCM (run-003.json). Strict state test explicitly uses Dry/Wet=0 and its active Output Level gain; this does not certify the wet algorithm. Complete wet pipeline remains D3."]
    renders = {}

    def save():
        report_path.write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")

    def case(name, action):
        print("RUN", name, flush=True)
        try:
            detail = action()
            report["checks"].append({"id": name, "status": "PASS", "evidence": detail})
            print("PASS", name, flush=True)
        except Exception as exc:
            traceback.print_exc()
            report["checks"].append({"id": name, "status": "FAIL", "error": str(exc), "details": getattr(exc, "details", {})})
            print("FAIL", name, str(exc), flush=True)
        save()

    def render(name, g, service=s, commit=False):
        result = service.render(g, args.timeout, commit, service.inspect()["head"] if commit else None)
        renders[name] = result
        report["renders"][name] = compact(result)
        # Source is a reproduction input, not an authoritative filesystem edit.
        path = report_path.parent / "graphs" / report_path.stem / (name + ".json")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(canonical(g))
        save()
        return result

    def expect_failure(action, code):
        before = s.inspect()
        last_hash = file_hash(s.content / before["last_playable"]) if before["last_playable"] else None
        try:
            action()
        except AdawError as exc:
            check(exc.code == code, f"Expected {code}; got {exc.code}")
            check(s.inspect() == before, "Source head or last playable changed after failure")
            if last_hash:
                check(file_hash(s.content / before["last_playable"]) == last_hash, "Playable bytes changed")
            return {"expected_code": code, "head_unchanged": before["head"], "last_playable_sha256": last_hash,
                    "details": exc.details}
        raise AssertionError("Expected failure did not occur")

    case("G0-01.windows_environment", lambda: s.run_worker({"operation": "doctor"}, args.timeout))

    def faust():
        dry = render("faust-bypass", faust_fixture(), commit=True)
        low = render("faust-drive-1", faust_fixture(1))
        high = render("faust-drive-4", faust_fixture(4), commit=True)
        trim = render("faust-trim-half", faust_fixture(4, trim=0.25, multitrack=False))
        ref = render("faust-trim-reference", faust_fixture(4, multitrack=False))
        repeat = render("faust-repeat", faust_fixture(4))
        dry_ratio, low_ratio, high_ratio = map(harmonic_ratio, (dry, low, high))
        check(high_ratio > 5 * low_ratio and low_ratio > 100 * dry_ratio, "Drive did not increase third harmonic")
        check(np.max(abs(pcm(trim) - 0.5 * pcm(ref))) < 1e-7, "Output trim did not halve PCM")
        check(high["data"]["pcm_sha256"] == repeat["data"]["pcm_sha256"], "Fresh-worker Faust PCM differs")
        check(high["data"]["warm_pcm_identical"], "Warm Faust PCM differs")
        return {"third_harmonic_ratio": {"bypass": dry_ratio, "drive_1": low_ratio, "drive_4": high_ratio},
                "trim_max_error": float(np.max(abs(pcm(trim) - 0.5 * pcm(ref)))),
                "fresh_worker_pcm_identical": True}
    case("RWT-05.faust_multitrack_subset", faust)

    def invalid_faust():
        g = faust_fixture(4)
        g["nodes"][1]["config"]["source"] = "process = deliberately invalid !!!;"
        return expect_failure(lambda: s.render(g, args.timeout, True, s.inspect()["head"]), "MODULE_COMPILE_FAILED")
    case("RWT-06.invalid_faust_subset", invalid_faust)

    def removed_binding():
        g = faust_fixture(4)
        g["nodes"][1]["config"]["source"] = "process = _,_;"
        return expect_failure(lambda: s.render(g, args.timeout, True, s.inspect()["head"]), "VALIDATION_ERROR")
    case("RWT-05.removed_faust_binding_subset", removed_binding)
    case("RWT-06.abrupt_worker_exit_subset", lambda: expect_failure(lambda: s.run_worker({"operation": "fault_crash"}, args.timeout), "WORKER_CRASHED"))
    case("RWT-06.worker_timeout_subset", lambda: expect_failure(lambda: s.run_worker({"operation": "fault_timeout", "sleep_seconds": 10}, 0.5), "TIMEOUT"))
    case("RWT-06.service_reopen_subset", lambda: {"reopened": Service(args.root).inspect()} if Service(args.root).inspect() == s.inspect() else (_ for _ in ()).throw(AssertionError("Reopen differs")))
    case("RWT-06.stale_commit_subset", lambda: expect_failure(lambda: s.render(faust_fixture(), args.timeout, True, "wrong-head"), "STALE_REVISION"))

    def timing():
        onset = 12345  # deliberately not block aligned, temporary timing fixture
        g = graph([tone("timing", 997, 0.1, onset)], seconds=1)
        r = render("onset", g)
        actual = int(np.flatnonzero(abs(pcm(r)[:, 0]) > 1e-9)[0])
        check(actual == onset, "Playback onset shifted")
        return {"requested_onset_frame": onset, "measured_onset_frame": actual, "block_size": 256}
    case("G0-04.sample_timing", timing)

    def calibration():
        results = []
        for name, expected in [("1770-2_Comp_23LKFS_1000Hz_2ch.wav", -23),
                               ("1770-2_Comp_AbsGateTest.wav", -69.5),
                               ("1770-2_Comp_RelGateTest.wav", -10)]:
            path = Path(".local/calibration") / name
            audio, rate = sf.read(path)
            measured = pyln.Meter(rate).integrated_loudness(audio)
            results.append({"file": str(path.resolve()), "sha256": file_hash(path), "expected_lufs": expected,
                            "measured_lufs": measured, "tolerance_lu": 0.1})
            check(abs(measured - expected) <= 0.1, f"Calibration failed: {name}")
        return {"method": "Three upstream BS.1770 compliance vectors: tone, absolute gate, relative gate. Not a full meter conformance suite.",
                "upstream_commit": Path(".local/calibration/upstream-commit.txt").read_text().strip(), "vectors": results}
    case("G0-04.loudness_calibration_subset", calibration)

    plugins = json.loads(Path(".local/fixture-plugins.json").read_text())
    synth = plugins["instrument"]["entry"]["registry_id"]
    effect = plugins["effect"]["entry"]["registry_id"]
    report["plugin_probes"] = {role: {"identity": p["entry"], "load_seconds": p["probe"]["data"]["load_seconds"],
        "inputs": p["probe"]["data"]["inputs"], "outputs": p["probe"]["data"]["outputs"],
        "parameter_count": len(p["probe"]["data"]["parameters"]), "stage": p["probe"]["stage"]} for role, p in plugins.items()}

    def vst_instrument():
        baseline = render("dexed-base", graph([vst_node("synth", synth, midi=notes(), parameters={"0": 0.8})], 4))
        changed = render("dexed-output-lower", graph([vst_node("synth", synth, midi=notes(), parameters={"0": 0.4})], 4))
        check(baseline["quality"]["rms"] > 1e-5, "MIDI instrument is silent")
        check(changed["quality"]["rms"] < baseline["quality"]["rms"] * 0.8, "Output control did not reduce RMS")
        state = changed["data"]["nodes"]["synth"]["state_sha256"]
        restored = render("dexed-restored", graph([vst_node("synth", synth, midi=notes(), state=state)], 4))
        values = changed["data"]["nodes"]["synth"]["values"]
        restored_values = restored["data"]["nodes"]["synth"]["values"]
        check(all(abs(v - restored_values[k]) < 1e-6 for k, v in values.items()), "State parameter restoration differs")
        delta = float(np.max(abs(pcm(changed) - pcm(restored))))
        # RMS envelope is the declared behavioral check; exact PCM reported independently.
        ratio = restored["quality"]["rms"] / changed["quality"]["rms"]
        check(0.95 <= ratio <= 1.05, "Restored instrument level differs >5% (fixture tolerance)")
        return {"base_rms": baseline["quality"]["rms"], "changed_rms": changed["quality"]["rms"],
                "state_sha256": state, "all_parameters_restored": True, "restored_rms_ratio": ratio,
                "fresh_worker_pcm_identical": delta == 0, "max_abs_delta": delta,
                "replay_grade": "D1 observed same-host" if delta == 0 else "D3 environment-dependent; PCM not identical"}
    case("RWT-11.fixture_instrument_midi_state_subset", vst_instrument)

    def vst_effect():
        def chain(value=0.5, state=None, automation=None):
            return graph([tone("source", 997, 0.1), vst_node("gain", effect, ["source"],
                parameters={} if state else {"4": 0, "12": value}, state=state, automation=automation)], 4)
        base = render("consolidated-base", chain())
        changed = render("consolidated-lower", chain(0.4))
        state = changed["data"]["nodes"]["gain"]["state_sha256"]
        restored = render("consolidated-restored", chain(state=state))
        automated = render("consolidated-automated", chain(automation={"12": [[0, 0.5], [96000, 0.4]]}))
        check(changed["quality"]["rms"] < base["quality"]["rms"] * 0.8, "Effect gain did not change output")
        values = changed["data"]["nodes"]["gain"]["values"]
        check(values == restored["data"]["nodes"]["gain"]["values"], "Effect state values differ")
        delta = float(np.max(abs(pcm(changed) - pcm(restored))))
        check(delta < 1e-6, "Restored effect exceeds 1e-6 PCM tolerance")
        a = pcm(automated)
        ratio = float(np.sqrt(np.mean(a[144000:] ** 2)) / np.sqrt(np.mean(a[24000:48000] ** 2)))
        check(ratio < 0.8, "Automation did not reduce late-window level")
        return {"base_rms": base["quality"]["rms"], "changed_rms": changed["quality"]["rms"],
                "state_sha256": state, "restored_max_abs_delta": delta, "automated_late_early_rms_ratio": ratio,
                "configuration": "Dry/Wet=0; Output Level is active VST gain processing, not plugin bypass",
                "automation": "hold lane at sample 96000; host/plugin smoothing not claimed sample-exact",
                "fresh_worker_pcm_identical": delta == 0}
    case("RWT-11.fixture_effect_automation_state_subset", vst_effect)

    def reusable_pipeline():
        g = faust_fixture(2)
        g["nodes"][0] = vst_node("tone-a", synth, midi=notes(), parameters={"0": 0.4})
        g["nodes"].append(vst_node("final-gain", effect, ["master"], parameters={"12": 0.45}))
        g["output"] = "final-gain"
        first = render("pipeline-project-a", g, commit=True)
        other = Service(str(Path(args.root).with_name(Path(args.root).name + "-independent")))
        for role in plugins.values():
            entry = role["entry"]
            other.authorize_plugin(entry["path"], entry["provenance"])
            other.probe_plugin(entry["registry_id"], 48000, 256, args.timeout)
        tuned = copy.deepcopy(g)
        tuned["nodes"][-1]["config"]["parameters"]["12"] = 0.4
        before = s.inspect()
        second = render("pipeline-project-b", tuned, other, commit=True)
        check(s.inspect() == before, "Independent project mutated original")
        check(first["data"]["pcm_sha256"] != second["data"]["pcm_sha256"], "Tuned pipeline PCM did not change")
        check(second["quality"]["rms"] > 0, "Pipeline output silent")
        return {"first_head": before["head"], "second_head": other.inspect()["head"], "independent": True,
                "template_source_sha256": first["source_sha256"], "tuned_source_sha256": second["source_sha256"]}
    case("RWT-12.fixture_pipeline_reuse_subset", reusable_pipeline)

    def denied():
        g = graph([vst_node("blocked", "not-authorized", midi=notes())], 4)
        return expect_failure(lambda: s.render(g, args.timeout, True, s.inspect()["head"]), "PLUGIN_UNAPPROVED")
    case("RWT-05.plugin_permission_denial_subset", denied)

    def missing_or_changed_plugin():
        original = plugins["limited_effect"]["entry"]["path"]
        sandbox = s.staging / "dependency-fault"
        sandbox.mkdir(exist_ok=True)
        copied = sandbox / "PurestGain64.dll"
        shutil.copyfile(original, copied)
        entry = s.authorize_plugin(copied, "Temporary copy of approved PurestGain for dependency-failure test")
        # Same binary ID may resolve the earlier installed path; use a distinct filename identity.
        variant = sandbox / "dependency-fixture.dll"
        copied.replace(variant)
        entry = s.authorize_plugin(variant, "Owner-approved fixture copy for dependency-failure test")
        variant.unlink()
        missing = expect_failure(lambda: s.plugin(entry["registry_id"]), "PLUGIN_MISSING")
        variant.write_bytes(b"deliberately corrupted fixture; must never load")
        changed = expect_failure(lambda: s.plugin(entry["registry_id"]), "PLUGIN_CAPABILITY_UNVERIFIED")
        return {"missing": missing, "changed": changed, "native_load_attempted": False}
    case("RWT-12.missing_changed_dependency_subset", missing_or_changed_plugin)

    report["failed_checks"] = sum(c["status"] == "FAIL" for c in report["checks"])
    report["permanent_tests"] = {f"RWT-{i:02d}": {"status": "NOT_EVALUATED", "note": "Full long-term scenario not evaluated at G0"} for i in range(1, 13)}
    for i in (5, 6, 11, 12):
        subset = [c for c in report["checks"] if c["id"].startswith(f"RWT-{i:02d}")]
        report["permanent_tests"][f"RWT-{i:02d}"]["g0_subset"] = "FAIL" if any(c["status"] == "FAIL" for c in subset) else "PASS"
        report["permanent_tests"][f"RWT-{i:02d}"]["check_ids"] = [c["id"] for c in subset]
    report["decision"] = "PARTIAL ADOPT" if not report["failed_checks"] else "G0 OPEN: investigate failed checks"
    save()
    print(json.dumps({"report": str(report_path.resolve()), "failed_checks": report["failed_checks"], "decision": report["decision"]}))
    return 1 if report["failed_checks"] else 0


if __name__ == "__main__":
    sys.exit(main())

