"""Versioned G1 source contract and deterministic musical-time graph compiler.

Fixed tempo/4:4 only. No implicit tempo, assets, processing or delivery targets.
The original v0.4 draft schema remains untouched; see ADR-0002.
"""
import re
from app.contracts import canonical, digest, fields, number, require, tick_sample, RenderGraph


def identifier(value):
    require(isinstance(value, str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", value), "Invalid stable ID")


def sha(value):
    require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value), "Invalid content hash")


def integer(value, minimum=0):
    require(type(value) is int and value >= minimum, "Invalid integer")


def validate_profile(p):
    fields(p, ("id", "status", "purpose", "sample_rate", "channels", "subtype", "min_lufs", "max_lufs",
               "max_sample_peak_dbfs", "max_estimated_true_peak_dbfs", "true_peak_margin_db", "max_dc", "dither_seed"))
    identifier(p["id"])
    require(p["status"] in ("temporary_engineering_profile", "owner_selected"), "Invalid profile status")
    require(isinstance(p["purpose"], str) and p["purpose"], "Missing profile purpose")
    integer(p["sample_rate"], 1)
    require(p["channels"] == 2 and p["subtype"] == "PCM_24", "G1 exports stereo PCM24")
    for key in ("min_lufs", "max_lufs", "max_sample_peak_dbfs", "max_estimated_true_peak_dbfs"):
        number(p[key])
    number(p["true_peak_margin_db"], 0)
    number(p["max_dc"], 0)
    integer(p["dither_seed"])
    require(p["min_lufs"] < p["max_lufs"], "Inverted loudness range")
    require(p["max_sample_peak_dbfs"] <= 0 and p["max_estimated_true_peak_dbfs"] <= 0, "Export peaks cannot exceed full scale")
    return p


def validate(source):
    fields(source, ("schema", "title", "brief", "tempo", "ppq", "sample_rate", "block_size", "length_ticks",
                    "tail_frames", "fade_frames", "sections", "tracks", "buses", "master", "profile"))
    require(source["schema"] == "adaw.arrangement@1", "Unsupported arrangement")
    require(isinstance(source["title"], str) and source["title"], "Missing title")
    require(isinstance(source["brief"], str) and source["brief"], "Missing brief")
    number(source["tempo"], 1)
    for key in ("ppq", "sample_rate", "block_size", "length_ticks", "fade_frames"):
        integer(source[key], 1)
    integer(source["tail_frames"])
    validate_profile(source["profile"])
    require(source["profile"]["sample_rate"] == source["sample_rate"], "Profile sample rate mismatch; resampling not implicit")
    frames = tick_sample(source["length_ticks"], source["tempo"], source["ppq"], source["sample_rate"]) + source["tail_frames"]
    require(source["fade_frames"] < frames // 2, "Fade too long")
    require(isinstance(source["sections"], list) and source["sections"], "Missing sections")
    end, ids = 0, set()
    for section in source["sections"]:
        fields(section, ("id", "start_tick", "end_tick", "mood", "swing"))
        identifier(section["id"])
        require(section["id"] not in ids, "Duplicate section")
        ids.add(section["id"])
        integer(section["start_tick"])
        integer(section["end_tick"], 1)
        require(section["start_tick"] == end and section["end_tick"] > end, "Sections must partition timeline")
        require(isinstance(section["mood"], str), "Invalid mood")
        number(section["swing"], .5, .75)
        end = section["end_tick"]
    require(end == source["length_ticks"], "Section end mismatch")
    require(isinstance(source["buses"], list) and source["buses"], "Missing buses")
    bus_ids = set()
    for bus in source["buses"]:
        fields(bus, ("id", "gain_db", "inserts"))
        identifier(bus["id"])
        require(bus["id"] not in bus_ids, "Duplicate bus")
        bus_ids.add(bus["id"])
        number(bus["gain_db"])
        validate_inserts(bus["inserts"])
    require(isinstance(source["tracks"], list) and source["tracks"], "Missing tracks")
    track_ids, event_ids = set(), set()
    for t in source["tracks"]:
        fields(t, ("id", "role", "kind", "bus", "gain_db", "pan", "protected", "instrument", "events", "inserts"))
        identifier(t["id"])
        require(t["id"] not in track_ids and t["id"] not in bus_ids, "Duplicate track/bus ID")
        track_ids.add(t["id"])
        require(t["bus"] in bus_ids and isinstance(t["role"], str), "Invalid track routing/role")
        require(type(t["protected"]) is bool, "Invalid protection flag")
        number(t["gain_db"])
        number(t["pan"], -1, 1)
        validate_inserts(t["inserts"])
        inst = t["instrument"]
        if t["kind"] == "samples":
            fields(inst, ("asset_sha256", "fade_frames"))
            sha(inst["asset_sha256"])
            integer(inst["fade_frames"])
        elif t["kind"] == "faust_synth":
            fields(inst, ("module_sha256", "parameters", "voices", "release_seconds"))
            sha(inst["module_sha256"])
            integer(inst["voices"], 1)
            number(inst["release_seconds"], 0)
            validate_parameters(inst["parameters"])
        elif t["kind"] == "vst":
            fields(inst, ("registry_id", "catalog_sha256", "state_sha256", "parameters"))
            require(isinstance(inst["registry_id"], str), "Invalid plugin reference")
            sha(inst["catalog_sha256"])
            sha(inst["state_sha256"])
            validate_parameters(inst["parameters"])
            for key, value in inst["parameters"].items():
                require(key.isdigit(), "Numeric plugin parameter required")
                number(value, 0, 1)
        else:
            require(False, "Unsupported instrument")
        require(isinstance(t["events"], list), "Invalid events")
        for e in t["events"]:
            fields(e, ("id", "start_tick", "duration_ticks", "note", "velocity"))
            identifier(e["id"])
            require(e["id"] not in event_ids, "Duplicate event ID")
            event_ids.add(e["id"])
            integer(e["start_tick"])
            integer(e["duration_ticks"], 1)
            integer(e["note"])
            integer(e["velocity"], 1)
            require(e["note"] <= 127 and e["velocity"] <= 127, "Invalid MIDI range")
            require(e["start_tick"] + e["duration_ticks"] <= source["length_ticks"], "Event outside arrangement")
    require(bus_ids == {t["bus"] for t in source["tracks"]}, "Empty buses unsupported")
    fields(source["master"], ("gain_db", "inserts"))
    number(source["master"]["gain_db"])
    validate_inserts(source["master"]["inserts"])
    canonical(source)
    return source


def validate_parameters(parameters):
    require(isinstance(parameters, dict), "Invalid parameters")
    for key, value in parameters.items():
        require(isinstance(key, str) and key, "Invalid binding")
        number(value)


def validate_inserts(inserts):
    require(isinstance(inserts, list), "Invalid ordered inserts")
    for insert in inserts:
        if "registry_id" in insert:
            fields(insert, ("registry_id", "catalog_sha256", "state_sha256", "parameters"))
            require(isinstance(insert["registry_id"], str), "Invalid plugin reference")
            sha(insert["catalog_sha256"])
            sha(insert["state_sha256"])
            for key, value in insert["parameters"].items():
                require(isinstance(key, str) and key.isdigit(), "Invalid plugin binding")
                number(value, 0, 1)
        else:
            fields(insert, ("module_sha256", "parameters"))
            sha(insert["module_sha256"])
        validate_parameters(insert["parameters"])


def compile_graph(source, read_content):
    validate(source)
    frame = lambda tick: tick_sample(tick, source["tempo"], source["ppq"], source["sample_rate"])
    total = frame(source["length_ticks"]) + source["tail_frames"]
    nodes, ends, stems = [], {}, []
    def add(name, kind, inputs, config):
        nodes.append(dict(id=name, kind=kind, inputs=inputs, channels=2, config=config))
        return name
    def processing(name, upstream, gain_db, pan, inserts):
        last = upstream
        for i, insert in enumerate(inserts):
            if "registry_id" in insert:
                last = add(f"{name}_fx{i}", "vst", [last], {"registry_id": insert["registry_id"], "state_sha256": insert["state_sha256"],
                    "parameters": insert["parameters"], "midi": [], "automation": {}})
            else:
                last = add(f"{name}_fx{i}", "faust", [last], {"source": read_content(insert["module_sha256"]).decode("utf-8"), "parameters": insert["parameters"]})
        gain = 10 ** (gain_db / 20)
        return add(name + "_level", "faust", [last], {"source": f"process = *( {gain*min(1,1-pan):.17g} ), *( {gain*min(1,1+pan):.17g} );", "parameters": {}})
    for t in source["tracks"]:
        inst = t["instrument"]
        midi = [{"note": e["note"], "velocity": e["velocity"], "start_frame": frame(e["start_tick"]),
                 "duration_frames": frame(e["start_tick"]+e["duration_ticks"]) - frame(e["start_tick"])} for e in t["events"]]
        if t["kind"] == "samples":
            config = {"events": [{"asset_sha256": inst["asset_sha256"], "start_frame": e["start_frame"],
                "duration_frames": e["duration_frames"], "gain": e["velocity"]/127, "pan": 0,
                "fade_frames": inst["fade_frames"]} for e in midi]}
        elif t["kind"] == "faust_synth":
            config = {"source": read_content(inst["module_sha256"]).decode("utf-8"), "parameters": inst["parameters"],
                "voices": inst["voices"], "release_seconds": inst["release_seconds"], "midi": midi}
        else:
            config = {"registry_id": inst["registry_id"], "state_sha256": inst["state_sha256"],
                      "parameters": inst["parameters"], "midi": midi, "automation": {}}
        dry = add("track_"+t["id"], t["kind"], [], config)
        ends[t["id"]] = processing("track_"+t["id"], dry, t["gain_db"], t["pan"], t["inserts"])
        stems.append(ends[t["id"]])
    buses = []
    for b in source["buses"]:
        inputs = [ends[t["id"]] for t in source["tracks"] if t["bus"] == b["id"]]
        summed = add("bus_"+b["id"], "faust", inputs, {"source": f"process = si.bus({2*len(inputs)}) :> si.bus(2);", "parameters": {}})
        buses.append(processing("bus_"+b["id"], summed, b["gain_db"], 0, b["inserts"]))
    summed = add("mix", "faust", buses, {"source": f"process = si.bus({2*len(buses)}) :> si.bus(2);", "parameters": {}})
    master = processing("master", summed, source["master"]["gain_db"], 0, source["master"]["inserts"])
    fade = source["fade_frames"]
    add("output", "faust", [master], {"source": f"envelope = min(1,ba.time/{fade}.0)*max(0,min(1,({total-1}.0-ba.time)/{fade}.0)); process = *(envelope),*(envelope);", "parameters": {}})
    graph = {"schema": "adaw.graph@2", "sample_rate": source["sample_rate"], "block_size": source["block_size"], "frames": total, "nodes": nodes, "output": "output"}
    return RenderGraph.parse(graph).value, stems
