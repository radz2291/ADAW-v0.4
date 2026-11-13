"""Read-only verification of G1 source, native output, delivery and failure evidence."""
import argparse
import json
from pathlib import Path
import numpy as np
import soundfile as sf

from app.arrangement import compile_graph
from app.contracts import canonical, digest, file_hash
from app.quality import analyze


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("run")
    args=parser.parse_args()
    directory=Path(args.run)
    report=json.loads((directory/"report.json").read_bytes())
    renditions=[]
    jobs=set()
    for path in sorted(directory.glob("*.json")):
        envelope=json.loads(path.read_bytes())
        if not isinstance(envelope,dict):
            continue
        data=envelope.get("data")
        if not isinstance(data,dict) or "graph" not in data or "render" not in data:
            continue
        render=data["render"]
        if render["job_id"] in jobs:
            continue
        jobs.add(render["job_id"])
        stage=Path(render["stage"])
        content=stage.parent.parent/"content"
        def read_content(sha):
            assert file_hash(content/sha)==sha
            return (content/sha).read_bytes()
        graph,_=compile_graph(data["source"],read_content)
        assert graph==data["graph"],path
        assert digest(canonical(graph))==render["source_sha256"]==data["manifest"]["graph_sha256"],path
        assert digest(canonical(data["source"]))==data["manifest"]["source_sha256"],path
        assert digest(canonical(data["source"]["profile"]))==data["manifest"]["profile_sha256"],path
        audio,rate=sf.read(stage/"output.wav",always_2d=True,dtype="float32")
        assert audio.shape==(graph["frames"],2) and rate==graph["sample_rate"] and np.isfinite(audio).all()
        audio_hash=file_hash(stage/"output.wav")
        assert audio_hash==render["data"]["audio_sha256"]==render["quality"]["audio_sha256"]
        assert digest(audio.astype("<f4").tobytes())==render["data"]["pcm_sha256"]
        assert file_hash(content/audio_hash)==audio_hash
        for node_id,node in render["data"]["nodes"].items():
            if "state_sha256" in node:
                assert file_hash(stage/(node_id+".state"))==node["state_sha256"]
        for node_id,stem in render["data"]["stems"].items():
            assert file_hash(stage/(node_id+".wav"))==stem["sha256"]
            stem_audio,stem_rate=sf.read(stage/(node_id+".wav"),always_2d=True)
            assert stem_audio.shape==audio.shape and stem_rate==rate and np.isfinite(stem_audio).all()
        request=json.loads((stage/"request.json").read_bytes())
        for plugin in request["plugins"].values():
            from app.service import binary_identity
            assert binary_identity(plugin["path"])["sha256"]==plugin["sha256"]
        assert (stage/"stderr.log").exists() and (stage/"stdout.log").exists()
        renditions.append(dict(id=data["id"],audio_sha256=audio_hash,source_sha256=data["manifest"]["source_sha256"],frames=len(audio)))
    export=report["export"]
    baseline=json.loads((directory/"baseline.json").read_bytes())["data"]["source"]
    final_sources=[json.loads(p.read_bytes()).get("data",{}) for p in directory.glob("*-project-render.json")]
    final_source=next(r["source"] for r in final_sources if r.get("id")==report["final_rendition"])
    for track in baseline["tracks"]:
        if track["protected"]:
            actual=next(t for t in final_source["tracks"] if t["id"]==track["id"])
            assert actual["events"]==track["events"], "Protected musical events changed"
    assert file_hash(export["path"])==export["audio_sha256"]==export["quality"]["audio_sha256"]
    measured=analyze(export["path"])
    assert measured["subtype"]=="PCM_24" and measured["frames"]==3600000 and measured["channels"]==2
    assert abs(measured["integrated_lufs"]-export["quality"]["integrated_lufs"])<1e-8
    assert export["quality"]["status"]=="PASS" and all(v=="PASS" for v in export["quality"]["rules"].values())
    assert export["listening"]=="NOT_EVALUATED"
    comparison=json.loads((directory/"kick-bass-comparison.json").read_bytes())
    for clip in comparison["files"]:
        assert file_hash(clip["path"])==clip["sha256"] and abs(clip["measured_lufs"]+23)<1e-5
    assert report["overlap_after"]["first_drop"]["mean_bass_to_kick_rms_first_70ms"] < report["overlap_before"]["first_drop"]["mean_bass_to_kick_rms_first_70ms"]
    assert all(abs(c["error_db"])<.12 for c in report["true_peak_calibration"])
    errors=[]
    trace=json.loads((directory/"trace.json").read_bytes())
    for call in trace:
        result=json.loads((directory/call["result_file"]).read_bytes())
        assert result["ok"]==(call["exit_code"]==0)
        if not result["ok"]:
            errors.append(result["error"]["code"])
    assert {"STALE_REVISION","MODULE_COMPILE_FAILED","QUALITY_BLOCKED","VALIDATION_ERROR"}<=set(errors)
    print(json.dumps(dict(status="PASS",verified_renditions=renditions,export_sha256=export["audio_sha256"],
        errors_exercised=errors,report_sha256=file_hash(directory/"report.json"),listening="NOT_EVALUATED",
        scope="Independent source/file/PCM/state/stem/dependency/measurement identities; no subjective sound judgment"),indent=2))


if __name__=="__main__":
    main()
