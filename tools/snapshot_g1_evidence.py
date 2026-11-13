"""Retain worker diagnostics and current source identities without altering history."""
import argparse
import json
from pathlib import Path
import shutil
from app.contracts import canonical, file_hash


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--evidence",required=True)
    parser.add_argument("--output",required=True)
    args=parser.parse_args()
    repo=Path(__file__).resolve().parent.parent
    evidence=Path(args.evidence).resolve()
    output=Path(args.output).resolve()
    if output.exists():
        raise RuntimeError("Snapshot exists; choose a new filename")
    stages={}
    def walk(value):
        if isinstance(value,dict):
            if "stage" in value and "job_id" in value:
                stage=Path(value["stage"]).resolve()
                if stage.is_relative_to(repo/".local") and stage.is_dir():
                    stages[value["job_id"]]=stage
            for child in value.values():
                walk(child)
        elif isinstance(value,list):
            for child in value:
                walk(child)
    for path in evidence.rglob("*.json"):
        walk(json.loads(path.read_text(encoding="utf-8-sig")))
    logs=evidence/"worker-logs"
    logs.mkdir(exist_ok=True)
    log_manifest={}
    for job,stage in stages.items():
        for name in ("stdout.log","stderr.log"):
            source=stage/name
            if source.exists():
                destination=logs/(job+"-"+name)
                if destination.exists():
                    assert file_hash(destination)==file_hash(source)
                else:
                    shutil.copyfile(source,destination)
                log_manifest[destination.relative_to(repo).as_posix()]=file_hash(destination)
    files=[repo/p for p in ("AGENTS.md","README.md","pyproject.toml","requirements.lock",".gitattributes",".gitignore")]
    for folder in ("app","tests","tools","fixtures","docs/decisions"):
        files.extend(p for p in (repo/folder).rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    original=json.loads((repo/"docs/spec/v0.4/FILE-MANIFEST.json").read_bytes())
    for entry in original["files"]:
        path=repo/"docs/spec/v0.4"/entry["path"]
        assert path.stat().st_size==entry["size_bytes"] and file_hash(path)==entry["sha256"]
    output.write_bytes(canonical({"scope":"Final implementation and retained diagnostics at G1 handoff; historical run source is in each rendition's graph/source, not rewritten",
        "source_files":{p.relative_to(repo).as_posix():file_hash(p) for p in sorted(files)},
        "worker_logs":log_manifest,"original_spec_files_verified":len(original["files"])}))
    print(json.dumps({"snapshot":str(output),"source_files":len(files),"worker_logs":len(log_manifest),"spec_files":len(original["files"])}))


if __name__=="__main__":
    main()
