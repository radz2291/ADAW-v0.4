"""Versioned localhost transport for ProjectService and an optional frontend."""

import argparse
import hmac
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
import secrets
from urllib.parse import unquote, urlsplit

from app.contracts import canonical, fields
from app.errors import AdawError
from app.project import ProjectService
from app.reviews import ReviewStore

MAX_COMMAND_BYTES = 8 * 1024 * 1024
RENDER_TIMEOUT_SECONDS = 180
STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/studio.css": ("studio.css", "text/css; charset=utf-8"),
    "/studio.js": ("studio.js", "text/javascript; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
}


def rendition_summary(report):
    return {"id": report["id"], "revision": report["revision"], "manifest": report["manifest"],
            "quality": report["render"]["quality"], "listening": report["listening"]}


def make_server(root, port=0, studio_dir=None):
    service = ProjectService(root)
    reviews = ReviewStore(service)
    token = secrets.token_urlsafe(32)
    assets = Path(studio_dir).resolve() if studio_dir is not None else None

    class Handler(BaseHTTPRequestHandler):
        def send_body(self, status, body, content_type, extra=()):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy",
                             "default-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'")
            for key, value in extra:
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(body)

        def send_json(self, status, value):
            self.send_body(status, canonical(value), "application/json; charset=utf-8")

        def authorize(self, write):
            authority = f"127.0.0.1:{self.server.server_port}"
            origin = self.headers.get("Origin")
            if (self.headers.get("Host") != authority
                    or (origin is not None and origin != "http://" + authority)
                    or self.headers.get("Sec-Fetch-Site") == "cross-site"):
                raise AdawError("FORBIDDEN", "Use the exact local Studio origin")
            if write and (self.headers.get("X-ADAW-Client") != "studio" or not hmac.compare_digest(
                    self.headers.get("X-ADAW-Token", "").encode(), token.encode())):
                raise AdawError("FORBIDDEN", "A valid local Studio session token is required")

        def command_body(self):
            if self.headers.get_content_type() != "application/json":
                raise AdawError("VALIDATION_ERROR", "Expected an application/json command")
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= MAX_COMMAND_BYTES:
                raise AdawError("VALIDATION_ERROR", "Missing or oversized command body")
            value = json.loads(self.rfile.read(length))
            if not isinstance(value, dict):
                raise AdawError("VALIDATION_ERROR", "Expected a command object")
            return value

        def audio(self, audio_sha256):
            audio = service.read_content(audio_sha256)
            size = len(audio)
            request = self.headers.get("Range")
            headers = [("Accept-Ranges", "bytes")]
            if request is None:
                self.send_body(200, audio, "audio/wav", headers)
                return
            match = re.fullmatch(r"bytes=(\d{0,20})-(\d{0,20})", request)
            if match and any(match.groups()):
                first, last = match.groups()
                start = int(first) if first else max(0, size - int(last))
                end = min(size - 1, int(last)) if first and last else size - 1
                if start <= end:
                    headers.append(("Content-Range", f"bytes {start}-{end}/{size}"))
                    self.send_body(206, audio[start:end+1], "audio/wav", headers)
                    return
            self.send_body(416, b"", "audio/wav", [("Content-Range", f"bytes */{size}")])

        def get_data(self, route):
            if route == "/api/v1/session":
                return {"token": token}
            if route == "/api/v1/state":
                snapshot = service.project_inspect()
                return {"project": snapshot, "history": service.history(),
                        "plugins": service.parameter_catalogs(snapshot["revision"])}
            match = re.fullmatch(r"/api/v1/(revisions|proposals|renditions)/([A-Za-z0-9_:-]+)", route)
            if match:
                collection, ident = match.groups()
                if collection == "revisions":
                    revision, source = service.source(ident)
                    return {"revision": revision, "source": source}
                if collection == "proposals":
                    return service.inspect_proposal(ident)
                return {**rendition_summary(service.rendition(ident)), "reviews": reviews.for_rendition(ident)}
            raise AdawError("NOT_FOUND", "Unknown Studio endpoint")

        def post_data(self, route, body):
            if route == "/api/v1/proposals":
                return service.propose(body)
            if route == "/api/v1/apply":
                fields(body, ("proposal_id",))
                return service.apply(body["proposal_id"])
            if route == "/api/v1/undo":
                fields(body, ("revision",))
                return service.undo(body["revision"])
            if route == "/api/v1/render":
                fields(body, (), ("revision", "proposal_id"))
                return rendition_summary(service.render_project(RENDER_TIMEOUT_SECONDS, **body))
            if route == "/api/v1/analyze":
                fields(body, ("rendition_id",))
                return service.analyze_rendition(body["rendition_id"])
            if route == "/api/v1/reviews":
                fields(body, ("export_id", "owner", "decision", "notes"))
                return reviews.record(**body)
            raise AdawError("NOT_FOUND", "Unknown Studio endpoint")

        def dispatch(self, write):
            try:
                self.authorize(write)
                route = unquote(urlsplit(self.path).path)
                if write:
                    data = self.post_data(route, self.command_body())
                else:
                    if assets and route in STATIC_FILES:
                        filename, media_type = STATIC_FILES[route]
                        self.send_body(200, (assets / filename).read_bytes(), media_type)
                        return
                    match = re.fullmatch(r"/api/v1/(renditions|exports)/([A-Za-z0-9_-]+)/audio", route)
                    if match:
                        collection, ident = match.groups()
                        if collection == "exports":
                            audio_sha256 = reviews.export_record(ident)["audio_sha256"]
                        else:
                            audio_sha256 = service.rendition(ident)["render"]["data"]["audio_sha256"]
                        self.audio(audio_sha256)
                        return
                    data = self.get_data(route)
                self.send_json(200, {"ok": True, "data": data})
            except ConnectionError:
                return
            except AdawError as exc:
                status = {"NOT_FOUND": 404, "FORBIDDEN": 403, "CONFLICT": 409,
                          "REVISION_CONFLICT": 409, "STALE_REVISION": 409}.get(exc.code, 400)
                self.send_json(status, {"ok": False, "error": {"code": exc.code, "message": str(exc),
                                                               "details": exc.details}})
            except (ValueError, TypeError, UnicodeError, FileNotFoundError) as exc:
                self.send_json(400, {"ok": False, "error": {"code": "VALIDATION_ERROR",
                                                           "message": str(exc), "details": {}}})

        def do_GET(self):
            self.dispatch(False)

        def do_POST(self):
            self.dispatch(True)

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, help="Local project directory")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--api-only", action="store_true")
    options = parser.parse_args()
    frontend = None if options.api_only else Path(__file__).resolve().parents[1] / "apps" / "studio"
    with make_server(options.root, options.port, frontend) as server:
        print(f"ADAW is available at http://127.0.0.1:{server.server_port}/", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
