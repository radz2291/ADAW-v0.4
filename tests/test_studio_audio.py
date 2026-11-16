"""Monitor assets are real, revision-bound native taps, never synthesized UI data."""

from copy import deepcopy
import io
import time

import numpy as np
import pytest
import soundfile as sf

from app.errors import AdawError
from app.project import ProjectService
from app.studio_audio import monitor_manifest, monitor_stem_sha
from tools.compose_glass_current_song import LEAD


def fixture_service(tmp_path):
    module_path = tmp_path / "lead.dsp"
    module_path.write_text(LEAD, encoding="utf-8")
    service = ProjectService(tmp_path / "project")
    module = service.import_file(module_path, "faust", "Original two-bar monitoring test", 30)["sha256"]
    source = dict(schema="adaw.arrangement@1", title="Monitor fixture", brief="Test only",
                  tempo=120, ppq=960, sample_rate=48000, block_size=256,
                  length_ticks=7680, tail_frames=2400, fade_frames=240,
                  sections=[dict(id="test", start_tick=0, end_tick=7680, mood="test", swing=.5)],
                  tracks=[dict(id="lead", role="lead", kind="faust_synth", bus="music",
                               gain_db=-12, pan=1, mute=True, solo=False, protected=False,
                               inserts=[], instrument=dict(module_sha256=module, parameters={}, voices=4,
                                                            release_seconds=.1),
                               events=[dict(id="note", note=60, velocity=110, start_tick=0, duration_ticks=7400)])],
                  buses=[dict(id="music", gain_db=0, inserts=[])], master=dict(gain_db=0, inserts=[]),
                  profile=dict(id="monitor-test", status="temporary_engineering_profile", purpose="test only",
                               sample_rate=48000, channels=2, subtype="PCM_24", min_lufs=-40,
                               max_lufs=-10, max_sample_peak_dbfs=-1, max_estimated_true_peak_dbfs=-1,
                               true_peak_margin_db=.25, max_dc=.001, dither_seed=1))
    service.create(source)
    return service


def test_native_monitor_tap_survives_mute_and_pan_and_is_revision_bound(tmp_path):
    service = fixture_service(tmp_path)
    timings = []
    for _ in range(3):
        started = time.monotonic()
        report = service.render_project(60)
        timings.append(time.monotonic() - started)
    print("Two-bar real Faust warm native render timings:", timings)
    manifest = monitor_manifest(service, report["id"])
    assert manifest["available"]
    assert manifest["revision"] == report["revision"]
    assert manifest["source_sha256"] == report["manifest"]["source_sha256"]
    assert "bus/master inserts" in manifest["limitations"]
    assert "pre-gain-pan-mute-solo" in manifest["tap"]
    tap_hash = monitor_stem_sha(service, report["id"], "lead")
    assert tap_hash == manifest["tracks"][0]["sha256"]
    tap, rate = sf.read(io.BytesIO(service.read_content(tap_hash)), always_2d=True)
    rendered, _ = sf.read(io.BytesIO(service.read_content(manifest["audio_sha256"])), always_2d=True)
    assert rate == manifest["sample_rate"]
    assert tap.shape == (manifest["frames"], 2)
    assert np.max(np.abs(tap[:, 0])) > .01 and np.max(np.abs(tap[:, 1])) > .01
    assert np.max(np.abs(rendered)) == 0
    with pytest.raises(AdawError, match="not part"):
        monitor_stem_sha(service, report["id"], "../other")
    with pytest.raises(AdawError):
        monitor_stem_sha(service, "rendition-unknown", "lead")


def test_historical_rendition_requests_regeneration_without_fabricating_stems(tmp_path):
    service = fixture_service(tmp_path)
    report = service.render_project(60)
    old = deepcopy(report)
    del old["render"]["data"]["stems"]["track_lead_monitor"]
    class HistoricalReader:
        def rendition(self, _):
            return old
    assert monitor_manifest(HistoricalReader(), old["id"])["available"] is False
    with pytest.raises(AdawError) as caught:
        monitor_stem_sha(HistoricalReader(), old["id"], "lead")
    assert caught.value.code == "MONITOR_UNAVAILABLE"
