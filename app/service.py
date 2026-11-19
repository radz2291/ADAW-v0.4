"""Only this service persists project truth. Workers receive staged snapshots.

SQLite atomically binds a successful render's source, audio and last-playable head.
Content files are immutable, published before the transaction; orphans are harmless.
G0 commits are explicit fixture commits, not the future proposal/approval API.
"""
from contextlib import closing
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import time
import uuid

from app.contracts import RenderGraph, canonical, catalog_hash, digest, file_hash
from app.errors import AdawError
from app.job_leases import job_lease
from app.quality import analyze

REPO = Path(__file__).resolve().parent.parent


def binary_identity(path):
    path = Path(path).resolve()
    if not path.exists():
        raise AdawError("PLUGIN_MISSING", "Plugin dependency missing", path=str(path))
    if path.is_dir():
        files = {f.relative_to(path).as_posix(): file_hash(f) for f in sorted(path.rglob("*")) if f.is_file()}
    else:
        files = {path.name: file_hash(path)}
    return {"path": str(path), "files": files, "sha256": digest(canonical(files))}


class Service:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.content = self.root / "content"
        self.content.mkdir(exist_ok=True)
        self.staging = self.root / "staging"
        self.staging.mkdir(exist_ok=True)
        self.db_path = self.root / "project.sqlite"
        with closing(self.connect()) as db, db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS revisions (id TEXT PRIMARY KEY, parent TEXT, source BLOB NOT NULL, audio TEXT NOT NULL, report BLOB NOT NULL);
                CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, status TEXT NOT NULL, result BLOB);
                CREATE TABLE IF NOT EXISTS plugins (id TEXT PRIMARY KEY, identity BLOB NOT NULL, provenance TEXT NOT NULL, probe BLOB);
            ''')

    def connect(self):
        db = sqlite3.connect(self.db_path)
        db.execute("PRAGMA trusted_schema=OFF")
        return db

    def inspect(self):
        with closing(self.connect()) as db:
            meta = dict(db.execute("SELECT key,value FROM metadata"))
            revisions = [{"id": r[0], "parent": r[1], "audio_sha256": r[2]} for r in db.execute("SELECT id,parent,audio FROM revisions ORDER BY rowid")]
        return {"head": meta.get("head"), "last_playable": meta.get("last_playable"), "revisions": revisions}

    def put(self, data):
        sha = digest(data)
        dest = self.content / sha
        if dest.exists():
            if file_hash(dest) != sha:
                raise AdawError("VALIDATION_ERROR", "Corrupt content-addressed file", sha256=sha)
            return sha
        temp = self.content / ("tmp-" + uuid.uuid4().hex)
        with temp.open("xb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, dest)
        return sha

    def authorize_plugin(self, path, provenance):
        if not provenance.strip():
            raise AdawError("PLUGIN_UNAPPROVED", "Explicit approval provenance required")
        identity = binary_identity(path)
        registry_id = "plugin-" + identity["sha256"]
        with closing(self.connect()) as db, db:
            db.execute("INSERT OR IGNORE INTO plugins VALUES (?,?,?,NULL)", (registry_id, canonical(identity), provenance))
            row = db.execute("SELECT identity FROM plugins WHERE id=?", (registry_id,)).fetchone()
            if json.loads(row[0]).get("path") is None:
                db.execute("UPDATE plugins SET identity=?,provenance=? WHERE id=?",
                           (canonical(identity), provenance, registry_id))
        return {"registry_id": registry_id, **identity, "provenance": provenance}

    def plugin(self, registry_id):
        with closing(self.connect()) as db:
            row = db.execute("SELECT identity,provenance,probe FROM plugins WHERE id=?", (registry_id,)).fetchone()
        if row is None:
            raise AdawError("PLUGIN_UNAPPROVED", "Plugin is not authorized", registry_id=registry_id)
        identity = json.loads(row[0])
        if identity.get("path") is None:
            raise AdawError("PLUGIN_MISSING", "Resolve and explicitly authorize the archived plugin", registry_id=registry_id)
        if binary_identity(identity["path"])["sha256"] != identity["sha256"]:
            raise AdawError("PLUGIN_CAPABILITY_UNVERIFIED", "Plugin files changed; reauthorize and probe")
        with closing(self.connect()) as db:
            policy = db.execute("SELECT value FROM metadata WHERE key=?", ("host-profile:"+registry_id,)).fetchone()
        return {**identity, "provenance": row[1], "probe": json.loads(row[2]) if row[2] else None,
                "host_profile": json.loads(policy[0])["profile"] if policy else "standard"}

    def configure_plugin_host(self, registry_id, profile, reason):
        if profile not in ("standard", "windows-stereo-zero-aux-isolated-v1") or not reason.strip():
            raise AdawError("VALIDATION_ERROR", "Known host profile and explicit reason required")
        if profile != "standard" and os.name != "nt":
            raise AdawError("VALIDATION_ERROR", "This compatibility profile requires Windows")
        identity = self.plugin(registry_id)  # Rechecks exact approved fingerprint.
        record = {"profile": profile, "reason": reason, "binary_sha256": identity["sha256"]}
        with closing(self.connect()) as db, db:
            db.execute("INSERT OR REPLACE INTO metadata VALUES (?,?)", ("host-profile:"+registry_id, canonical(record)))
            # I/O and host semantics changed; old probe must not be reused.
            db.execute("UPDATE plugins SET probe=NULL WHERE id=?", (registry_id,))
        return {"registry_id": registry_id, **record}

    def run_worker(self, request, timeout, staged_states=(), staged_assets=()):
        if not isinstance(timeout, (int, float)) or not 0 < timeout < float("inf"):
            raise AdawError("VALIDATION_ERROR", "Timeout must be finite and positive")
        job = uuid.uuid4().hex
        stage = self.staging / job
        stage.mkdir()
        for sha in staged_assets:
            source = self.content / sha
            if not source.exists() or file_hash(source) != sha:
                raise AdawError("ASSET_MISSING", "Missing/corrupt audio asset", sha256=sha)
            shutil.copyfile(source, stage / (sha + ".wav"))
        for sha in staged_states:
            source = self.content / sha
            if not source.exists() or file_hash(source) != sha:
                raise AdawError("VALIDATION_ERROR", "Missing/corrupt plugin state", sha256=sha)
            shutil.copyfile(source, stage / (sha + ".state"))
        (stage / "request.json").write_bytes(canonical(request))
        with job_lease(stage / "service.lease") as locked:
            if not locked:
                raise AdawError("CONFLICT", "Worker lease is already held")
            return self._run_job(stage, job, timeout)

    def _run_job(self, stage, job, timeout):
        with closing(self.connect()) as db, db:
            db.execute("INSERT INTO jobs VALUES (?, 'running', NULL)", (job,))
        start = time.perf_counter()
        result = None
        with (stage / "stdout.log").open("wb") as out, (stage / "stderr.log").open("wb") as err:
            process = subprocess.Popen([sys.executable, "-m", "app.worker", str(stage / "request.json")],
                cwd=REPO, stdout=out, stderr=err, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            try:
                code = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                code = process.returncode
                result = {"ok": False, "error": {"code": "TIMEOUT", "message": "Worker exceeded explicit deadline"}}
        if result is None:
            if not (stage / "result.json").exists():
                result = {"ok": False, "error": {"code": "WORKER_CRASHED", "message": "Worker exited without result"}}
            else:
                result = json.loads((stage / "result.json").read_text(encoding="utf-8"))
                if code != 0 and result.get("ok"):
                    result = {"ok": False, "error": {"code": "WORKER_CRASHED", "message": "Nonzero worker exit"}}
        result.update(job_id=job, stage=str(stage), exit_code=code, wall_seconds=time.perf_counter() - start)
        with closing(self.connect()) as db, db:
            db.execute("UPDATE jobs SET status=?,result=? WHERE id=?", ("succeeded" if result["ok"] else "failed", canonical(result), job))
        if not result["ok"]:
            error = result["error"]
            raise AdawError(error["code"], error["message"], job_id=job, stage=str(stage), worker=result)
        return result

    def reconcile_jobs(self):
        """Only the process that owns a job may promote its worker result."""
        with closing(self.connect()) as db:
            jobs = [row[0] for row in db.execute("SELECT id FROM jobs WHERE status='running'")]
        interrupted, active, untracked = [], [], []
        for job in jobs:
            if len(job) != 32 or any(ch not in "0123456789abcdef" for ch in job):
                untracked.append(job)
                continue
            lease = self.staging / job / "service.lease"
            if not lease.is_file():
                untracked.append(job)
                continue
            with job_lease(lease) as locked:
                if not locked:
                    active.append(job)
                    continue
                result = {"ok": False, "job_id": job, "error": {
                    "code": "SERVICE_INTERRUPTED", "message": "Worker owner exited before publishing a result"}}
                with closing(self.connect()) as db, db:
                    changed = db.execute("UPDATE jobs SET status='interrupted',result=? WHERE id=? AND status='running'",
                                         (canonical(result), job)).rowcount
                if changed:
                    interrupted.append(job)
        return {"interrupted": interrupted, "active": active, "untracked": untracked}

    def probe_plugin(self, registry_id, sample_rate, block_size, timeout):
        if type(sample_rate) is not int or type(block_size) is not int or sample_rate <= 0 or block_size <= 0:
            raise AdawError("VALIDATION_ERROR", "Rate/block size must be positive integers")
        identity = self.plugin(registry_id)
        result = self.run_worker({"operation": "probe", "plugin_path": identity["path"], "sample_rate": sample_rate, "block_size": block_size,
                                  "host_profile": identity["host_profile"]}, timeout)
        with closing(self.connect()) as db, db:
            db.execute("UPDATE plugins SET probe=? WHERE id=?", (canonical(result["data"]), registry_id))
        return result

    def render(self, graph, timeout, commit=False, base_revision=None, record_nodes=(), benchmark=True):
        graph = RenderGraph.parse(graph)
        before = self.inspect()
        if commit and base_revision != before["head"]:
            raise AdawError("STALE_REVISION", "Explicit base revision does not match head")
        plugins, states, assets = {}, set(), set()
        for node in graph.value["nodes"]:
            if node["kind"] == "samples":
                assets.update(e["asset_sha256"] for e in node["config"]["events"])
            if node["kind"] != "vst":
                continue
            c = node["config"]
            identity = self.plugin(c["registry_id"])
            if identity["probe"] is None:
                raise AdawError("PLUGIN_CAPABILITY_UNVERIFIED", "Plugin needs isolated probe")
            plugins[c["registry_id"]] = {"path": identity["path"], "sha256": identity["sha256"],
                "catalog_sha256": catalog_hash(identity["probe"]["parameters"]), "host_profile": identity["host_profile"]}
            if c["state_sha256"]:
                states.add(c["state_sha256"])
        if not set(record_nodes) <= {n["id"] for n in graph.value["nodes"]}:
            raise AdawError("VALIDATION_ERROR", "Unknown stem node")
        result = self.run_worker({"operation": "render", "graph": graph.value, "plugins": plugins,
            "record_nodes": list(record_nodes), "benchmark": benchmark}, timeout, states, assets)
        stage = Path(result["stage"])
        data = result["data"]
        audio = stage / "output.wav"
        if file_hash(audio) != data["audio_sha256"]:
            raise AdawError("INVALID_EXPORT", "Worker audio hash mismatch")
        quality = analyze(audio)
        if (quality["frames"], quality["sample_rate"], quality["channels"]) != (graph.value["frames"], graph.value["sample_rate"], graph.value["nodes"][-1]["channels"]):
            raise AdawError("INVALID_EXPORT", "Decoded audio differs from graph contract")
        audio_sha = self.put(audio.read_bytes())
        for node_id, stem in data.get("stems", {}).items():
            if node_id not in record_nodes:
                raise AdawError("INVALID_EXPORT", "Unexpected stem")
            path = stage / (node_id + ".wav")
            if file_hash(path) != stem["sha256"]:
                raise AdawError("INVALID_EXPORT", "Stem hash mismatch")
            self.put(path.read_bytes())
        for node_id, report in data["nodes"].items():
            if "state_file" in report:
                # Derive path from validated node ID, never trust worker-supplied path.
                state = (stage / (node_id + ".state")).read_bytes()
                if digest(state) != report["state_sha256"]:
                    raise AdawError("INVALID_EXPORT", "Worker state hash mismatch")
                self.put(state)
        result.update(source_sha256=graph.sha256, quality=quality, audio_path=str(audio), committed=commit)
        if commit:
            # Single serialized transaction; recheck after potentially long render.
            with closing(self.connect()) as db, db:
                db.execute("BEGIN IMMEDIATE")
                row = db.execute("SELECT value FROM metadata WHERE key='head'").fetchone()
                actual = row[0] if row else None
                if actual != base_revision:
                    raise AdawError("STALE_REVISION", "Head changed while rendering")
                revision = uuid.uuid4().hex
                db.execute("INSERT INTO revisions VALUES (?,?,?,?,?)", (revision, actual, graph.source, audio_sha, canonical(result)))
                db.execute("INSERT OR REPLACE INTO metadata VALUES ('head',?)", (revision,))
                db.execute("INSERT OR REPLACE INTO metadata VALUES ('last_playable',?)", (audio_sha,))
                result["revision"] = revision
        return result

