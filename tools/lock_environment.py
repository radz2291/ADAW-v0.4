"""Generate exact target-wheel hashes from the downloaded environment wheels."""
import json
from pathlib import Path
import zipfile
from email.parser import Parser
from app.contracts import file_hash


def main():
    entries = []
    for path in sorted(Path(".local/wheels").glob("*.whl")):
        with zipfile.ZipFile(path) as archive:
            metadata = next(n for n in archive.namelist() if n.endswith(".dist-info/METADATA"))
            meta = Parser().parsestr(archive.read(metadata).decode())
        entries.append({"name": meta["Name"], "version": meta["Version"], "wheel": path.name,
                        "sha256": file_hash(path)})
    Path("requirements.lock").write_text("# Windows x64 CPython 3.12.14; exact tested wheels\n" +
        "\n".join(f"{e['name']}=={e['version']} --hash=sha256:{e['sha256']}" for e in entries) + "\n", encoding="utf-8")
    Path("evidence/gates/g0/dependency-wheels.json").write_text(json.dumps(entries, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

