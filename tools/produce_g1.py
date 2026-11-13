"""Run the real CLI production/evaluation cycle; never writes project authority."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
import numpy as np
import pyloudnorm as pyln
import soundfile as sf
from scipy.signal import butter, sosfilt

from app.contracts import canonical, digest, file_hash, tick_sample
from app.quality import analyze_delivery, estimated_true_peak


def overlap(rendition):
    source = rendition["source"]
    stage = Path(rendition["render"]["stage"])
    rate = source["sample_rate"]
    sos = butter(4,[30,140],btype="bandpass",fs=rate,output="sos")
    kick = sosfilt(sos,sf.read(stage/"track_kick_level.wav")[0],axis=0)
    bass = sosfilt(sos,sf.read(stage/"track_bass808_level.wav")[0],axis=0)
    events = next(t for t in source["tracks"] if t["id"]=="kick")["events"]
    result = {}
    for name,lo,hi in [("first_drop",4,12),("already_separated_fracture",12,20)]:
        ratios = []
        for event in events:
            if lo*3840 <= event["start_tick"] < hi*3840:
                frame = tick_sample(event["start_tick"],source["tempo"],source["ppq"],rate)
                window = round(.070*rate)
                ratios.append(float(np.sqrt(np.mean(bass[frame:frame+window]**2))/np.sqrt(np.mean(kick[frame:frame+window]**2))))
        result[name] = {"mean_bass_to_kick_rms_first_70ms":float(np.mean(ratios)),"kick_count":len(ratios)}
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",required=True)
    parser.add_argument("--baseline",required=True)
    parser.add_argument("--evidence",required=True)
    parser.add_argument("--delivery",required=True)
    parser.add_argument("--timeout",required=True,type=float)
    args=parser.parse_args()
    evidence,delivery=Path(args.evidence),Path(args.delivery)
    if evidence.exists():
        raise RuntimeError("Use a fresh evidence run directory")
    evidence.mkdir(parents=True)
    delivery.mkdir(parents=True,exist_ok=True)
    diagnostics=delivery.parent/(delivery.name+"-diagnostics")
    diagnostics.mkdir(parents=True,exist_ok=True)
    trace=[]
    def cli(*command,expect=True):
        argv=[sys.executable,"-m","app","--root",args.root,"--timeout",str(args.timeout),*map(str,command)]
        start=time.perf_counter()
        proc=subprocess.run(argv,capture_output=True,text=True,encoding="utf-8")
        result=json.loads(proc.stdout)
        name=f"{len(trace):02d}-{command[0]}"
        (evidence/(name+".json")).write_bytes(canonical(result))
        (evidence/(name+".stderr.log")).write_text(proc.stderr,encoding="utf-8")
        trace.append(dict(argv=argv,result_file=name+".json",exit_code=proc.returncode,seconds=time.perf_counter()-start))
        (evidence/"trace.json").write_bytes(canonical(trace))
        if result["ok"] != expect:
            raise RuntimeError(f"Unexpected CLI status: {name}: {result.get('error')}")
        return result["data"] if expect else result["error"]
    def revise(label,base,operations,reason):
        command=dict(command_id=label,base_revision=base,reason=reason,operations=operations)
        path=evidence/(label+"-command.json")
        path.write_bytes(canonical(command))
        cli("proposal-create","--command",path)
        return cli("proposal-apply","--id",label)["revision"]
    baseline_envelope=json.loads(Path(args.baseline).read_text(encoding="utf-8-sig"))
    baseline=baseline_envelope["data"]
    (evidence/"baseline.json").write_bytes(canonical(baseline_envelope))
    source=baseline["source"]
    before_overlap=overlap(baseline)
    operations=[]
    for e in next(t for t in source["tracks"] if t["id"]=="bass808")["events"]:
        if 4*3840<=e["start_tick"]<12*3840 or 24*3840<=e["start_tick"]<36*3840:
            operations.append(dict(kind="move_event",track_id="bass808",event_id=e["id"],start_tick=e["start_tick"]+144))
    revised=revise("g1-bass-space",baseline["revision"],operations,
        "Measured first-drop bass/kick onset RMS ratio exceeds the already-separated section. Delay only overlapping-drop 808 notes by 144 ticks (62.5ms); retain notes, durations, protected snare and the separated fracture section. No compressor or sidechain assumption.")
    spaced=cli("project-render","--revision",revised)
    after_overlap=overlap(spaced)
    comparisons=[]
    for name,lo,hi in [("first-drop",4,12),("fracture-no-change",12,20)]:
        for label,render in [("A",baseline),("B",spaced)]:
            audio,rate=sf.read(render["render"]["audio_path"],always_2d=True)
            start=tick_sample(lo*3840,144,960,rate)
            end=tick_sample(hi*3840,144,960,rate)
            clip=audio[start:end].copy()
            loudness=pyln.Meter(rate).integrated_loudness(clip)
            clip*=10**((-23-loudness)/20)
            path=delivery/f"{name}-{label}-matched.wav"
            sf.write(path,clip,rate,subtype="FLOAT")
            comparisons.append(dict(context=name,label=label,rendition=render["id"],path=str(path.resolve()),sha256=file_hash(path),
                target_lufs=-23,measured_lufs=float(pyln.Meter(rate).integrated_loudness(sf.read(path)[0])),listening="NOT_EVALUATED"))
    (evidence/"kick-bass-comparison.json").write_bytes(canonical(dict(before=before_overlap,after=after_overlap,files=comparisons,
        method="30-140Hz Butterworth order4; mean bass/kick RMS ratio in first70ms after each kick. Diagnostic, not perceptual masking proof.")))
    fixtures=json.loads(Path(".local/fixture-plugins.json").read_text(encoding="utf-8"))
    effect=cli("plugin-allow","--path",fixtures["effect"]["entry"]["path"],"--provenance","Owner authorized online fixture plugins 2026-11-13; exact locked Consolidated bundle")
    cli("plugin-probe","--id",effect["registry_id"],"--sample-rate",48000,"--block-size",256)
    state=cli("plugin-state-capture","--id",effect["registry_id"],"--sample-rate",48000,"--block-size",256)
    insert={k:state[k] for k in ("registry_id","catalog_sha256","state_sha256")}
    insert["parameters"]={"4":0,"12":.47}
    mixed_revision=revise("g1-balance",revised,[
        dict(kind="set_track_gain",track_id="prism",value=-4),
        dict(kind="set_track_gain",track_id="hat",value=-17),
        dict(kind="set_track_gain",track_id="clap",value=-14),
        dict(kind="append_bus_insert",bus_id="drums",insert=insert)],
        "Lead stem RMS was 34dB below bass; raise lead10dB and hats/clap4/3dB for a reviewable balance. Add the proven VST output-gain stage (Dry/Wet0, Output.47) after Faust drum body. Wet algorithm and subjective balance remain unapproved.")
    mixed=cli("project-render","--revision",mixed_revision)
    pre_master=cli("analyze","--rendition",mixed["id"])
    # Temporary production target, recorded here before the measured adjustment.
    target_lufs,peak_ceiling=-16.0,-1.5
    adjustment=min(target_lufs-pre_master["integrated_lufs"],peak_ceiling-pre_master["true_peak"]["dbfs"])
    final_gain=round(mixed["source"]["master"]["gain_db"]+adjustment,3)
    final_revision=revise("g1-master-level",mixed_revision,[dict(kind="set_master_gain",value=final_gain)],
        f"Measured pre-master {pre_master['integrated_lufs']:.3f}LUFS/{pre_master['true_peak']['dbfs']:.3f}dBFS estimated true peak. Transparent gain toward temporary -16LUFS, constrained by -1.5dBFS estimated peak; no limiter required. Profile has additional0.25dB estimator margin.")
    final=cli("project-render","--revision",final_revision)
    quality=cli("analyze","--rendition",final["id"])
    exported=cli("export","--rendition",final["id"],"--path",delivery/"Night-Circuit-G1-review.wav")
    replay=cli("project-render","--revision",final_revision)
    a,rate=sf.read(final["render"]["audio_path"],always_2d=True)
    b,_=sf.read(replay["render"]["audio_path"],always_2d=True)
    delta=np.abs(a-b)
    replay_result=dict(exact_pcm=bool(np.array_equal(a,b)),max_abs_delta=float(delta.max()),rms_delta=float(np.sqrt(np.mean(delta*delta))),
        grade="D1" if np.array_equal(a,b) else "D3",reason="Real native rerender; nondeterministic VST oscillators/state may differ. No portable exact-replay claim.",
        final=final["id"],replay=replay["id"])
    (evidence/"replay.json").write_bytes(canonical(replay_result))
    # Deliberately wrong frame contract; evaluate exact exported bytes.
    bad=analyze_delivery(exported["path"],source["profile"],3600001)
    (evidence/"invalid-export.json").write_bytes(canonical(bad))
    assert bad["status"]=="FAIL" and bad["rules"]["frames"]=="FAIL"
    stale=evidence/"stale-command.json"
    stale.write_bytes(canonical(dict(command_id="g1-stale",base_revision=baseline["revision"],reason="deliberate stale injection",operations=[dict(kind="set_master_gain",value=0)])))
    error=cli("proposal-create","--command",stale,expect=False)
    assert error["code"]=="STALE_REVISION"
    bad_module=evidence/"invalid-module.dsp"
    bad_module.write_text("process = broken syntax !!!;",encoding="utf-8")
    before=cli("project-inspect")
    error=cli("asset-import","--path",bad_module,"--kind","faust","--provenance","deliberate invalid Faust injection",expect=False)
    assert error["code"]=="MODULE_COMPILE_FAILED"
    after=cli("project-inspect")
    assert before==after
    # A failed delivery publication cannot change source or last playable.
    occupied=diagnostics/"occupied.wav"
    occupied.write_bytes(b"intentional failed-export fixture")
    error=cli("export","--rendition",final["id"],"--path",occupied,expect=False)
    assert occupied.read_bytes()==b"intentional failed-export fixture"
    assert cli("project-inspect")==before
    excessive=evidence/"excessive-master-command.json"
    excessive.write_bytes(canonical(dict(command_id="g1-excessive-master",base_revision=final_revision,
        reason="Deliberately out-of-profile preview; never apply",operations=[dict(kind="set_master_gain",value=20)])))
    cli("proposal-create","--command",excessive)
    preview=cli("project-render","--proposal","g1-excessive-master")
    error=cli("export","--rendition",preview["id"],"--path",diagnostics/"must-not-publish.wav",expect=False)
    assert error["code"]=="QUALITY_BLOCKED" and not (diagnostics/"must-not-publish.wav").exists()
    assert cli("project-inspect")==before
    # Actual section/stem evidence, never an AI listening verdict.
    sections=[]
    for section in final["source"]["sections"]:
        lo=tick_sample(section["start_tick"],144,960,rate)
        hi=tick_sample(section["end_tick"],144,960,rate)
        clip=a[lo:hi]
        sections.append({**section,"rms":float(np.sqrt(np.mean(clip*clip))),"lufs":float(pyln.Meter(rate).integrated_loudness(clip))})
    stems=[]
    for name,ref in final["render"]["data"]["stems"].items():
        path=Path(final["render"]["stage"])/ref["file"]
        x,_=sf.read(path)
        stems.append(dict(id=name,sha256=ref["sha256"],rms=float(np.sqrt(np.mean(x*x))),peak=float(np.abs(x).max())))
    calibration=[]
    for freq,phase in [(997,.3),(6000,np.pi/2),(12000,np.pi/4),(18000,.3),(20000,.7)]:
        n=np.arange(rate)
        x=.8*np.sin(2*np.pi*freq*n/rate+phase)
        x[:4800]*=np.linspace(0,1,4800)
        x[-4800:]*=np.linspace(1,0,4800)
        measured=estimated_true_peak(x[:,None])
        calibration.append(dict(frequency=freq,phase=phase,expected_peak=.8,measured_peak=measured,error_db=float(20*np.log10(measured/.8))))
    report=dict(schema="adaw.g1.evidence@1",export=exported,quality=quality,sections=sections,stems=stems,
        baseline_rendition=baseline["id"],final_revision=final_revision,final_rendition=final["id"],replay=replay_result,
        overlap_before=before_overlap,overlap_after=after_overlap,true_peak_calibration=calibration,
        listening="NOT_EVALUATED",owner_brief="Modern electronic808 trap, different structure, swing and moods; listening/demo WAV",
        technical_profile="temporary engineering profile; owner chose use/genre, no loudness threshold",
        limitations=["True peak is calibrated analytic-test FIR estimate, not full EBU conformance", "No subjective listening approval", "No user plugin collection tested", "Native processes are not hardened sandboxes", "G2 conflict merging and G3 portability/recovery remain future work"],
        history=cli("history"))
    (evidence/"report.json").write_bytes(canonical(report))
    print(json.dumps({"report":str((evidence/"report.json").resolve()),"export":exported,"overlap_before":before_overlap,"overlap_after":after_overlap,"replay":replay_result},indent=2))


if __name__ == "__main__":
    main()
