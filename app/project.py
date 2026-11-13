"""G1 authoritative service: validated imports, proposals, revisions and renditions."""
from contextlib import closing
import io
import json
import os
from pathlib import Path
import uuid

from app.arrangement import validate, compile_graph, sha
from app.contracts import canonical, catalog_hash, digest, fields, file_hash, number, require
from app.errors import AdawError
from app.service import Service
from app.quality import analyze_delivery


class ProjectService(Service):
    def __init__(self, root):
        super().__init__(root)
        with closing(self.connect()) as db, db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS g1_imports (hash TEXT PRIMARY KEY, kind TEXT NOT NULL, provenance TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS g1_states (hash TEXT NOT NULL, plugin TEXT NOT NULL, catalog TEXT NOT NULL, PRIMARY KEY(hash,plugin,catalog));
                CREATE TABLE IF NOT EXISTS g1_revisions (id TEXT PRIMARY KEY, parent TEXT, source BLOB NOT NULL, reason TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS g1_proposals (id TEXT PRIMARY KEY, payload BLOB NOT NULL, source BLOB NOT NULL, applied TEXT);
                CREATE TABLE IF NOT EXISTS g1_renditions (id TEXT PRIMARY KEY, revision TEXT NOT NULL, report BLOB NOT NULL);
                CREATE TABLE IF NOT EXISTS g1_exports (id TEXT PRIMARY KEY, rendition TEXT NOT NULL, report BLOB NOT NULL);
            ''')

    def read_content(self, content_hash):
        sha(content_hash)
        path = self.content / content_hash
        if not path.is_file() or file_hash(path) != content_hash:
            raise AdawError("ASSET_MISSING", "Missing or corrupt content", sha256=content_hash)
        return path.read_bytes()

    def import_file(self, path, kind, provenance, timeout):
        require(kind in ("audio", "faust"), "Import supports WAV or Faust")
        require(isinstance(provenance, str) and provenance.strip(), "Import provenance required")
        data = Path(path).resolve().read_bytes()
        if kind == "audio":
            import numpy as np
            import soundfile as sf
            audio, rate = sf.read(io.BytesIO(data), always_2d=True)
            require(sf.info(io.BytesIO(data)).format == "WAV" and len(audio) and audio.shape[1] in (1, 2) and np.isfinite(audio).all(), "Invalid WAV asset")
            details = {"frames": len(audio), "sample_rate": rate, "channels": audio.shape[1]}
        else:
            # Compilation is isolated and must succeed before publication.
            details = self.run_worker({"operation": "module_validate", "source": data.decode("utf-8"),
                                      "sample_rate": 48000, "block_size": 256}, timeout)["data"]
        content_hash = self.put(data)
        with closing(self.connect()) as db, db:
            db.execute("INSERT OR IGNORE INTO g1_imports VALUES (?,?,?)", (content_hash, kind, provenance))
        return {"sha256": content_hash, "kind": kind, "provenance": provenance, "validation": details}

    def capture_plugin_state(self, registry_id, timeout, sample_rate, block_size):
        identity = self.plugin(registry_id)
        if not identity["probe"]:
            raise AdawError("PLUGIN_CAPABILITY_UNVERIFIED", "Probe before capturing state")
        require(identity["probe"]["inputs"] in (0, 2) and identity["probe"]["outputs"] == 2, "G1 state initialization supports stereo instrument/effect")
        graph = {"schema": "adaw.g0.graph@1", "sample_rate": sample_rate, "block_size": block_size,
                 "frames": sample_rate, "output": "instrument", "nodes": [{"id": "instrument", "kind": "vst", "inputs": [], "channels": 2,
                 "config": {"registry_id": registry_id, "parameters": {}, "midi": [], "automation": {}, "state_sha256": None}}]}
        if identity["probe"]["inputs"] == 2:
            graph["nodes"][0]["inputs"] = ["tone"]
            graph["nodes"].insert(0, {"id": "tone", "kind": "tone", "inputs": [], "channels": 2,
                                     "config": {"frequency_hz": 440, "amplitude": .1, "onset_frame": 0}})
        result = self.render(graph, timeout, benchmark=False)
        state = result["data"]["nodes"]["instrument"]["state_sha256"]
        catalog = catalog_hash(identity["probe"]["parameters"])
        with closing(self.connect()) as db, db:
            db.execute("INSERT OR IGNORE INTO g1_states VALUES (?,?,?)", (state, registry_id, catalog))
        return {"state_sha256": state, "registry_id": registry_id, "catalog_sha256": catalog, "job_id": result["job_id"]}

    def validate_dependencies(self, source):
        validate(source)
        references = []
        with closing(self.connect()) as db:
            def check_plugin(inst):
                identity = self.plugin(inst["registry_id"])
                if not identity["probe"] or catalog_hash(identity["probe"]["parameters"]) != inst["catalog_sha256"]:
                    raise AdawError("PLUGIN_CAPABILITY_UNVERIFIED", "Source catalog binding changed")
                if not db.execute("SELECT 1 FROM g1_states WHERE hash=? AND plugin=? AND catalog=?", (inst["state_sha256"], inst["registry_id"], inst["catalog_sha256"])).fetchone():
                    raise AdawError("PLUGIN_CAPABILITY_UNVERIFIED", "State is not bound to this plugin/catalog")
                self.read_content(inst["state_sha256"])
            for t in source["tracks"]:
                inst = t["instrument"]
                if t["kind"] == "samples":
                    references.append((inst["asset_sha256"], "audio"))
                    import soundfile as sf
                    info = sf.info(io.BytesIO(self.read_content(inst["asset_sha256"])))
                    require(info.samplerate == source["sample_rate"] and info.channels in (1, 2), "Sample rate/channels must match source; no implicit resampling")
                elif t["kind"] == "faust_synth":
                    references.append((inst["module_sha256"], "faust"))
                else:
                    check_plugin(inst)
            for entity in [*source["tracks"], *source["buses"], source["master"]]:
                for i in entity["inserts"]:
                    if "registry_id" in i:
                        check_plugin(i)
                    else:
                        references.append((i["module_sha256"], "faust"))
            for content_hash, kind in references:
                if not db.execute("SELECT 1 FROM g1_imports WHERE hash=? AND kind=?", (content_hash, kind)).fetchone():
                    raise AdawError("ASSET_MISSING", "Reference has no validated import", sha256=content_hash)
                self.read_content(content_hash)
        # Validate event/sample bounds and generated graph before changing head.
        compile_graph(source, self.read_content)

    def head(self, db):
        row = db.execute("SELECT value FROM metadata WHERE key='g1_head'").fetchone()
        return row[0] if row else None

    def create(self, source):
        self.validate_dependencies(source)
        revision = "rev-" + digest(canonical(source))
        with closing(self.connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            require(self.head(db) is None, "Project already exists")
            db.execute("INSERT INTO g1_revisions VALUES (?,?,?,?)", (revision, None, canonical(source), "Initial composition"))
            db.execute("INSERT INTO metadata VALUES ('g1_head',?)", (revision,))
        return {"revision": revision, "source_sha256": digest(canonical(source)), "listening": "NOT_EVALUATED"}

    def source(self, revision=None):
        with closing(self.connect()) as db:
            revision = revision or self.head(db)
            row = db.execute("SELECT source FROM g1_revisions WHERE id=?", (revision,)).fetchone()
        if not row:
            raise AdawError("NOT_FOUND", "Revision not found", revision=revision)
        return revision, json.loads(row[0])

    def project_inspect(self):
        revision, source = self.source()
        with closing(self.connect()) as db:
            last = db.execute("SELECT value FROM metadata WHERE key='g1_last_playable'").fetchone()
        return {"revision": revision, "source_sha256": digest(canonical(source)), "source": source,
                "last_playable_rendition": last[0] if last else None, "listening": "NOT_EVALUATED"}

    def history(self):
        with closing(self.connect()) as db:
            return {"revisions": [{"id": r[0], "parent": r[1], "reason": r[2]} for r in db.execute("SELECT id,parent,reason FROM g1_revisions ORDER BY rowid")],
                    "proposals": [{"id": r[0], "applied_revision": r[1]} for r in db.execute("SELECT id,applied FROM g1_proposals ORDER BY rowid")],
                    "renditions": [{"id": r[0], "revision": r[1]} for r in db.execute("SELECT id,revision FROM g1_renditions ORDER BY rowid")],
                    "exports": [{"id": r[0], "rendition": r[1]} for r in db.execute("SELECT id,rendition FROM g1_exports ORDER BY rowid")]}

    def propose(self, command):
        fields(command, ("command_id", "base_revision", "reason", "operations"))
        require(isinstance(command["command_id"], str) and command["command_id"], "Missing command ID")
        require(isinstance(command["reason"], str) and command["reason"], "Revision needs reasoning")
        require(isinstance(command["operations"], list) and command["operations"], "Empty proposal")
        payload = canonical(command)
        with closing(self.connect()) as db:
            row = db.execute("SELECT payload,applied FROM g1_proposals WHERE id=?", (command["command_id"],)).fetchone()
            if row:
                require(row[0] == payload, "Command ID reused with different payload")
                return {"proposal_id": command["command_id"], "applied_revision": row[1], "idempotent": True}
            if self.head(db) != command["base_revision"]:
                raise AdawError("STALE_REVISION", "Proposal base is not current head")
        _, source = self.source(command["base_revision"])
        for op in command["operations"]:
            require(isinstance(op, dict) and "kind" in op, "Invalid operation")
            if op["kind"] == "set_master_gain":
                fields(op, ("kind", "value"))
                number(op["value"])
                source["master"]["gain_db"] = op["value"]
                continue
            if op["kind"] == "append_bus_insert":
                fields(op, ("kind", "bus_id", "insert"))
                matches = [b for b in source["buses"] if b["id"] == op["bus_id"]]
                require(len(matches) == 1, "Unknown bus")
                matches[0]["inserts"].append(op["insert"])
                continue
            require(op.get("track_id") in {t["id"] for t in source["tracks"]}, "Unknown track")
            track = next(t for t in source["tracks"] if t["id"] == op["track_id"])
            if op["kind"] == "set_track_gain":
                fields(op, ("kind", "track_id", "value"))
                number(op["value"])
                track["gain_db"] = op["value"]
            elif op["kind"] == "move_event":
                fields(op, ("kind", "track_id", "event_id", "start_tick"))
                if track["protected"]:
                    raise AdawError("ARTISTIC_BOUNDARY", "Protected track events cannot be changed by this operation")
                matches = [e for e in track["events"] if e["id"] == op["event_id"]]
                require(len(matches) == 1, "Unknown event")
                matches[0]["start_tick"] = op["start_tick"]
            elif op["kind"] == "edit_event":
                fields(op, ("kind", "track_id", "event_id", "changes"))
                if track["protected"]:
                    raise AdawError("ARTISTIC_BOUNDARY", "Protected track events cannot be changed by this operation")
                fields(op["changes"], (), ("start_tick", "duration_ticks", "note", "velocity"))
                require(bool(op["changes"]), "Empty event edit")
                matches = [e for e in track["events"] if e["id"] == op["event_id"]]
                require(len(matches) == 1, "Unknown event")
                matches[0].update(op["changes"])
            elif op["kind"] == "set_instrument_module":
                fields(op, ("kind", "track_id", "module_sha256", "parameters"))
                require(track["kind"] == "faust_synth", "Only a Faust instrument has source code")
                track["instrument"]["module_sha256"] = op["module_sha256"]
                track["instrument"]["parameters"] = op["parameters"]
            elif op["kind"] == "set_instrument_parameter":
                fields(op, ("kind", "track_id", "binding", "value"))
                require(track["kind"] in ("faust_synth", "vst"), "Track has no exposed parameters")
                require(isinstance(op["binding"], str) and op["binding"], "Missing parameter binding")
                number(op["value"])
                track["instrument"]["parameters"][op["binding"]] = op["value"]
            else:
                raise AdawError("VALIDATION_ERROR", "Unsupported typed operation")
        self.validate_dependencies(source)
        with closing(self.connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            if self.head(db) != command["base_revision"]:
                raise AdawError("STALE_REVISION", "Head changed during proposal validation")
            row = db.execute("SELECT payload FROM g1_proposals WHERE id=?", (command["command_id"],)).fetchone()
            if row:
                require(row[0] == payload, "Concurrent command ID collision")
            else:
                db.execute("INSERT INTO g1_proposals VALUES (?,?,?,NULL)", (command["command_id"], payload, canonical(source)))
        return {"proposal_id": command["command_id"], "source_sha256": digest(canonical(source)), "operations": command["operations"], "head_changed": False}

    def apply(self, proposal_id):
        with closing(self.connect()) as db:
            candidate = db.execute("SELECT source,applied FROM g1_proposals WHERE id=?", (proposal_id,)).fetchone()
        if not candidate:
            raise AdawError("NOT_FOUND", "Proposal not found")
        # An already applied command remains idempotent even if an external plugin
        # has subsequently disappeared; a new commit must revalidate dependencies.
        if not candidate[1]:
            self.validate_dependencies(json.loads(candidate[0]))
        with closing(self.connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT payload,source,applied FROM g1_proposals WHERE id=?", (proposal_id,)).fetchone()
            if not row:
                raise AdawError("NOT_FOUND", "Proposal not found")
            if row[2]:
                return {"revision": row[2], "idempotent": True}
            command = json.loads(row[0])
            if self.head(db) != command["base_revision"]:
                raise AdawError("STALE_REVISION", "Head changed; explicit new proposal required (no silent rebase)")
            revision = "rev-" + digest(canonical({"parent": command["base_revision"], "source": json.loads(row[1]), "command": proposal_id}))
            db.execute("INSERT INTO g1_revisions VALUES (?,?,?,?)", (revision, command["base_revision"], row[1], command["reason"]))
            db.execute("UPDATE metadata SET value=? WHERE key='g1_head'", (revision,))
            db.execute("UPDATE g1_proposals SET applied=? WHERE id=?", (revision, proposal_id))
        return {"revision": revision, "listening": "NOT_EVALUATED"}

    def render_project(self, timeout, revision=None, proposal_id=None):
        require(not (revision and proposal_id), "Choose revision or proposal")
        if proposal_id:
            with closing(self.connect()) as db:
                row = db.execute("SELECT source FROM g1_proposals WHERE id=?", (proposal_id,)).fetchone()
            if not row:
                raise AdawError("NOT_FOUND", "Proposal not found")
            revision, source = "proposal:" + proposal_id, json.loads(row[0])
        else:
            revision, source = self.source(revision)
        self.validate_dependencies(source)
        graph, stems = compile_graph(source, self.read_content)
        result = self.render(graph, timeout, record_nodes=stems, benchmark=False)
        rendition_id = "rendition-" + result["job_id"]
        manifest = {"source_sha256": digest(canonical(source)), "graph_sha256": digest(canonical(graph)),
                    "profile_sha256": digest(canonical(source["profile"])), "revision": revision,
                    "environment": result["data"]["environment"], "plugin_dependencies": {}}
        instances = {t["id"]: t["instrument"] for t in source["tracks"] if t["kind"] == "vst"}
        for entity in [*source["tracks"], *source["buses"], {"id": "master", **source["master"]}]:
            instances.update({entity["id"]+"_fx"+str(i): inst for i,inst in enumerate(entity["inserts"]) if "registry_id" in inst})
        for instance_id, inst in instances.items():
            dep = self.plugin(inst["registry_id"])
            manifest["plugin_dependencies"][instance_id] = {"registry_id": inst["registry_id"], "binary_sha256": dep["sha256"],
                "files": dep["files"], "catalog_sha256": inst["catalog_sha256"], "state_sha256": inst["state_sha256"]}
        report = {"id": rendition_id, "revision": revision, "source": source, "manifest": manifest,
                  "graph": graph, "render": result, "listening": "NOT_EVALUATED"}
        self.put(canonical(report))
        with closing(self.connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("INSERT INTO g1_renditions VALUES (?,?,?)", (rendition_id, revision, canonical(report)))
            if revision == self.head(db):
                db.execute("INSERT OR REPLACE INTO metadata VALUES ('g1_last_playable',?)", (rendition_id,))
        return report

    def rendition(self, rendition_id):
        with closing(self.connect()) as db:
            row = db.execute("SELECT report FROM g1_renditions WHERE id=?", (rendition_id,)).fetchone()
        if not row:
            raise AdawError("NOT_FOUND", "Rendition not found")
        return json.loads(row[0])

    def analyze_rendition(self, rendition_id):
        report = self.rendition(rendition_id)
        audio_hash = report["render"]["data"]["audio_sha256"]
        self.read_content(audio_hash)
        return analyze_delivery(self.content / audio_hash, report["source"]["profile"], report["graph"]["frames"], require_pcm=False)

    def export(self, rendition_id, destination):
        import numpy as np
        import soundfile as sf
        report = self.rendition(rendition_id)
        source = self.read_content(report["render"]["data"]["audio_sha256"])
        audio, rate = sf.read(io.BytesIO(source), dtype="float64", always_2d=True)
        profile = report["source"]["profile"]
        rng = np.random.default_rng(profile["dither_seed"])
        # Quantize with round-to-nearest after 2-LSB peak-to-peak TPDF dither.
        scale = 2**23
        quantized = np.rint(audio * scale + rng.random(audio.shape) - rng.random(audio.shape))
        if not (np.max(quantized) < scale and np.min(quantized) >= -scale):
            raise AdawError("QUALITY_BLOCKED", "PCM24 clipping; revise master before export")
        stream = io.BytesIO()
        sf.write(stream, quantized / scale, rate, format="WAV", subtype="PCM_24")
        output_hash = self.put(stream.getvalue())
        quality = analyze_delivery(self.content / output_hash, profile, report["graph"]["frames"], require_pcm=True)
        if quality["status"] != "PASS":
            raise AdawError("QUALITY_BLOCKED", "Export failed the explicit engineering profile", quality=quality)
        dest = Path(destination).resolve()
        require(dest.suffix.lower() == ".wav", "Export requires .wav")
        # Export is a user-selected delivery path, never an authoritative project path.
        require(not dest.is_relative_to(self.root) and not self.root.is_relative_to(dest), "Export outside project storage")
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            require(file_hash(dest) == output_hash, "Destination exists with different bytes; choose a new path")
        else:
            temp = dest.with_name(dest.name + "." + uuid.uuid4().hex + ".tmp")
            try:
                with temp.open("xb") as f:
                    f.write(stream.getvalue())
                    f.flush()
                    os.fsync(f.fileno())
                # Windows rename fails rather than overwriting a racing destination.
                os.rename(temp, dest)
            finally:
                if temp.exists():
                    temp.unlink()
        require(file_hash(dest) == output_hash, "Published export hash mismatch")
        export_id = "export-" + digest(canonical({"rendition": rendition_id, "audio": output_hash, "profile": profile}))
        result = {"id": export_id, "rendition": rendition_id, "revision": report["revision"], "audio_sha256": output_hash,
                  "path": str(dest), "profile_sha256": digest(canonical(profile)), "quality": quality,
                  "listening": "NOT_EVALUATED", "label": "listening-review candidate", "dither": "seeded TPDF, round-to-nearest PCM24"}
        with closing(self.connect()) as db, db:
            db.execute("INSERT OR IGNORE INTO g1_exports VALUES (?,?,?)", (export_id, rendition_id, canonical(result)))
        return result

    def job_status(self, job_id):
        with closing(self.connect()) as db:
            row = db.execute("SELECT status,result FROM jobs WHERE id=?", (job_id,)).fetchone()
        if not row:
            raise AdawError("NOT_FOUND", "Job not found")
        return {"id": job_id, "status": row[0], "result": json.loads(row[1]) if row[1] else None}
