import copy
import json
import numpy as np
import pytest
import soundfile as sf

from app.arrangement import compile_graph, validate
from app.contracts import canonical, digest, tick_sample
from app.errors import AdawError
from app.project import ProjectService
from app.quality import analyze, analyze_delivery, estimated_true_peak
from app.revisions import merge_source


@pytest.fixture
def project(tmp_path):
    service = ProjectService(tmp_path/"project")
    path = tmp_path/"sample.wav"
    sf.write(path,np.sin(np.arange(4800)*2*np.pi*440/48000)*.1,48000,subtype="FLOAT")
    imported = service.import_file(path,"audio","test-generated sine",10)
    profile = dict(id="test-profile",status="temporary_engineering_profile",purpose="test only",sample_rate=48000,
        channels=2,subtype="PCM_24",min_lufs=-30,max_lufs=-10,max_sample_peak_dbfs=-1,
        max_estimated_true_peak_dbfs=-1,true_peak_margin_db=.25,max_dc=.001,dither_seed=1)
    source = dict(schema="adaw.arrangement@1",title="Test",brief="temporary test fixture",tempo=144,ppq=960,
        sample_rate=48000,block_size=256,length_ticks=3840,tail_frames=8000,fade_frames=240,
        sections=[dict(id="one",start_tick=0,end_tick=3840,mood="test",swing=.5)],
        tracks=[dict(id="kick",role="percussion",kind="samples",bus="drums",gain_db=-3,pan=0,protected=False,
        instrument=dict(asset_sha256=imported["sha256"],fade_frames=12),inserts=[],
        events=[dict(id="hit",start_tick=0,duration_ticks=240,note=60,velocity=100)])],
        buses=[dict(id="drums",gain_db=0,inserts=[])],master=dict(gain_db=0,inserts=[]),profile=profile)
    service.create(source)
    return service,source


def command(service, name, value):
    return dict(command_id=name,base_revision=service.source()[0],reason="test change",
                operations=[dict(kind="set_track_gain",track_id="kick",value=value)])


def test_proposal_isolated_stale_and_idempotent(project):
    service,original = project
    before = service.project_inspect()
    first,second = command(service,"first",-6),command(service,"second",-9)
    service.propose(first)
    service.propose(second)
    assert service.project_inspect() == before
    applied = service.apply("first")
    assert service.apply("first")["revision"] == applied["revision"]
    assert service.propose(first)["idempotent"]
    with pytest.raises(AdawError) as conflict:
        service.apply("second")
    assert conflict.value.code == "CONFLICT"
    assert conflict.value.details["conflicts"] == [
        dict(path=["tracks", "kick", "gain_db"], reason="DIVERGENT_EDIT",
             base=-3, current=-6, proposed=-9)
    ]
    with pytest.raises(AdawError,match="reused"):
        service.propose({**first,"reason":"different payload"})
    assert len(service.history()["revisions"]) == 2
    assert service.source(before["revision"])[1] == original
    assert service.source()[1]["tracks"][0]["gain_db"] == -6


def test_invalid_operation_batch_is_atomic(project):
    service,_ = project
    before = service.project_inspect()
    cmd = command(service,"invalid",-6)
    cmd["operations"].append(dict(kind="move_event",track_id="kick",event_id="hit",start_tick=99999))
    with pytest.raises(AdawError):
        service.propose(cmd)
    assert service.project_inspect() == before
    assert not service.history()["proposals"]


def test_event_edit_is_revisioned_and_validated(project):
    service,original = project
    before = service.source()[0]
    cmd = command(service,"event-edit",0)
    cmd["operations"] = [dict(kind="edit_event",track_id="kick",event_id="hit",
        changes=dict(note=48,velocity=73,duration_ticks=360,start_tick=120))]
    service.propose(cmd)
    service.apply(cmd["command_id"])
    assert service.source()[1]["tracks"][0]["events"][0]["velocity"] == 73
    assert service.source(before)[1] == original
    invalid = command(service,"bad-note",0)
    invalid["operations"] = [dict(kind="edit_event",track_id="kick",event_id="hit",changes=dict(note=200))]
    with pytest.raises(AdawError):
        service.propose(invalid)


def test_apply_revalidates_import_after_proposal(project):
    service,source = project
    before = service.source()[0]
    service.propose(command(service,"pending",-8))
    (service.content/source["tracks"][0]["instrument"]["asset_sha256"]).write_bytes(b"corrupted after proposal")
    with pytest.raises(AdawError):
        service.apply("pending")
    assert service.source()[0] == before


def test_arrangement_proposal_changes_sections_and_events_only(project):
    service, original = project
    cmd = command(service, "arrangement", 0)
    sections = [dict(id="intro", start_tick=0, end_tick=1920, mood="sparse", swing=.5),
                dict(id="drop", start_tick=1920, end_tick=3840, mood="full", swing=.56)]
    events = [{**original["tracks"][0]["events"][0], "start_tick": 1920}]
    cmd["operations"] = [dict(kind="set_arrangement", sections=sections, track_events={"kick": events})]
    service.propose(cmd)
    assert service.source()[1] == original
    service.apply(cmd["command_id"])
    expected = copy.deepcopy(original)
    expected["sections"] = sections
    expected["tracks"][0]["events"] = events
    assert service.source()[1] == expected


def test_disjoint_proposal_rebase_and_selective_undo(project):
    service, original = project
    move = command(service, "ghost-move", 0)
    move["operations"] = [dict(kind="move_event", track_id="kick", event_id="hit", start_tick=120)]
    saturation = command(service, "drum-bus", 0)
    saturation["operations"] = [dict(kind="set_bus_gain", bus_id="drums", value=-2)]
    service.propose(move)
    preview = service.inspect_proposal("ghost-move")
    service.propose(saturation)
    bus_revision = service.apply("drum-bus")["revision"]
    merged = service.apply("ghost-move")
    assert merged["rebased"] and merged["preview_status"] == "STALE"
    merged_revision, source = service.source()
    assert merged["revision"] == merged_revision
    assert source["tracks"][0]["events"][0]["start_tick"] == 120
    assert source["buses"][0]["gain_db"] == -2
    assert service.history()["revisions"][-1]["parent"] == bus_revision
    assert service.inspect_proposal("ghost-move") == {**preview, "applied": merged_revision}
    assert service.apply("ghost-move") == {**merged, "idempotent": True}

    service.propose(command(service, "later-level", -8))
    service.apply("later-level")
    undone = service.undo(merged_revision)
    expected = copy.deepcopy(original)
    expected["buses"][0]["gain_db"] = -2
    expected["tracks"][0]["gain_db"] = -8
    assert service.source() == (undone["revision"], expected)
    assert service.undo(merged_revision) == {**undone, "idempotent": True}


def test_real_faust_bus_drive_interleaves_with_event_move(project):
    service, _ = project
    imported = service.import_file("fixtures/saturation.dsp", "faust", "G0 saturation fixture", 30)
    binding = next(p["name"] for p in imported["validation"]["catalog"] if p["name"].endswith("/drive"))
    add = command(service, "add-saturation", 0)
    add["operations"] = [dict(kind="append_bus_insert", bus_id="drums",
                              insert=dict(module_sha256=imported["sha256"], parameters={binding: 1}))]
    service.propose(add)
    service.apply(add["command_id"])

    agent = command(service, "ghost-hit", 0)
    agent["operations"] = [dict(kind="move_event", track_id="kick", event_id="hit", start_tick=120)]
    human = command(service, "raise-drive", 0)
    points = [{"tick": 0, "value": 1}, {"tick": 216, "value": 4}]
    human["operations"] = [
        dict(kind="set_bus_insert_parameter", bus_id="drums", insert_index=0, binding=binding, value=4),
        dict(kind="set_faust_bus_automation", bus_id="drums", insert_index=0, binding=binding, points=points),
    ]
    service.propose(agent)
    service.propose(human)
    service.apply(human["command_id"])
    merged = service.apply(agent["command_id"])
    assert merged["rebased"] and merged["preview_status"] == "STALE"
    rendition = service.render_project(30, revision=merged["revision"])
    audio, _ = sf.read(service.content / rendition["render"]["data"]["audio_sha256"], always_2d=True)
    assert rendition["manifest"]["revision"] == merged["revision"]
    assert np.count_nonzero(audio[:tick_sample(120, 144, 960, 48000)]) == 0
    assert np.max(np.abs(audio)) > .09
    early = np.sqrt(np.mean(audio[3000:4000] ** 2))
    late = np.sqrt(np.mean(audio[5200:6200] ** 2))
    assert late > 3 * early > 0
    assert rendition["source"]["buses"][0]["inserts"][0]["parameters"][binding] == 4
    service.undo(merged["revision"])
    _, source = service.source()
    assert source["tracks"][0]["events"][0]["start_tick"] == 0
    assert source["buses"][0]["inserts"][0]["parameters"][binding] == 4
    assert source["buses"][0]["inserts"][0]["automation"][binding] == points

    invalid = command(service, "invalid-drive", 0)
    invalid["operations"] = [{**human["operations"][0], "value": 100}]
    with pytest.raises(AdawError, match="Number above"):
        service.propose(invalid)


def test_convergent_proposals_do_not_create_phantom_revisions(project):
    service, _ = project
    service.propose(command(service, "first", -6))
    service.propose(command(service, "second", -6))
    first = service.apply("first")
    second = service.apply("second")
    assert second["revision"] == first["revision"]
    assert second["rebased"] and not second["changed"]
    assert second["preview_status"] == "MATCHES_SOURCE"
    assert service.apply("second") == {**second, "idempotent": True}
    assert len(service.history()["revisions"]) == 2


def test_undo_conflict_preserves_later_same_field_edit(project):
    service, _ = project
    service.propose(command(service, "first", -6))
    first = service.apply("first")
    service.propose(command(service, "second", -9))
    second = service.apply("second")
    with pytest.raises(AdawError) as conflict:
        service.undo(first["revision"])
    assert conflict.value.code == "CONFLICT"
    assert service.source()[0] == second["revision"]


def test_timing_changes_conflict_with_event_and_other_timing_edits(project):
    _, source = project
    head = {**source, "schema": "adaw.arrangement@2", "time_map": [
        dict(tick=0, bpm=144, numerator=4, denominator=4),
        dict(tick=1920, bpm=96, numerator=4, denominator=4),
    ]}
    validate(head)
    timing = {**source, "tempo": 120}
    events = copy.deepcopy(source)
    events["tracks"][0]["events"][0]["start_tick"] = 1920
    for candidate in (timing, events):
        with pytest.raises(AdawError) as conflict:
            merge_source(source, head, candidate, base_revision="base", current_revision="head")
        assert conflict.value.code == "CONFLICT"
        assert any(item["path"] == ["time_map"] and item["reason"] == "TIMING_CONTEXT_CHANGED"
                   for item in conflict.value.details["conflicts"])
    gains = copy.deepcopy(source)
    gains["tracks"][0]["gain_db"] = -7
    merged = merge_source(source, head, gains, base_revision="base", current_revision="head")
    assert merged["time_map"] == head["time_map"]
    assert merged["tracks"][0]["gain_db"] == -7
    validate(merged)


def test_compiler_maps_absolute_ticks_and_source_hash(project):
    service,source = project
    graph,stems = compile_graph(source,service.read_content)
    assert graph["frames"] == 88000
    event = graph["nodes"][0]["config"]["events"][0]
    assert event["duration_frames"] == tick_sample(240,144,960,48000)
    assert stems == ["track_kick_monitor", "track_kick_level"]
    assert digest(canonical(graph)) == digest(canonical(compile_graph(copy.deepcopy(source),service.read_content)[0]))


def test_offline_parallel_send_raises_rms_by_declared_linear_gain(project):
    service, original = project
    source = copy.deepcopy(original)
    source["schema"] = "adaw.arrangement@2"
    source["time_map"] = [{"tick": 0, "bpm": 144, "numerator": 4, "denominator": 4}]
    source["buses"].append({"id": "parallel", "gain_db": 0, "inserts": [],
                            "send_from": [{"bus": "drums", "gain_db": -6}]})
    direct, _ = compile_graph(original, service.read_content)
    parallel, _ = compile_graph(source, service.read_content)
    first = service.render(direct, 30, benchmark=False)
    second = service.render(parallel, 30, benchmark=False)
    assert second["quality"]["rms"] / first["quality"]["rms"] == pytest.approx(1 + 10 ** (-6 / 20), abs=1e-6)
    source["buses"][0]["send_from"] = [{"bus": "parallel", "gain_db": -6}]
    with pytest.raises(AdawError, match="earlier bus"):
        validate(source)


def test_faust_sidechain_routes_independent_main_and_key(project, tmp_path):
    service, source = project
    module = tmp_path / "sidechain.dsp"
    module.write_text("duck(l,r,kl,kr) = l*g,r*g with { g = 1/(1+8*max(abs(kl),abs(kr))); };\nprocess = duck;",
                      encoding="utf-8")
    imported = service.import_file(module, "faust", "Generated main/key routing test", 30)
    assert (imported["validation"]["inputs"], imported["validation"]["outputs"]) == (4, 2)
    source["schema"] = "adaw.arrangement@2"
    source["time_map"] = [{"tick": 0, "bpm": 144, "numerator": 4, "denominator": 4}]
    key = copy.deepcopy(source["tracks"][0])
    key.update(id="key", bus="trigger", events=[])
    source["tracks"].append(key)
    source["buses"].insert(0, {"id": "trigger", "gain_db": 0, "inserts": []})
    source["buses"][1]["inserts"].append(
        {"module_sha256": imported["sha256"], "parameters": {}, "key_bus": "trigger"})
    graphs = []
    for events in ([], [{"id": "trigger-hit", "start_tick": 0, "duration_ticks": 240,
                         "note": 60, "velocity": 127}]):
        key["events"] = events
        service.validate_dependencies(source)
        graph, _ = compile_graph(source, service.read_content)
        render = service.render(graph, 30, record_nodes=["bus_drums_level"], benchmark=False)
        stem = render["data"]["stems"]["bus_drums_level"]["sha256"]
        signal, _ = sf.read(service.content / stem)
        graphs.append(signal)
    no_key, keyed = graphs
    assert np.sqrt(np.mean(keyed[300:4200] ** 2)) < .75 * np.sqrt(np.mean(no_key[300:4200] ** 2))
    assert np.allclose(keyed[5050:], no_key[5050:], atol=1e-7)


def test_unknown_fields_duplicate_ids_and_bad_hash_rejected(project):
    service,source = project
    for mutate in (lambda s:s.update(hidden=True),
                   lambda s:s["tracks"][0]["events"].append(s["tracks"][0]["events"][0]),
                   lambda s:s["tracks"][0]["instrument"].update(asset_sha256="../secret")):
        bad = copy.deepcopy(source)
        mutate(bad)
        with pytest.raises(AdawError):
            validate(bad)


def test_protected_motif_requires_separate_authorization(project,tmp_path):
    service,source = project
    source["tracks"][0]["protected"] = True
    other = ProjectService(tmp_path/"protected")
    asset = source["tracks"][0]["instrument"]["asset_sha256"]
    other.import_file(service.content/asset,"audio","test asset",10)
    other.create(source)
    cmd = command(other,"protected",-4)
    cmd["operations"] = [dict(kind="move_event",track_id="kick",event_id="hit",start_tick=120)]
    with pytest.raises(AdawError,match="Protected"):
        other.propose(cmd)
    cmd["operations"] = [dict(kind="set_arrangement", sections=source["sections"], track_events={"kick": []})]
    with pytest.raises(AdawError, match="Protected"):
        other.propose(cmd)


def test_pcm24_independent_decode_and_bad_profile(tmp_path,project):
    _,source = project
    audio = .2*np.sin(2*np.pi*997*np.arange(48000)/48000)
    path = tmp_path/"pcm.wav"
    sf.write(path,np.column_stack([audio,audio]),48000,subtype="PCM_24")
    assert analyze(path)["independent_decode"].startswith("PASS")
    result = analyze_delivery(path,source["profile"],48001)
    assert result["status"] == "FAIL" and result["rules"]["frames"] == "FAIL"
    profile = {**source["profile"],"max_sample_peak_dbfs":-30}
    assert analyze_delivery(path,profile,48000)["rules"]["sample_peak"] == "FAIL"


@pytest.mark.parametrize("frequency,phase",[(997,.3),(6000,np.pi/2),(12000,np.pi/4),(18000,.3),(20000,.7)])
def test_true_peak_estimator_analytic_sine_calibration(frequency,phase):
    n = np.arange(48000)
    x = .8*np.sin(2*np.pi*frequency*n/48000+phase)
    x[:4800] *= np.linspace(0,1,4800)
    x[-4800:] *= np.linspace(1,0,4800)
    peak = estimated_true_peak(x[:,None])
    assert abs(20*np.log10(peak/.8)) < .12
    if frequency == 12000:
        assert peak > np.max(np.abs(x))*1.3


def test_missing_content_does_not_change_revision(project):
    service,source = project
    before = service.project_inspect()["revision"]
    # Injection into disposable test storage, never production authority.
    (service.content/source["tracks"][0]["instrument"]["asset_sha256"]).write_bytes(b"corrupt")
    with pytest.raises(AdawError,match="corrupt"):
        service.propose(command(service,"corrupt",-6))
    assert service.project_inspect()["revision"] == before


def test_native_nonfinite_metadata_is_explicit_json():
    from app.worker import report_safe
    warnings = []
    result = report_safe({"placeholder":float("nan"), "gain":.47}, warnings=warnings)
    assert result["placeholder"]["status"] == "UNAVAILABLE"
    assert result["gain"] == .47 and warnings[0]["code"] == "NATIVE_METADATA_NONFINITE"
    canonical(result)
