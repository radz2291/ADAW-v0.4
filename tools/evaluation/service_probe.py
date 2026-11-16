"""Independent current-candidate service/audio probe; no production modifications."""
import argparse
import hashlib
import io
import json
import time
import uuid
from pathlib import Path
import numpy as np
import soundfile as sf
from app.project import ProjectService
from app.errors import AdawError
from tools.evaluation.fixture import create


def run(folder):
    identity=create(folder)
    service=ProjectService(identity["root"])
    results=[]
    def check(name,fn):
        try:
            detail=fn()
            results.append(dict(name=name,status="PASS",detail=detail))
        except Exception as error:
            results.append(dict(name=name,status="FAIL",detail=repr(error)))
    def expect(condition,message):
        if not condition: raise AssertionError(message)
    def edit(operations,base=None):
        return service.edit(dict(command_id="evaluator-"+uuid.uuid4().hex,base_revision=base or service.source()[0],reason="Independent evaluation",operations=operations))
    def op(kind,track="evaluation-midi",**kw): return dict(kind=kind,track_id=track,**kw)
    def tracks(): return {t["id"]:t for t in service.source()[1]["tracks"]}
    def protected():
        revision,source=service.source()
        for operation in [op("add_events","evaluation-protected",events=[dict(id="bad",start_tick=0,duration_ticks=240,note=60,velocity=90)]),op("delete_events","evaluation-protected",event_ids=["protected-eval-0"]),op("transform_events","evaluation-protected",event_ids=["protected-eval-0"],action="move",offset_ticks=240)]:
            try: edit([op("set_track_gain",value=-9),operation])
            except AdawError as error: expect(error.code=="ARTISTIC_BOUNDARY",str(error))
            else: raise AssertionError("Protected edit accepted")
            expect(service.source()==(revision,source),"Rejected batch partially changed source")
    check("protected event/clip batches atomic",protected)
    def history():
        initial=tracks()["evaluation-midi"]["gain_db"]
        revisions=[edit([op("set_track_gain",value=value)])["revision"] for value in [-10,-9,-8]]
        edit([op("set_track_gain","evaluation-sample",value=-7)])
        undos=[]
        for revision,expected in zip(reversed(revisions),[-9,-10,initial]):
            undos.append(service.undo(revision)["revision"])
            expect(tracks()["evaluation-midi"]["gain_db"]==expected,"Undo order")
            expect(tracks()["evaluation-sample"]["gain_db"]==-7,"Unrelated change lost")
        for revision,expected in zip(reversed(undos),[-10,-9,-8]):
            service.redo(revision)
            expect(tracks()["evaluation-midi"]["gain_db"]==expected,"Redo order")
        target=edit([op("set_track_gain",value=-6)])["revision"]
        edit([op("set_track_gain",value=-4)])
        before=service.source()
        try: service.undo(target)
        except AdawError: pass
        else: raise AssertionError("Conflicting undo accepted")
        expect(service.source()==before,"Conflicting undo overwrote source")
    check("three undo redo plus unrelated and conflict",history)
    def agent():
        pending=service.propose(dict(command_id="independent-agent-proposal",base_revision=service.source()[0],reason="Pending agent proposal",operations=[op("set_track_gain","evaluation-sample",value=-2)]))
        edit([op("set_track_pan",value=.5)])
        expect(tracks()["evaluation-sample"]["gain_db"]==-7,"Manual edit applied agent proposal")
        service.apply(pending["proposal_id"])
        expect(tracks()["evaluation-midi"]["pan"]==.5,"Agent overwrote manual change")
    check("manual and pending proposals separate",agent)
    def stable():
        note=dict(id="independent-new",start_tick=8000,duration_ticks=240,note=55,velocity=73)
        edit([op("add_events",events=[note])])
        expect(note in tracks()["evaluation-midi"]["events"],"Add mismatch")
        edit([op("duplicate_events",event_ids=["independent-new"],new_ids={"independent-new":"independent-copy"},offset_ticks=240)])
        expect({**note,"id":"independent-copy","start_tick":8240} in tracks()["evaluation-midi"]["events"],"Duplicate mismatch")
        edit([op("delete_events",event_ids=["independent-new","independent-copy"])])
        expect(not any(n["id"].startswith("independent-") for n in tracks()["evaluation-midi"]["events"]),"Deletion mismatch")
        before=service.source()[1]
        edit([op("delete_events",event_ids=[])])
        expect(service.source()[1]==before,"Empty delete changed source")
    check("stable create duplicate delete and empty selection",stable)
    def render():
        started=time.perf_counter()
        rendition=service.render_project(60)
        data=service.read_content(rendition["render"]["data"]["audio_sha256"])
        audio,rate=sf.read(io.BytesIO(data),always_2d=True)
        return audio,dict(revision=rendition["revision"],sha256=hashlib.sha256(data).hexdigest(),seconds=time.perf_counter()-started,rate=rate)
    audio_evidence=[]
    def signal():
        edit([op("set_track_pan",value=0),op("set_track_gain",value=-6),op("set_track_solo",value=True)])
        reference,meta=render();audio_evidence.append(meta)
        edit([op("set_track_gain",value=-12)])
        quiet,meta=render();audio_evidence.append(meta)
        ratio=float(np.sqrt(np.mean(quiet**2))/np.sqrt(np.mean(reference**2)))
        expect(abs(ratio-10**(-6/20))<.0001,"Native gain ratio incorrect")
        edit([op("set_track_pan",value=1)])
        right,meta=render();audio_evidence.append(meta)
        expect(float(np.max(np.abs(right[:,0])))<1e-7,"Pan right not silent left")
        edit([op("set_track_mute",value=True)])
        silence,meta=render();audio_evidence.append(meta)
        expect(float(np.max(np.abs(silence)))<1e-7,"Mute does not override solo or other tracks leak")
        return dict(gain_ratio=ratio,silence_peak=float(np.max(np.abs(silence))))
    check("native gain pan solo mute semantics",signal)
    return dict(identity=identity,checks=results,audio=audio_evidence,final_revision=service.source()[0])

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("folder");parser.add_argument("output")
    args=parser.parse_args();report=run(args.folder)
    Path(args.output).parent.mkdir(parents=True,exist_ok=True)
    Path(args.output).write_text(json.dumps(report,indent=2))
    print(json.dumps(report))
