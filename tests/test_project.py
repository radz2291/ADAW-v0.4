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
    with pytest.raises(AdawError,match="Head changed"):
        service.apply("second")
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


def test_compiler_maps_absolute_ticks_and_source_hash(project):
    service,source = project
    graph,stems = compile_graph(source,service.read_content)
    assert graph["frames"] == 88000
    event = graph["nodes"][0]["config"]["events"][0]
    assert event["duration_frames"] == tick_sample(240,144,960,48000)
    assert stems == ["track_kick_level"]
    assert digest(canonical(graph)) == digest(canonical(compile_graph(copy.deepcopy(source),service.read_content)[0]))


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
