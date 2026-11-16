"""Service and native-audio regressions for the frozen everyday interaction rubric."""
import copy

import numpy as np
import pytest
import soundfile as sf

from app.arrangement import compile_graph, validate
from app.errors import AdawError
from app.project import ProjectService
from test_project import project


def edit(service, name, *operations):
    return service.edit(dict(command_id=name, base_revision=service.source()[0],
                             reason=name, operations=list(operations)))


def event_op(kind, **kwargs):
    return dict(kind=kind, track_id="kick", **kwargs)


def test_direct_add_duplicate_move_delete_are_atomic_and_revisioned(project):
    service, original = project
    first = dict(id="new", start_tick=480, duration_ticks=120, note=65, velocity=81)
    edit(service, "draw", event_op("add_events", events=[first]))
    edit(service, "duplicate", event_op("duplicate_events", event_ids=["hit", "new"],
         new_ids={"hit": "copy_hit", "new": "copy_new"}, offset_ticks=960))
    edit(service, "move", event_op("transform_events", event_ids=["copy_hit", "copy_new"],
         action="move", offset_ticks=240))
    events = {e["id"]: e for e in service.source()[1]["tracks"][0]["events"]}
    assert events["copy_new"] == {**first, "id": "copy_new", "start_tick": 1680}
    assert events["copy_hit"]["start_tick"] == 1200
    before = service.project_inspect()
    with pytest.raises(AdawError):
        edit(service, "bad batch", event_op("delete_events", event_ids=["hit"]),
             event_op("add_events", events=[{**first, "id": "new", "note": 200}]))
    assert service.project_inspect() == before
    assert all(p["id"] != "bad batch" for p in service.history()["proposals"])
    edit(service, "delete", event_op("delete_events", event_ids=["copy_hit", "copy_new"]))
    before = service.source()[0]
    assert edit(service, "empty delete", event_op("delete_events", event_ids=[]))["revision"] == before
    assert service.source()[1]["tracks"][0]["events"] == [original["tracks"][0]["events"][0], first]


@pytest.mark.parametrize("operation", [
    event_op("add_events", events=[dict(id="new", start_tick=480, duration_ticks=120, note=65, velocity=81)]),
    event_op("delete_events", event_ids=["hit"]),
    event_op("duplicate_events", event_ids=["hit"], new_ids={"hit": "other"}, offset_ticks=240),
    event_op("transform_events", event_ids=["hit"], action="move", offset_ticks=240),
    event_op("transform_events", event_ids=["hit"], action="trim", start_tick=0, end_tick=120),
    event_op("transform_events", event_ids=["hit"], action="split", tick=120, new_ids={"hit": "right"}),
])
def test_protection_applies_to_every_new_event_operation(project, tmp_path, operation):
    service, source = project
    source["tracks"][0]["protected"] = True
    # A separate fixture project avoids changing protection outside the service.
    guarded = ProjectService(tmp_path / "protected")
    imported = guarded.import_file(tmp_path / "sample.wav", "audio", "test fixture", 10)
    assert imported["sha256"] == source["tracks"][0]["instrument"]["asset_sha256"]
    guarded.create(source)
    before = guarded.project_inspect()
    with pytest.raises(AdawError) as error:
        edit(guarded, "protected edit", operation)
    assert error.value.code == "ARTISTIC_BOUNDARY"
    assert guarded.project_inspect() == before


def test_three_undos_redos_preserve_external_edits_and_detect_conflicts(project):
    service, original = project
    revisions = [edit(service, str(value), event_op("set_track_gain", value=value))["revision"]
                 for value in (-4, -5, -6)]
    edit(service, "external pan", event_op("set_track_pan", value=.4))
    inverse = [service.undo(revision)["revision"] for revision in reversed(revisions)]
    assert service.source()[1]["tracks"][0]["gain_db"] == original["tracks"][0]["gain_db"]
    redone = [service.redo(revision)["revision"] for revision in reversed(inverse)]
    assert service.source()[1]["tracks"][0]["gain_db"] == -6
    assert service.source()[1]["tracks"][0]["pan"] == .4
    service.undo(redone[-1])
    assert service.source()[1]["tracks"][0]["gain_db"] == -5
    edit(service, "external collision", event_op("set_track_gain", value=-10))
    before = service.project_inspect()
    with pytest.raises(AdawError) as error:
        service.undo(redone[-2])
    assert error.value.code == "CONFLICT"
    assert service.project_inspect() == before
    with pytest.raises(AdawError, match="actual undo"):
        service.redo(revisions[0])


def test_undo_redo_note_creation_preserves_external_note_creation(project):
    service, _ = project
    first = dict(id="manual", start_tick=480, duration_ticks=120, note=65, velocity=81)
    second = {**first, "id": "agent", "start_tick": 960}
    revision = edit(service, "manual creation", event_op("add_events", events=[first]))["revision"]
    edit(service, "agent creation", event_op("add_events", events=[second]))
    undone = service.undo(revision)["revision"]
    assert {event["id"] for event in service.source()[1]["tracks"][0]["events"]} == {"hit", "agent"}
    service.redo(undone)
    assert {event["id"] for event in service.source()[1]["tracks"][0]["events"]} == {"hit", "manual", "agent"}


def test_noop_undo_cannot_redo_an_unrelated_revision(project):
    service, _ = project
    gain_revision = edit(service, "gain", event_op("set_track_gain", value=-6))["revision"]
    external = edit(service, "externally reset gain and pan", event_op("set_track_gain", value=-3),
                    event_op("set_track_pan", value=.5))["revision"]
    undone = service.undo(gain_revision)
    assert undone["revision"] == external and undone["changed"] is False
    assert service.undo(gain_revision)["changed"] is False
    with pytest.raises(AdawError, match="actual undo"):
        service.redo(undone["revision"])
    assert service.source()[1]["tracks"][0]["pan"] == .5


def test_midi_split_trim_stable_ids_and_sample_limit(project, tmp_path):
    service, original = project
    # Reproducible synthesizer uses native gate/frequency/velocity polyphony.
    module = tmp_path / "notes.dsp"
    module.write_text('import("stdfaust.lib"); freq=hslider("freq",440,20,20000,1); '
                      'gain=hslider("gain",0.5,0,1,0.01); gate=button("gate"); '
                      'process=(os.osc(freq)*gain*gate)<:_,_;', encoding="utf-8")
    instrument = service.import_file(module, "faust", "test synthesizer", 30)
    source = copy.deepcopy(original)
    source["tracks"][0].update(kind="faust_synth", instrument=dict(module_sha256=instrument["sha256"],
        parameters={}, voices=4, release_seconds=0))
    synth = ProjectService(tmp_path / "synth")
    synth.import_file(module, "faust", "test synthesizer", 30)
    synth.create(source)
    edit(synth, "split", event_op("transform_events", event_ids=["hit"], action="split", tick=120,
                                  new_ids={"hit": "right"}))
    events = synth.source()[1]["tracks"][0]["events"]
    assert [(e["id"], e["start_tick"], e["duration_ticks"]) for e in events] == [("hit", 0, 120), ("right", 120, 120)]
    edit(synth, "trim", event_op("transform_events", event_ids=["hit", "right"], action="trim",
                                 start_tick=60, end_tick=180))
    events = synth.source()[1]["tracks"][0]["events"]
    assert [(e["id"], e["start_tick"], e["duration_ticks"]) for e in events] == [("hit", 60, 60), ("right", 120, 60)]
    rendered = synth.render_project(30)
    signal, _ = sf.read(synth.content / rendered["render"]["data"]["audio_sha256"], always_2d=True)
    assert np.max(np.abs(signal[:1200])) < 1e-7
    assert np.max(np.abs(signal[1800:3000])) > .01
    assert np.max(np.abs(signal[4500:])) < 1e-7
    for operation in (event_op("transform_events", event_ids=["hit"], action="split", tick=120,
                                new_ids={"hit": "right"}),
                      event_op("transform_events", event_ids=["hit"], action="trim", start_tick=120, end_tick=240)):
        with pytest.raises(AdawError, match="source offsets"):
            edit(service, "unsupported", operation)
    edit(service, "sample end trim", event_op("transform_events", event_ids=["hit"], action="trim",
                                              start_tick=0, end_tick=60))
    rendered = service.render_project(30)
    signal, _ = sf.read(service.content / rendered["render"]["data"]["audio_sha256"], always_2d=True)
    assert np.max(np.abs(signal[1500:])) < 1e-7


def test_native_multiple_solo_mute_pan_and_unattenuated_monitor(project):
    service, source = project
    source = copy.deepcopy(source)
    for name, pan, mute, solo in [("left", -1, False, True), ("right", 1, False, True),
                                  ("muted", 0, True, True), ("excluded", 0, False, False)]:
        track = copy.deepcopy(source["tracks"][0])
        track.update(id=name, pan=pan, mute=mute, solo=solo)
        track["events"][0]["id"] = name + "_note"
        source["tracks"].append(track)
    graph, stems = compile_graph(source, service.read_content)
    rendered = service.render(graph, 30, record_nodes=stems, benchmark=False)
    def audio(name):
        return sf.read(service.content / rendered["data"]["stems"]["track_" + name]["sha256"])[0]
    for name in ("muted", "excluded", "kick"):
        assert np.max(np.abs(audio(name + "_level"))) == 0
        assert np.max(np.abs(audio(name + "_monitor"))) > .01
    assert np.max(np.abs(audio("left_level")[:, 1])) == 0
    assert np.max(np.abs(audio("right_level")[:, 0])) == 0
    assert np.max(np.abs(audio("left_level")[:, 0])) > .01
    assert np.max(np.abs(audio("right_level")[:, 1])) > .01
    for bad in (1, "false", None):
        source["tracks"][0]["mute"] = bad
        with pytest.raises(AdawError):
            validate(source)


def test_faust_controls_use_validated_ranges_and_actual_default(project, tmp_path):
    service, _ = project
    module = tmp_path / "fx.dsp"
    module.write_text('declare name "Test"; gain=hslider("volume",0.5,0,1,0.01); process=*(gain),*(gain);', encoding="utf-8")
    imported = service.import_file(module, "faust", "bounded control test", 30)
    binding = imported["validation"]["catalog"][0]["name"]
    edit(service, "insert", dict(kind="append_bus_insert", bus_id="drums",
         insert=dict(module_sha256=imported["sha256"], parameters={})))
    row = service.parameter_catalogs()[0]
    assert row["kind"] == "faust" and row["module_sha256"] == imported["sha256"]
    assert row["parameters"][0]["binding"] == binding
    assert row["parameters"][0]["value"] == .5
    with pytest.raises(AdawError):
        edit(service, "outside range", dict(kind="set_bus_insert_parameter", bus_id="drums", insert_index=0,
                                              binding=binding, value=2))
    edit(service, "control", dict(kind="set_bus_insert_parameter", bus_id="drums", insert_index=0,
                                 binding=binding, value=.25))
    assert service.parameter_catalogs()[0]["parameters"][0]["value"] == .25
