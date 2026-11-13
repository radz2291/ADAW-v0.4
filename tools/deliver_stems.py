"""Copy verified track-tap stems and report their shared render frame grid."""

import argparse
import json
from pathlib import Path
import tempfile

import soundfile as sf

from app.arrangement import identifier
from app.contracts import canonical, require
from app.project import ProjectService


def deliver_stems(project, rendition_id, destination):
    report = project.rendition(rendition_id)
    stems = report["render"]["data"]["stems"]
    require(bool(stems), "No captured track stems")
    graph = report["graph"]
    destination = Path(destination).resolve()
    require(not destination.exists() and not destination.is_relative_to(project.root),
            "Choose a fresh stem directory outside the project")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as directory:
        stage = Path(directory) / "stems"
        stage.mkdir()
        files = {}
        for tap, stem in stems.items():
            identifier(tap)
            path = stage / f"{tap}.wav"
            path.write_bytes(project.read_content(stem["sha256"]))
            info = sf.info(path)
            require((info.frames, info.samplerate, info.channels, info.subtype) ==
                    (graph["frames"], graph["sample_rate"], 2, "FLOAT"),
                    "Stem format differs from render frame grid")
            files[path.name] = stem["sha256"]
        manifest = {"schema": "adaw.stem-delivery@1", "rendition": rendition_id,
                    "revision": report["revision"], "frames": graph["frames"],
                    "sample_rate": graph["sample_rate"], "channels": 2, "subtype": "FLOAT",
                    "tap": "after track inserts and gain, before bus and master", "files": files}
        (stage / "manifest.json").write_bytes(canonical(manifest))
        stage.rename(destination)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--rendition", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(json.dumps(deliver_stems(ProjectService(args.root), args.rendition, args.output)))


if __name__ == "__main__":
    main()
