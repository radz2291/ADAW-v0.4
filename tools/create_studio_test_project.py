"""Create an isolated real Faust project for desktop browser verification."""
import argparse
from copy import deepcopy
from pathlib import Path
from app.project import ProjectService
from tools.compose_glass_current_song import LEAD


def create(folder):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=False)
    module_path = folder / "lead.dsp"
    module_path.write_text(LEAD, encoding="utf-8")
    service = ProjectService(folder / "project")
    module = service.import_file(module_path, "faust", "Original test instrument", 30)["sha256"]
    track = dict(id="tone", role="lead", kind="faust_synth", bus="music", gain_db=-12,
                 pan=0, protected=False, inserts=[],
                 instrument=dict(module_sha256=module, parameters={}, voices=8, release_seconds=.28),
                 events=[dict(id=f"n{i}", note=60+i, velocity=90, start_tick=i*960,
                              duration_ticks=480) for i in range(8)])
    protected = deepcopy(track)
    protected.update(id="protected", protected=True)
    protected["events"] = [{**event, "id": "p" + event["id"]} for event in track["events"]]
    source = dict(schema="adaw.arrangement@2", title="Desktop UI fixture",
                  brief="Disposable desktop interaction test", tempo=120, ppq=960,
                  sample_rate=48000, block_size=256, length_ticks=10560,
                  tail_frames=24000, fade_frames=240,
                  time_map=[dict(tick=t, bpm=b, numerator=n, denominator=4)
                            for t, b, n in [(0, 120, 4), (3840, 104, 4), (7680, 104, 3)]],
                  sections=[dict(id=n, start_tick=a, end_tick=b, mood="test", swing=.5)
                            for n, a, b in [("intro", 0, 3840), ("bridge", 3840, 7680), ("turn", 7680, 10560)]],
                  tracks=[track, protected], buses=[dict(id="music", gain_db=0, inserts=[])],
                  master=dict(gain_db=0, inserts=[]),
                  profile=dict(id="ui-test", status="temporary_engineering_profile", purpose="test only",
                               sample_rate=48000, channels=2, subtype="PCM_24", min_lufs=-40,
                               max_lufs=-10, max_sample_peak_dbfs=-1, max_estimated_true_peak_dbfs=-1,
                               true_peak_margin_db=.25, max_dc=.001, dither_seed=1))
    service.create(source)
    rendition = service.render_project(60)
    return {"root": str(service.root), "rendition": rendition["id"], "revision": rendition["revision"]}


if __name__ == "__main__":
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder")
    print(json.dumps(create(parser.parse_args().folder)))
