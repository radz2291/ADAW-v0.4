"""Independent decoded-file checks. No artistic or delivery PASS inferred."""
import importlib.metadata
import math
import numpy as np
import pyloudnorm as pyln
import soundfile as sf
from scipy.io import wavfile

from app.contracts import file_hash
from app.errors import AdawError


def analyze(path):
    audio, rate = sf.read(path, always_2d=True, dtype="float64")
    info = sf.info(path)
    if not len(audio) or not np.isfinite(audio).all():
        raise AdawError("QUALITY_BLOCKED", "Empty or nonfinite audio")
    other_rate, other = wavfile.read(path)
    if other.ndim == 1:
        other = other[:, None]
    # G0 publishes float WAV only; do not apply this comparison to integer PCM.
    if info.subtype != "FLOAT" or other_rate != rate or not np.array_equal(audio, other.astype(np.float64)):
        raise AdawError("INVALID_EXPORT", "Independent FLOAT WAV decode mismatch")
    peak = float(np.max(np.abs(audio)))
    loudness = pyln.Meter(rate).integrated_loudness(audio) if len(audio) >= round(0.4 * rate) and audio.shape[1] <= 5 else None
    return {"audio_sha256": file_hash(path), "frames": len(audio), "sample_rate": rate,
            "channels": audio.shape[1], "subtype": info.subtype, "duration_seconds": len(audio) / rate,
            "sample_peak": peak, "sample_peak_dbfs": 20 * math.log10(peak) if peak else None,
            "rms": float(np.sqrt(np.mean(audio * audio))), "dc_per_channel": np.mean(audio, axis=0).tolist(),
            "integrated_lufs": float(loudness) if loudness is not None and math.isfinite(loudness) else None,
            "loudness_method": "pyloudnorm ITU-R BS.1770-4 K-weighting and gating; 400 ms blocks",
            "analyzer_versions": {n: importlib.metadata.version(n) for n in ("pyloudnorm", "soundfile", "scipy", "numpy")},
            "independent_decode": "PASS: libsndfile and scipy.io.wavfile agree",
            "true_peak": {"status": "NOT_EVALUATED", "reason": "No calibrated true-peak meter in G0 subset"},
            "delivery_profile_status": "UNKNOWN: no owner-selected thresholds",
            "listening": "NOT_EVALUATED"}

