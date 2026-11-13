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
    decoded = other.astype(np.float64)
    if info.subtype in ("PCM_16", "PCM_24", "PCM_32"):
        # SciPy left-justifies 24-bit samples in int32; normalize its container.
        decoded /= 2 ** (np.iinfo(other.dtype).bits - 1)
    elif info.subtype != "FLOAT":
        raise AdawError("INVALID_EXPORT", "Unsupported WAV subtype")
    if other_rate != rate or not np.array_equal(audio, decoded):
        raise AdawError("INVALID_EXPORT", "Independent WAV decode mismatch")
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


def estimated_true_peak(audio, factor=8):
    """Explicit engineering estimator, NOT claimed full BS.1770 conformance.

    128-tap-per-phase Kaiser(12) windowed sinc, zero extension. Calibrated against
    analytic intersample sine peaks in tests and G1 evidence. Profile adds margin.
    """
    from scipy.signal import firwin, resample_poly
    kernel = firwin(128 * factor + 1, 1/factor, window=("kaiser", 12.0))
    return max(float(np.max(np.abs(resample_poly(audio[:, ch], factor, 1, window=kernel)))) for ch in range(audio.shape[1]))


def analyze_delivery(path, profile, expected_frames, require_pcm=True):
    from app.arrangement import validate_profile
    from app.contracts import canonical, digest
    validate_profile(profile)
    quality = analyze(path)
    audio, rate = sf.read(path, always_2d=True, dtype="float64")
    tp = estimated_true_peak(audio)
    tp_db = 20 * math.log10(tp) if tp else None
    mono = np.mean(audio, axis=1)
    mono_rms = float(np.sqrt(np.mean(mono*mono)))
    stereo_rms = quality["rms"]
    quality["true_peak"] = {"status": "MEASURED_ESTIMATE", "linear": tp, "dbfs": tp_db,
        "method": "8x polyphase FIR, 128 taps/phase, Kaiser beta=12, scipy.signal.resample_poly",
        "calibration": "analytic phase-shifted sines; not full EBU/ITU conformance",
        "profile_margin_db": profile["true_peak_margin_db"]}
    quality["engineering"] = {"crest_db": 20*math.log10(quality["sample_peak"]/stereo_rms) if stereo_rms else None,
        "mono_fold_rms_ratio": mono_rms/stereo_rms if stereo_rms else None,
        "stereo_correlation": float(np.corrcoef(audio.T)[0, 1]) if np.all(np.std(audio, axis=0) > 0) else None,
        "last_10ms_peak": float(np.max(np.abs(audio[-max(1,round(rate*.01)):])))}
    rules = {
        "frames": quality["frames"] == expected_frames,
        "sample_rate": rate == profile["sample_rate"],
        "channels": quality["channels"] == profile["channels"],
        "subtype": quality["subtype"] == (profile["subtype"] if require_pcm else "FLOAT"),
        "loudness": quality["integrated_lufs"] is not None and profile["min_lufs"] <= quality["integrated_lufs"] <= profile["max_lufs"],
        "sample_peak": quality["sample_peak_dbfs"] is not None and quality["sample_peak_dbfs"] <= profile["max_sample_peak_dbfs"],
        "estimated_true_peak_with_margin": tp_db is not None and tp_db + profile["true_peak_margin_db"] <= profile["max_estimated_true_peak_dbfs"],
        "dc": max(abs(v) for v in quality["dc_per_channel"]) <= profile["max_dc"],
    }
    quality.update(status="PASS" if all(rules.values()) else "FAIL", rules={k: "PASS" if v else "FAIL" for k,v in rules.items()},
                   profile=profile, profile_sha256=digest(canonical(profile)),
                   delivery_profile_status="temporary engineering profile" if profile["status"].startswith("temporary") else "owner selected")
    return quality

