"""Fetch locked, user-authorized test fixtures into ignored local storage.

Never loads binaries, invokes an installer, scans machine folders, or changes PATH.
"""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request
import zipfile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-test-downloads", action="store_true", required=True,
                        help="Explicitly authorize these named test-fixture downloads")
    parser.parse_args()
    lock = json.loads(Path("fixtures/downloads.lock.json").read_text())
    for entry in lock:
        target = Path(entry["local_path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            with urllib.request.urlopen(entry["url"], timeout=60) as response:
                data = response.read()
            if hashlib.sha256(data).hexdigest() != entry["sha256"]:
                raise RuntimeError("Download changed: " + entry["url"])
            target.write_bytes(data)
        if hashlib.sha256(target.read_bytes()).hexdigest() != entry["sha256"]:
            raise RuntimeError("Local fixture hash differs: " + str(target))
        if "extract" in entry:
            with zipfile.ZipFile(target) as archive:
                for selection in entry["extract"]:
                    matched = False
                    for name in archive.namelist():
                        if name.endswith("/"):
                            continue
                        if name == selection["member"] or name.startswith(selection["member"].rstrip("/") + "/"):
                            matched = True
                            rel = name[len(selection["member"]):].lstrip("/")
                            dest = Path(selection["destination"])
                            if rel:
                                dest = dest / rel
                            # Reject malicious archive names rather than trusting a remote ZIP.
                            root = Path(".local/plugins").resolve()
                            if not dest.resolve().is_relative_to(root):
                                raise RuntimeError("Archive path escapes fixture directory")
                            dest.parent.mkdir(parents=True, exist_ok=True)
                            dest.write_bytes(archive.read(name))
                    if not matched:
                        raise RuntimeError("Archive layout changed: " + selection["member"])
        print("VERIFIED", target)
    Path(".local/calibration/upstream-commit.txt").write_text("b8d67bfd3ce5deef872f688fcfa491a0ca69fddd\n")


if __name__ == "__main__":
    main()

