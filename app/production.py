"""Reusable, explicitly scoped offline production workflows."""

import math
from pathlib import Path

from app.contracts import file_hash, number, require
from app.quality import analyze


def matched_comparison(project, rendition_ids, target_lufs, destination):
    """Produce gain-only matched review WAVs and measure the delivered bytes."""
    import numpy as np
    import soundfile as sf

    number(target_lufs)
    require(len(rendition_ids) >= 2 and len(set(rendition_ids)) == len(rendition_ids),
            "Choose at least two distinct renditions")
    destination = Path(destination).resolve()
    require(not destination.is_relative_to(project.root), "Comparison output belongs outside project storage")
    prepared = []
    for ident in rendition_ids:
        rendition = project.rendition(ident)
        sha = rendition["render"]["data"]["audio_sha256"]
        project.read_content(sha)
        path = project.content / sha
        measured = analyze(path)
        require(measured["integrated_lufs"] is not None, "Cannot match unmeasurable loudness")
        gain_db = target_lufs - measured["integrated_lufs"]
        require(abs(gain_db) <= 60, "Requested gain exceeds comparison guardrail")
        gain = math.pow(10, gain_db / 20)
        require(measured["sample_peak"] * gain < 1, "Select a lower comparison target to preserve headroom")
        prepared.append((rendition, path, gain, gain_db))
    destination.mkdir(parents=True, exist_ok=False)
    items = []
    for index, (rendition, path, gain, gain_db) in enumerate(prepared, 1):
        audio, rate = sf.read(path, always_2d=True, dtype="float64")
        output = destination / f"candidate-{index}.wav"
        sf.write(output, np.asarray(audio * gain, dtype=np.float32), rate, subtype="FLOAT")
        items.append({"rendition": rendition["id"], "revision": rendition["revision"], "gain_db": gain_db,
                      "path": str(output), "sha256": file_hash(output), "quality": analyze(output)})
    return {"schema": "adaw.comparison@1", "target_lufs": target_lufs,
            "method": "BS.1770-4 integrated loudness, gain-only float WAV review",
            "listening": "AWAITING_OWNER_REVIEW", "items": items}
