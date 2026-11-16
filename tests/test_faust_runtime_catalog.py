"""Real polyphonic controls must persist AND alter real native audio."""
from concurrent.futures import ThreadPoolExecutor
import copy

import numpy as np
import pytest
import soundfile as sf

from app.errors import AdawError
from app.project import ProjectService
from test_project import project


@pytest.fixture
def synth(project, tmp_path):
    _, source = project
    service = ProjectService(tmp_path / "runtime-synth")
    module = tmp_path / "runtime-synth.dsp"
    module.write_text('freq=nentry("freq",440,20,20000,1); gain=nentry("gain",.5,0,1,.01); '
                      'gate=button("gate"); level=hslider("level",.3,0,1,.01); '
                      'process=os.osc(freq)*gain*level*en.adsr(.01,.03,.7,.1,gate)<:_,_; effect=_,_;', encoding="utf-8")
    imported = service.import_file(module,"faust","polyphonic native-control regression",30)
    source["tracks"][0].update(kind="faust_synth", instrument=dict(module_sha256=imported["sha256"],
        parameters={},voices=8,release_seconds=.2))
    service.create(source)
    return service


def edit(service, name, operation):
    return service.edit(dict(command_id=name,base_revision=service.source()[0],reason=name,operations=[operation]))


def test_exposed_synth_control_changes_native_audio_and_survives_fresh_service(synth):
    before=synth.render_project(30)
    catalog=synth.parameter_catalogs()[0]["parameters"]
    native=before["render"]["data"]["nodes"]["track_kick"]["catalog"]
    assert {item["binding"] for item in catalog} == {item["name"] for item in native}
    assert all(item["label"] not in {"freq","gain","gate"} for item in catalog)
    level=next(item for item in catalog if item["label"]=="level")
    assert level["binding"] != "/dawdreamer/level"
    edit(synth,"halve native level",dict(kind="set_instrument_parameter",track_id="kick",binding=level["binding"],value=.15))
    fresh=ProjectService(synth.root)
    assert fresh.parameter_catalogs()[0]["parameters"][0]["value"] == .15
    after=fresh.render_project(30)
    a,_=sf.read(synth.content / before["render"]["data"]["audio_sha256"])
    b,_=sf.read(synth.content / after["render"]["data"]["audio_sha256"])
    assert np.sqrt(np.mean(a*a)) > 1e-5
    # Compare the sounding note (0..5000 frames); voice release can change tails.
    assert np.sqrt(np.mean(b[1000:4000]**2)) / np.sqrt(np.mean(a[1000:4000]**2)) == pytest.approx(.5,abs=.00001)
    assert np.sqrt(np.mean(b*b)) < .6 * np.sqrt(np.mean(a*a))
    assert after["revision"]==fresh.source()[0]
    for binding,value in [("/dawdreamer/level",.1),("/dawdreamer/gate",1),('/missing',.2),(level["binding"],2)]:
        previous=fresh.source()[0]
        with pytest.raises(AdawError):
            edit(fresh,"invalid "+binding+str(value),dict(kind="set_instrument_parameter",track_id="kick",binding=binding,value=value))
        assert fresh.source()[0]==previous


def test_synth_catalog_cache_handles_context_changes_threads_and_cold_apply(synth, monkeypatch, tmp_path):
    revision,source=synth.source()
    variants=[]
    for voices,rate,block,release in [(1,48000,256,.2),(8,44100,256,.2),(8,48000,128,.2),(8,48000,256,.4)]:
        changed=copy.deepcopy(source); changed.update(sample_rate=rate,block_size=block)
        changed["tracks"][0]["instrument"].update(voices=voices,release_seconds=release)
        variants.append(changed)
    variants.insert(0,copy.deepcopy(variants[0]))  # Two first-request API callers share a key.
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(lambda s:synth._synth_validation(s["tracks"][0]["instrument"],s),variants))
    assert all(any(item["label"]=="level" for item in r["catalog"]) for r in results)
    assert synth.source()[0]==revision
    cold=ProjectService(synth.root)
    def unexpected_worker(*args,**kwargs):
        raise AssertionError("Validated native catalogs must survive fresh service instances")
    monkeypatch.setattr(cold,"run_worker",unexpected_worker)
    for s in variants:
        assert cold._synth_validation(s["tracks"][0]["instrument"],s)["catalog"]
    # A source race may introduce an uncached runtime after preflight. Never
    # start a worker job (which needs SQLite writes) under the source-write lock.
    unseen=copy.deepcopy(source)
    unseen["tracks"][0]["instrument"]["voices"]=3
    with cold.connect() as locked:
        locked.execute("BEGIN IMMEDIATE")
        with pytest.raises(AdawError) as error:
            cold._synth_validation(unseen["tracks"][0]["instrument"],unseen,locked)
        assert error.value.code=="STALE_REVISION"
    binding=cold.parameter_catalogs()[0]["parameters"][0]["binding"]
    synth.propose(dict(command_id="cold-apply",base_revision=revision,reason="cold process",operations=[
        dict(kind="set_instrument_parameter",track_id="kick",binding=binding,value=.1)]))
    applied=cold.apply("cold-apply")
    undone=ProjectService(synth.root).undo(applied["revision"])
    assert ProjectService(synth.root).redo(undone["revision"])["revision"]
    # A different DSP with a different range may not inherit the prior catalog.
    module=tmp_path / "different-runtime.dsp"
    module.write_text('declare name "Changed"; freq=nentry("freq",440,20,20000,1); gain=nentry("gain",.5,0,1,.01); '
                      'gate=button("gate"); level=hslider("brightness",2,1,4,.1); '
                      'process=os.osc(freq)*gain*level*gate<:_,_; effect=_,_;',encoding="utf-8")
    imported=synth.import_file(module,"faust","different native controls",30)
    edit(synth,"replace instrument",dict(kind="set_instrument_module",track_id="kick",module_sha256=imported["sha256"],parameters={}))
    controls=synth.parameter_catalogs()[0]["parameters"]
    assert [item["label"] for item in controls]==["brightness"]
    assert controls[0]["min"]==1 and controls[0]["max"]==4
