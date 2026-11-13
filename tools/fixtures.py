from pathlib import Path

from app.contracts import tick_sample

ROOT = Path(__file__).resolve().parent.parent


def node(name, kind, inputs, config, channels=2):
    return {"id": name, "kind": kind, "inputs": inputs, "channels": channels, "config": config}


def tone(name, frequency, amplitude, onset=0):
    return node(name, "tone", [], {"frequency_hz": frequency, "amplitude": amplitude, "onset_frame": onset})


def graph(nodes, seconds=16):
    return {"schema": "adaw.g0.graph@1", "sample_rate": 48000, "block_size": 256,
            "frames": round(seconds * 48000), "nodes": nodes, "output": nodes[-1]["id"]}


def faust_fixture(drive=None, trim=0.5, multitrack=True):
    nodes = [tone("tone-a", 220, 0.2)]
    source = "tone-a"
    if drive is not None:
        source = "saturation"
        nodes.append(node(source, "faust", ["tone-a"], {
            "source": (ROOT / "fixtures/saturation.dsp").read_text(),
            "parameters": {"/ADAW_Saturation/drive": drive, "/ADAW_Saturation/trim": trim}}))
    if multitrack:
        nodes.append(tone("tone-b", 997, 0.05))
        nodes.append(node("bus", "faust", [source, "tone-b"], {"source": "process = si.bus(4) :> si.bus(2);", "parameters": {}}))
        source = "bus"
    nodes.append(node("master", "faust", [source], {"source": "process = _ * 0.5, _ * 0.5;", "parameters": {}}))
    return graph(nodes)


def vst_node(name, registry_id, inputs=(), parameters=None, midi=None, state=None, automation=None):
    return node(name, "vst", list(inputs), {"registry_id": registry_id, "parameters": parameters or {},
        "midi": midi or [], "automation": automation or {}, "state_sha256": state})


def notes():
    # Explicit temporary performance; exact tick conversion tested separately.
    return [{"note": pitch, "velocity": 90, "start_frame": tick_sample(i * 960, 120, 960, 48000),
             "duration_frames": tick_sample(720, 120, 960, 48000)} for i, pitch in enumerate([60, 64, 67, 72])]

