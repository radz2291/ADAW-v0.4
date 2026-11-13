"""Independently verify reported hashes against local WAV bytes and graph inputs."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np
import soundfile as sf

from app.contracts import RenderGraph, digest, file_hash


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("report")
    args = parser.parse_args()
    path = Path(args.report)
    report = json.loads(path.read_text())
    verified = []
    for name, render in report["renders"].items():
        audio_path = Path(render["audio_path"])
        actual = file_hash(audio_path)
        assert actual == render["data"]["audio_sha256"] == render["quality"]["audio_sha256"], name
        audio, rate = sf.read(audio_path, dtype="float32", always_2d=True)
        assert digest(audio.astype("<f4").tobytes()) == render["data"]["pcm_sha256"], name
        graph_path = path.parent / "graphs" / path.stem / (name + ".json")
        graph = RenderGraph.parse(json.loads(graph_path.read_text()))
        assert graph.sha256 == render["source_sha256"], name
        assert len(audio) == graph.value["frames"] and rate == graph.value["sample_rate"], name
        assert np.isfinite(audio).all(), name
        for node_id, node in render["data"]["nodes"].items():
            if "state_sha256" in node:
                assert file_hash(audio_path.parent / (node_id + ".state")) == node["state_sha256"], name
        verified.append({"name": name, "audio_sha256": actual, "frames": len(audio), "source_sha256": graph.sha256})
    result = {"status": "PASS", "verified_renders": verified, "report_sha256": file_hash(path),
              "note": "Verifies file/PCM/source/state identities, not human listening or all behavioral assertions."}
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

