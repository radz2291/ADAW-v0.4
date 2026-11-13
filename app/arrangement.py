"""Versioned G1 source contract and deterministic musical-time graph compiler.

Version 1 is fixed tempo and meter. Version 2 adds an explicit tempo/meter map.
The original v0.4 draft schema remains untouched; see ADR-0002.
"""
import re
from bisect import bisect_right
from fractions import Fraction
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


def timing(source):
    """Accumulate unrounded frame offsets and round each absolute event endpoint."""
    if source["schema"] == "adaw.arrangement@1":
        return lambda tick: tick_sample(tick, source["tempo"], source["ppq"], source["sample_rate"])
    changes = source["time_map"]
    require(isinstance(changes, list) and bool(changes), "Time map must start at tick zero")
    tick_positions, frames, slopes = [], [], []
    meter_origin = meter = None
    for index, change in enumerate(changes):
        fields(change, ("tick", "bpm", "numerator", "denominator"))
        tick = change["tick"]
        integer(tick)
        number(change["bpm"], 1)
        integer(change["numerator"], 1)
        integer(change["denominator"], 1)
        denominator = change["denominator"]
        require(denominator & (denominator - 1) == 0 and (source["ppq"] * 4) % denominator == 0,
                "Meter denominator must divide a whole note in ticks")
        require(tick < source["length_ticks"] and (tick > tick_positions[-1] if index else tick == 0),
                "Time map ticks must increase from zero within the project")
        next_meter = (change["numerator"], denominator)
        if not index:
            require(change["bpm"] == source["tempo"], "Initial tempo must match the first map entry")
        if meter != next_meter:
            if meter:
                bar_ticks = source["ppq"] * 4 * meter[0] // meter[1]
                require((tick - meter_origin) % bar_ticks == 0, "Meter changes must start on a bar boundary")
            meter_origin, meter = tick, next_meter
        frames.append(frames[-1] + (tick - tick_positions[-1]) * slopes[-1] if index else Fraction(0))
        tick_positions.append(tick)
        slopes.append(Fraction(60 * source["sample_rate"], source["ppq"]) / Fraction(str(change["bpm"])))

    def frame_at(tick):
        i = bisect_right(tick_positions, tick) - 1
        return round(frames[i] + (tick - tick_positions[i]) * slopes[i])

    return frame_at


def validate(source):
    fields(source, ("schema", "title", "brief", "tempo", "ppq", "sample_rate", "block_size", "length_ticks",
                    "tail_frames", "fade_frames", "sections", "tracks", "buses", "master", "profile"), ("time_map",))
    require(source["schema"] in ("adaw.arrangement@1", "adaw.arrangement@2"), "Unsupported arrangement")
    require(("time_map" in source) == (source["schema"] == "adaw.arrangement@2"), "Time map requires arrangement version 2")
    require(isinstance(source["title"], str) and source["title"], "Missing title")
    require(isinstance(source["brief"], str) and source["brief"], "Missing brief")
    number(source["tempo"], 1)
    for key in ("ppq", "sample_rate", "block_size", "length_ticks", "fade_frames"):
        integer(source[key], 1)
    integer(source["tail_frames"])
    validate_profile(source["profile"])
    require(source["profile"]["sample_rate"] == source["sample_rate"], "Profile sample rate mismatch; resampling not implicit")
    frames = timing(source)(source["length_ticks"]) + source["tail_frames"]
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
        fields(bus, ("id", "gain_db", "inserts"), ("send_from",) if source["schema"] == "adaw.arrangement@2" else ())
        identifier(bus["id"])
        require(bus["id"] not in bus_ids, "Duplicate bus")
        bus_ids.add(bus["id"])
        number(bus["gain_db"])
        validate_inserts(bus["inserts"])
    bus_positions = {bus["id"]: index for index, bus in enumerate(source["buses"])}
    for bus in source["buses"]:
        sends = bus.get("send_from", [])
        require(isinstance(sends, list), "Expected a bus send list")
        upstream = set()
        for send in sends:
            fields(send, ("bus", "gain_db"))
            identifier(send["bus"])
            require(send["bus"] in bus_positions and bus_positions[send["bus"]] < bus_positions[bus["id"]],
                    "Post-fader send must reference an earlier bus")
            require(send["bus"] not in upstream, "Duplicate bus send")
            upstream.add(send["bus"])
            number(send["gain_db"], -120, 0)
        for insert in bus["inserts"]:
            if "key_bus" in insert:
                key_bus = insert["key_bus"]
                require(source["schema"] == "adaw.arrangement@2"
                        and key_bus in bus_positions and bus_positions[key_bus] < bus_positions[bus["id"]],
                        "Faust sidechain must reference an earlier bus in arrangement v2")
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
        validate_inserts(t["inserts"], allow_key=False)
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
    require(bus_ids == ({t["bus"] for t in source["tracks"]} |
                        {bus["id"] for bus in source["buses"] if bus.get("send_from")}),
            "Each bus needs a track or a send")
    fields(source["master"], ("gain_db", "inserts"))
    number(source["master"]["gain_db"])
    validate_inserts(source["master"]["inserts"], allow_key=False)
    canonical(source)
    return source


def validate_parameters(parameters):
    require(isinstance(parameters, dict), "Invalid parameters")
    for key, value in parameters.items():
        require(isinstance(key, str) and key, "Invalid binding")
        number(value)


def validate_inserts(inserts, allow_key=True):
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
            fields(insert, ("module_sha256", "parameters"), ("automation", "key_bus") if allow_key else ("automation",))
            sha(insert["module_sha256"])
            if "key_bus" in insert:
                identifier(insert["key_bus"])
            lanes = insert.get("automation", {})
            require(isinstance(lanes, dict), "Invalid Faust automation")
            for binding, points in lanes.items():
                require(isinstance(binding, str) and binding and isinstance(points, list) and points,
                        "Invalid Faust automation lane")
                previous = -1
                for point in points:
                    fields(point, ("tick", "value"))
                    integer(point["tick"])
                    require(point["tick"] > previous, "Automation ticks must increase")
                    number(point["value"])
                    previous = point["tick"]
                require(points[0]["tick"] == 0, "Automation must start at tick zero")
        validate_parameters(insert["parameters"])


def compile_graph(source, read_content):
    validate(source)
    frame = timing(source)
    total = frame(source["length_ticks"]) + source["tail_frames"]
    nodes, ends, stems = [], {}, []
    def add(name, kind, inputs, config):
        nodes.append(dict(id=name, kind=kind, inputs=inputs, channels=2, config=config))
        return name
    def processing(name, upstream, gain_db, pan, inserts, available_keys=None):
        last = upstream
        for i, insert in enumerate(inserts):
            if "registry_id" in insert:
                last = add(f"{name}_fx{i}", "vst", [last], {"registry_id": insert["registry_id"], "state_sha256": insert["state_sha256"],
                    "parameters": insert["parameters"], "midi": [], "automation": {}})
            else:
                config = {"source": read_content(insert["module_sha256"]).decode("utf-8"), "parameters": insert["parameters"]}
                if insert.get("automation"):
                    require(all(point["tick"] < source["length_ticks"] for points in insert["automation"].values()
                                for point in points), "Automation point outside arrangement")
                    config["automation"] = {key: [[frame(point["tick"]), point["value"]] for point in points]
                                            for key, points in insert["automation"].items()}
                inputs = [last]
                if "key_bus" in insert:
                    inputs.append(available_keys[insert["key_bus"]])
                last = add(f"{name}_fx{i}", "faust", inputs, config)
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
    buses = {}
    for b in source["buses"]:
        inputs = [ends[t["id"]] for t in source["tracks"] if t["bus"] == b["id"]]
        for index, send in enumerate(b.get("send_from", [])):
            inputs.append(processing(f"bus_{b['id']}_send{index}", buses[send["bus"]], send["gain_db"], 0, []))
        summed = add("bus_"+b["id"], "faust", inputs, {"source": f"process = si.bus({2*len(inputs)}) :> si.bus(2);", "parameters": {}})
        buses[b["id"]] = processing("bus_"+b["id"], summed, b["gain_db"], 0, b["inserts"], buses)
    summed = add("mix", "faust", list(buses.values()), {"source": f"process = si.bus({2*len(buses)}) :> si.bus(2);", "parameters": {}})
    master = processing("master", summed, source["master"]["gain_db"], 0, source["master"]["inserts"])
    fade = source["fade_frames"]
    add("output", "faust", [master], {"source": f"envelope = min(1,ba.time/{fade}.0)*max(0,min(1,({total-1}.0-ba.time)/{fade}.0)); process = *(envelope),*(envelope);", "parameters": {}})
    graph = {"schema": "adaw.graph@2", "sample_rate": source["sample_rate"], "block_size": source["block_size"], "frames": total, "nodes": nodes, "output": "output"}
    return RenderGraph.parse(graph).value, stems
