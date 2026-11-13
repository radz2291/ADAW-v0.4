"""Record explicit owner decisions against verified export identities."""

from contextlib import closing
from datetime import datetime, timezone
import json

from app.contracts import canonical, digest, require
from app.errors import AdawError


class ReviewStore:
    def __init__(self, project):
        self.project = project
        with closing(project.connect()) as db, db:
            db.execute("""CREATE TABLE IF NOT EXISTS owner_reviews (
                id TEXT PRIMARY KEY, rendition TEXT NOT NULL, record BLOB NOT NULL
            )""")

    def for_rendition(self, rendition_id):
        with closing(self.project.connect()) as db:
            return [json.loads(row[0]) for row in db.execute(
                "SELECT record FROM owner_reviews WHERE rendition=? ORDER BY rowid", (rendition_id,))]

    def export_record(self, export_id):
        require(isinstance(export_id, str) and bool(export_id), "Export ID required")
        with closing(self.project.connect()) as db:
            row = db.execute("SELECT report FROM g1_exports WHERE id=?", (export_id,)).fetchone()
        if row is None:
            raise AdawError("NOT_FOUND", "Verified export required", export_id=export_id)
        return json.loads(row[0])

    def record(self, export_id, owner, decision, notes):
        require(isinstance(owner, str) and bool(owner.strip()), "Owner name required")
        require(decision in ("APPROVED", "CHANGES_REQUESTED"), "Invalid review decision")
        require(isinstance(notes, str) and bool(notes.strip()), "Listening notes required")
        export = self.export_record(export_id)
        require(export["quality"]["status"] == "PASS", "Export must have passed technical checks")
        self.project.read_content(export["audio_sha256"])
        record = {
            "schema": "adaw.owner-review@1", "export_id": export_id,
            "rendition": export["rendition"], "revision": export["revision"],
            "audio_sha256": export["audio_sha256"], "profile_sha256": export["profile_sha256"],
            "owner": owner.strip(), "decision": decision, "notes": notes.strip(),
        }
        review_id = "review-" + digest(canonical(record))
        record.update(id=review_id, time_utc=datetime.now(timezone.utc).isoformat())
        with closing(self.project.connect()) as db, db:
            db.execute("INSERT OR IGNORE INTO owner_reviews VALUES (?,?,?)",
                       (review_id, export["rendition"], canonical(record)))
            return json.loads(db.execute("SELECT record FROM owner_reviews WHERE id=?", (review_id,)).fetchone()[0])
