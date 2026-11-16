"""Capture an exact candidate tree fingerprint without changing the Git index."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

paths=subprocess.check_output(["git","ls-files","-c","-o","--exclude-standard","app","apps","tests","requirements.lock","docs/evaluation/EVERYDAY-INTERACTION-v1.md"],text=True).splitlines()
files={path:hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in sorted(set(paths)) if Path(path).is_file()}
report={"commit":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),"tree_sha256":hashlib.sha256(json.dumps(files,sort_keys=True,separators=(",",":")).encode()).hexdigest(),"files":files}
Path(sys.argv[1]).parent.mkdir(parents=True,exist_ok=True)
Path(sys.argv[1]).write_text(json.dumps(report,indent=2))
print(report["tree_sha256"])
