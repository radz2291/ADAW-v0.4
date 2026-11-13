"""Narrow G0 graph contract. All numbers are explicit fixture inputs.

The graph is deliberately distinct from the future full arrangement schema.
Unknown fields fail; native processors only exist in the worker.
"""
from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
import math
import re

from app.errors import AdawError


def canonical(value):
    # Python 3.12 JSON serialization, not cross-language RFC8785/JCS.
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def file_hash(path):
    with open(path, "rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def catalog_hash(catalog):
    """Bind interface metadata, not mutable current-value/display text."""
    keys = ("index", "name", "numSteps", "isBoolean", "isDiscrete", "label", "category",
            "isMetaParameter", "isAutomatable", "min", "max", "valueStrings")
    return digest(canonical([{k: p.get(k) for k in keys} for p in catalog]))


def require(condition, message):
    if not condition:
        raise AdawError("VALIDATION_ERROR", message)


def fields(value, required, optional=()):
    require(isinstance(value, dict), "Expected an object")
    require(set(required) <= value.keys(), f"Missing fields: {set(required) - value.keys()}")
    require(value.keys() <= set(required) | set(optional), f"Unknown fields: {value.keys() - set(required) - set(optional)}")


def number(value, low=None, high=None):
    require(type(value) in (int, float) and math.isfinite(value), "Expected finite number")
    require(low is None or value >= low, f"Number below {low}")
    require(high is None or value <= high, f"Number above {high}")


def tick_sample(tick, bpm, ppq, sample_rate):
    """Nearest sample, ties to even; exact rational origin, no accumulated drift."""
    require(type(tick) is int and tick >= 0, "Invalid tick")
    number(bpm, 0.000001)
    require(type(ppq) is int and ppq > 0, "Invalid PPQ")
    require(type(sample_rate) is int and sample_rate > 0, "Invalid rate")
    return round(Fraction(tick * 60 * sample_rate, ppq) / Fraction(str(bpm)))


@dataclass(frozen=True)
class RenderGraph:
    source: bytes

    @property
    def value(self):
        return json.loads(self.source)

    @property
    def sha256(self):
        return digest(self.source)

    @classmethod
    def parse(cls, value):
        fields(value, ("schema", "sample_rate", "block_size", "frames", "nodes", "output"))
        require(value["schema"] == "adaw.g0.graph@1", "Unsupported graph schema")
        for key in ("sample_rate", "block_size", "frames"):
            require(type(value[key]) is int and value[key] > 0, f"Invalid {key}")
        require(isinstance(value["nodes"], list) and value["nodes"], "Graph is empty")
        seen = {}
        for node in value["nodes"]:
            fields(node, ("id", "kind", "inputs", "channels", "config"))
            require(isinstance(node["id"], str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", node["id"]), "Invalid node ID")
            require(node["id"] not in seen, "Duplicate node ID")
            require(type(node["channels"]) is int and node["channels"] > 0, "Invalid channels")
            require(isinstance(node["inputs"], list) and all(isinstance(i, str) and i in seen for i in node["inputs"]), "Inputs must precede node; cycles/unknown inputs rejected")
            c = node["config"]
            if node["kind"] == "tone":
                fields(c, ("frequency_hz", "amplitude", "onset_frame"))
                require(not node["inputs"], "Tone cannot have inputs")
                number(c["frequency_hz"], 0, value["sample_rate"] / 2)
                number(c["amplitude"], 0, 1)
                require(type(c["onset_frame"]) is int and 0 <= c["onset_frame"] < value["frames"], "Invalid onset")
            elif node["kind"] == "faust":
                fields(c, ("source", "parameters"))
                require(isinstance(c["source"], str) and c["source"], "Empty Faust")
                require(isinstance(c["parameters"], dict), "Invalid parameters")
                for key, val in c["parameters"].items():
                    require(isinstance(key, str), "Parameter binding must be a string")
                    number(val)
            elif node["kind"] == "vst":
                fields(c, ("registry_id", "parameters", "midi", "automation", "state_sha256"))
                require(isinstance(c["registry_id"], str), "Invalid registry ID")
                require(c["state_sha256"] is None or isinstance(c["state_sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", c["state_sha256"]), "Invalid state hash")
                require(isinstance(c["parameters"], dict), "Invalid parameters")
                for key, val in c["parameters"].items():
                    require(isinstance(key, str) and key.isdigit(), "VST parameter index must be numeric")
                    number(val, 0, 1)
                require(isinstance(c["midi"], list), "Invalid MIDI")
                for note in c["midi"]:
                    fields(note, ("note", "velocity", "start_frame", "duration_frames"))
                    require(all(type(v) is int for v in note.values()), "MIDI fields must be integers")
                    require(0 <= note["note"] <= 127 and 1 <= note["velocity"] <= 127, "Invalid MIDI note/velocity")
                    require(note["start_frame"] >= 0 and note["duration_frames"] > 0 and note["start_frame"] + note["duration_frames"] <= value["frames"], "MIDI outside render range")
                require(isinstance(c["automation"], dict), "Invalid automation")
                for key, points in c["automation"].items():
                    require(isinstance(key, str) and key.isdigit() and isinstance(points, list) and points, "Invalid automation binding")
                    last = -1
                    for point in points:
                        require(isinstance(point, list) and len(point) == 2, "Expected frame/value pair")
                        frame, val = point
                        require(type(frame) is int and last < frame < value["frames"], "Automation frames must increase")
                        number(val, 0, 1)
                        last = frame
                    require(points[0][0] == 0, "G0 hold automation must start at frame zero")
            else:
                raise AdawError("ROUTING_UNSUPPORTED", f"Unknown node kind: {node['kind']}")
            seen[node["id"]] = node
        require(value["output"] == value["nodes"][-1]["id"], "Output must be last node")
        reachable = set()
        def walk(name):
            if name not in reachable:
                reachable.add(name)
                for parent in seen[name]["inputs"]:
                    walk(parent)
        walk(value["output"])
        require(reachable == seen.keys(), "Every node must reach output")
        return cls(canonical(value))

