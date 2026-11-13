"""Build a separate 64-second musical project for portability and timing checks."""

import argparse
from copy import deepcopy
import json

from app.project import ProjectService


def create_study(origin, destination):
    _, reference = origin.source()
    source = deepcopy(reference)
    source.update(schema="adaw.arrangement@2", title="Glass Current",
                  brief="Instrumental meter study with a 4/4 opening and a 3/4 ending.",
                  tempo=120, length_ticks=115200, tail_frames=48000)
    source["time_map"] = [
        {"tick": 0, "bpm": 120, "numerator": 4, "denominator": 4},
        {"tick": 61440, "bpm": 104, "numerator": 4, "denominator": 4},
        {"tick": 92160, "bpm": 104, "numerator": 3, "denominator": 4},
    ]
    source["sections"] = [
        {"id": name, "start_tick": start, "end_tick": end, "mood": mood, "swing": .5}
        for name, start, end, mood in [
            ("opening", 0, 15360, "Sparse and suspended"),
            ("current", 15360, 61440, "Steady four-beat pulse"),
            ("undertow", 61440, 92160, "Slower chord changes and lighter drums"),
            ("turn", 92160, 115200, "Three-beat refrain"),
        ]
    ]
    # Reuse known source assets and Faust modules through validated imports.
    source["tracks"] = [track for track in source["tracks"]
                        if track["id"] in {"kick", "hat", "bass808", "haze"}]
    for bus in source["buses"]:
        bus["inserts"] = [insert for insert in bus["inserts"] if "module_sha256" in insert]
    imported = set()
    def import_ref(sha, kind):
        if sha not in imported:
            origin.read_content(sha)
            destination.import_file(origin.content / sha, kind, "Reusable Night Circuit source asset", 30)
            imported.add(sha)

    for entity in [*source["tracks"], *source["buses"], source["master"]]:
        for insert in entity["inserts"]:
            import_ref(insert["module_sha256"], "faust")
    tracks = {track["id"]: track for track in source["tracks"]}
    for track in tracks.values():
        track["events"] = []
        instrument = track["instrument"]
        if track["kind"] == "samples":
            import_ref(instrument["asset_sha256"], "audio")
        else:
            import_ref(instrument["module_sha256"], "faust")
    tracks["kick"]["gain_db"] = -9
    tracks["haze"]["gain_db"] = -12

    def add(name, tick, duration, note, velocity):
        events = tracks[name]["events"]
        events.append(dict(id=f"{name}_{len(events)}", start_tick=tick, duration_ticks=duration,
                           note=note, velocity=velocity))

    chords = [(57, 60, 64, 71), (53, 57, 60, 64), (55, 59, 62, 69), (52, 56, 59, 65)]
    roots = (33, 29, 31, 28)
    tick = 0
    for bar in range(32):
        beats = 4 if bar < 24 else 3
        chord = (bar // 2) % len(chords)
        if bar % 2 == 0:
            for pitch in chords[chord]:
                add("haze", tick, beats * 1920 - 160, pitch, 72)
        if bar >= 4 and bar < 31:
            for pulse in ([0, 1920] if 4 <= bar < 16 else [0]):
                add("kick", tick + pulse, 450, 60, 95)
                add("bass808", tick + pulse + 144, 980, roots[chord], 93)
            for pulse in range(480, beats * 960, 960):
                add("hat", tick + pulse, 220, 60, 64 if bar < 16 else 49)
        tick += beats * 960
    return destination.create(source)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-project", required=True)
    parser.add_argument("--root", required=True)
    args = parser.parse_args()
    print(json.dumps(create_study(ProjectService(args.from_project), ProjectService(args.root))))


if __name__ == "__main__":
    main()
