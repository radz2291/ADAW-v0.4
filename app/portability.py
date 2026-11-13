"""Windows project backup and restore using verified, streamed ADAW archives."""

import argparse
from contextlib import closing
from hashlib import sha256
import json
from pathlib import Path
import re
import shutil
import sqlite3
import tempfile
import zipfile

from app.contracts import canonical, file_hash, require
from app.arrangement import validate
from app.errors import AdawError
from app.project import ProjectService
from app.service import binary_identity

SCHEMA = "adaw.project-package@1"
MEMBER = re.compile(r"project\.sqlite|content/[0-9a-f]{64}")
MAX_MANIFEST_BYTES = 8 * 1024 * 1024


def verify_source_content(project, source):
    validate(source)
    refs = set()
    for track in source["tracks"]:
        instrument = track["instrument"]
        refs.update(instrument[key] for key in ("asset_sha256", "module_sha256", "state_sha256")
                    if key in instrument)
    for entity in [*source["tracks"], *source["buses"], source["master"]]:
        for insert in entity["inserts"]:
            refs.add(insert.get("module_sha256") or insert["state_sha256"])
    for identity in refs:
        project.read_content(identity)


def backup(project, destination):
    destination = Path(destination).resolve()
    require(not destination.is_relative_to(project.root), "Store the archive outside its project")
    require(not destination.exists(), "Archive destination already exists")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as temp:
        temp = Path(temp)
        database = temp / "project.sqlite"
        with closing(project.connect()) as source, closing(sqlite3.connect(database)) as target:
            source.backup(target)
            with target:
                for ident, encoded in target.execute("SELECT id,identity FROM plugins").fetchall():
                    identity = json.loads(encoded)
                    identity["path"] = None
                    target.execute("UPDATE plugins SET identity=? WHERE id=?", (canonical(identity), ident))
                target.execute("UPDATE jobs SET status='interrupted' WHERE status='running'")
        paths = {"project.sqlite": database}
        paths.update({f"content/{p.name}": p for p in project.content.iterdir()
                      if p.is_file() and re.fullmatch(r"[0-9a-f]{64}", p.name)})
        manifest = {}
        package = temp / "archive.tmp"
        with zipfile.ZipFile(package, "w", zipfile.ZIP_DEFLATED, compresslevel=1) as archive:
            for name, path in paths.items():
                checksum = sha256()
                size = 0
                with path.open("rb") as source, archive.open(name, "w", force_zip64=True) as target:
                    while block := source.read(1024 * 1024):
                        checksum.update(block)
                        size += len(block)
                        target.write(block)
                value = checksum.hexdigest()
                require(name == "project.sqlite" or name.split("/")[1] == value, "Corrupt content in project")
                manifest[name] = {"sha256": value, "size": size}
            payload = canonical({"schema": SCHEMA, "files": manifest})
            require(len(payload) <= MAX_MANIFEST_BYTES, "Project manifest exceeds package limit")
            archive.writestr("manifest.json", payload)
        checksum = file_hash(package)
        package.rename(destination)
    return {"path": str(destination), "sha256": checksum, "files": len(manifest)}


def restore(package, destination, approved_plugins=()):
    destination = Path(destination).resolve()
    require(not destination.exists(), "Restore requires a fresh project directory")
    destination.parent.mkdir(parents=True, exist_ok=True)
    bindings = {}
    for path in approved_plugins:
        identity = binary_identity(path)
        bindings[identity["sha256"]] = identity
    with zipfile.ZipFile(package) as archive, tempfile.TemporaryDirectory(dir=destination.parent) as temp:
        names = archive.namelist()
        require(len(names) == len(set(names)) and "manifest.json" in names, "Invalid package inventory")
        require(archive.getinfo("manifest.json").file_size <= MAX_MANIFEST_BYTES, "Oversized package manifest")
        manifest = json.loads(archive.read("manifest.json"))
        require(manifest.get("schema") == SCHEMA, "Unsupported package schema")
        files = manifest.get("files")
        require(isinstance(files, dict) and set(files) == set(names) - {"manifest.json"}
                and "project.sqlite" in files, "Package inventory differs from manifest")
        root = Path(temp) / "project"
        (root / "content").mkdir(parents=True)
        required_space = sum(archive.getinfo(name).file_size for name in files)
        require(required_space <= shutil.disk_usage(root).free, "Insufficient free space to restore")
        for name, entry in files.items():
            require(MEMBER.fullmatch(name) and isinstance(entry, dict)
                    and archive.getinfo(name).file_size == entry.get("size"), "Invalid package member")
            checksum = sha256()
            with archive.open(name) as source, (root / name).open("xb") as target:
                while block := source.read(1024 * 1024):
                    checksum.update(block)
                    target.write(block)
            value = checksum.hexdigest()
            require(value == entry.get("sha256") and (name == "project.sqlite" or value == name.split("/")[1]),
                    "Package checksum mismatch")
        missing = []
        with closing(sqlite3.connect(root / "project.sqlite")) as db, db:
            db.execute("PRAGMA trusted_schema=OFF")
            require(db.execute("PRAGMA quick_check").fetchone() == ("ok",), "Invalid project database")
            require(db.execute("SELECT count(*) FROM sqlite_schema WHERE type IN ('trigger','view')").fetchone()[0] == 0,
                    "Unexpected database objects")
            for ident, encoded in db.execute("SELECT id,identity FROM plugins").fetchall():
                identity = json.loads(encoded)
                match = bindings.get(identity["sha256"])
                require(ident == "plugin-" + identity["sha256"], "Invalid registry identity")
                if match is None or match["files"] != identity["files"]:
                    missing.append(ident)
                    identity["path"] = None
                else:
                    identity["path"] = match["path"]
                db.execute("UPDATE plugins SET identity=? WHERE id=?", (canonical(identity), ident))
            db.execute("UPDATE jobs SET status='interrupted' WHERE status='running'")
        # Read source through the project service before exposing the directory.
        project = ProjectService(root)
        revision, source = project.source()
        for record in project.history()["revisions"]:
            verify_source_content(project, project.source(record["id"])[1])
        if not missing:
            project.validate_dependencies(source)
        root.rename(destination)
    return {"root": str(destination), "revision": revision, "missing_plugins": missing}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="operation", required=True)
    pack = commands.add_parser("backup")
    pack.add_argument("--root", required=True)
    pack.add_argument("--archive", required=True)
    unpack = commands.add_parser("restore")
    unpack.add_argument("--archive", required=True)
    unpack.add_argument("--root", required=True)
    unpack.add_argument("--allow-plugin", action="append", default=[])
    reconcile = commands.add_parser("reconcile")
    reconcile.add_argument("--root", required=True)
    args = parser.parse_args()
    try:
        if args.operation == "backup":
            result = backup(ProjectService(args.root), args.archive)
        elif args.operation == "restore":
            result = restore(args.archive, args.root, args.allow_plugin)
        else:
            result = ProjectService(args.root).reconcile_jobs()
        print(json.dumps({"ok": True, "data": result}))
        return 0
    except (AdawError, OSError, ValueError, KeyError, TypeError, sqlite3.DatabaseError, zipfile.BadZipFile) as exc:
        print(json.dumps({"ok": False, "error": {"code": getattr(exc, "code", "INVALID_PACKAGE"), "message": str(exc)}}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
