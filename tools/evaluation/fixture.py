"""Independent evaluator's disposable three-track/two-bus real-audio fixture."""
import argparse
import json
from copy import deepcopy
from pathlib import Path
import numpy as np
import soundfile as sf
from app.project import ProjectService


def create(folder, two_bars=False, sustained=False):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=False)
    dsp = folder / "evaluation-tone.dsp"
    dsp.write_text('freq=nentry("freq",440,20,20000,1);\ngain=nentry("gain",0.5,0,1,.01);\ngate=button("gate");\nlevel=hslider("level",.3,0,1,.01);\nprocess=os.osc(freq)*gain*level*en.adsr(.01,.03,.7,.1,gate)<:_,_;\neffect=_,_;\n')
    sample = folder / "evaluation-sample.wav"
    t = np.arange(24000) / 48000
    tone = .1 * np.sin(2 * np.pi * 220 * t) * np.sin(np.pi * np.arange(24000) / 24000) ** 2
    sf.write(sample, np.column_stack((tone, tone)), 48000, subtype="PCM_24")
    service = ProjectService(folder / "project")
    module = service.import_file(dsp, "faust", "Evaluator authored sine", 30)["sha256"]
    asset = service.import_file(sample, "audio", "Evaluator authored sample", 30)["sha256"]
    notes = [dict(id=f"eval-{i}",note=60+i,velocity=90,start_tick=i*960,duration_ticks=480) for i in range(8)]
    track = dict(id="evaluation-midi",role="lead",kind="faust_synth",bus="music",gain_db=-12,pan=0,protected=False,inserts=[],instrument=dict(module_sha256=module,parameters={},voices=8,release_seconds=.2),events=notes)
    protected=deepcopy(track)
    protected.update(id="evaluation-protected",protected=True,bus="other")
    protected["events"]=[{**n,"id":"protected-"+n["id"]} for n in notes]
    samples=dict(id="evaluation-sample",role="sample",kind="samples",bus="other",gain_db=-12,pan=0,protected=False,inserts=[],instrument=dict(asset_sha256=asset,fade_frames=24),events=[dict(id="sample-1",start_tick=0,duration_ticks=960,velocity=90,note=60)])
    source=dict(schema="adaw.arrangement@2",title="Independent interaction fixture",brief="Disposable evaluation only",tempo=120,ppq=960,sample_rate=48000,block_size=256,length_ticks=10560,tail_frames=24000,fade_frames=240,time_map=[dict(tick=t,bpm=b,numerator=n,denominator=4) for t,b,n in [(0,120,4),(3840,104,4),(7680,104,3)]],sections=[dict(id=n,start_tick=a,end_tick=b,mood="test",swing=.5) for n,a,b in [("intro",0,3840),("bridge",3840,7680),("turn",7680,10560)]],tracks=[track,samples,protected],buses=[dict(id=n,gain_db=0,inserts=[]) for n in ["music","other"]],master=dict(gain_db=0,inserts=[]),profile=dict(id="evaluation",status="temporary_engineering_profile",purpose="test only",sample_rate=48000,channels=2,subtype="PCM_24",min_lufs=-40,max_lufs=-10,max_sample_peak_dbfs=-1,max_estimated_true_peak_dbfs=-1,true_peak_margin_db=.25,max_dc=.001,dither_seed=1))
    if two_bars:
        source["length_ticks"]=7680
        source["time_map"]=source["time_map"][:2]
        source["sections"]=source["sections"][:2]
    if sustained:
        for item in source["tracks"]:
            if item["kind"]=="faust_synth":
                item["events"]=[{**item["events"][0],"duration_ticks":source["length_ticks"]}]
    service.create(source)
    rendition=service.render_project(60)
    return dict(root=str(service.root),rendition=rendition["id"],revision=rendition["revision"])

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("folder")
    parser.add_argument("--two-bars",action="store_true")
    parser.add_argument("--sustained",action="store_true")
    args=parser.parse_args()
    print(json.dumps(create(args.folder,args.two_bars,args.sustained)))
