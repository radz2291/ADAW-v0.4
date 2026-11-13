import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
import uuid

from app.errors import AdawError
from app.service import Service


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise AdawError("VALIDATION_ERROR", message)


def main(argv=None):
    request_id = uuid.uuid4().hex
    operation = "parse"
    try:
        parser = Parser(description="ADAW G0 engineering CLI; JSON output")
        parser.add_argument("--root", required=True, help="Explicit G0 project/service directory")
        parser.add_argument("--timeout", type=float, required=True, help="Worker wall-clock deadline in seconds")
        parser.add_argument("--json", action="store_true", help="JSON is always used in G0")
        sub = parser.add_subparsers(dest="command", required=True)
        sub.add_parser("doctor")
        sub.add_parser("inspect")
        module = sub.add_parser("module-validate")
        module.add_argument("--source", required=True)
        module.add_argument("--sample-rate", type=int, required=True)
        module.add_argument("--block-size", type=int, required=True)
        render = sub.add_parser("render")
        render.add_argument("--graph", required=True)
        render.add_argument("--commit-fixture", action="store_true")
        render.add_argument("--base-revision")
        allow = sub.add_parser("plugin-allow")
        allow.add_argument("--path", required=True)
        allow.add_argument("--provenance", required=True)
        probe = sub.add_parser("plugin-probe")
        probe.add_argument("--id", required=True)
        probe.add_argument("--sample-rate", type=int, required=True)
        probe.add_argument("--block-size", type=int, required=True)
        args = parser.parse_args(argv)
        operation = args.command
        service = Service(args.root)
        if args.command == "doctor":
            data = service.run_worker({"operation": "doctor"}, args.timeout)
        elif args.command == "inspect":
            data = service.inspect()
        elif args.command == "plugin-allow":
            data = service.authorize_plugin(args.path, args.provenance)
        elif args.command == "plugin-probe":
            data = service.probe_plugin(args.id, args.sample_rate, args.block_size, args.timeout)
        elif args.command == "module-validate":
            if args.sample_rate <= 0 or args.block_size <= 0:
                raise AdawError("VALIDATION_ERROR", "Rate and block size must be positive")
            data = service.run_worker({"operation": "module_validate", "source": Path(args.source).read_text(encoding="utf-8"),
                "sample_rate": args.sample_rate, "block_size": args.block_size}, args.timeout)
        else:
            graph = json.loads(Path(args.graph).read_text(encoding="utf-8"))
            data = service.render(graph, args.timeout, args.commit_fixture, args.base_revision)
        result = {"ok": True, "data": data, "error": None}
    except (AdawError, ValueError, OSError) as exc:
        result = {"ok": False, "data": None, "error": {
            "code": getattr(exc, "code", "VALIDATION_ERROR"), "message": str(exc), "target": operation,
            "retryable": False, "details": getattr(exc, "details", {})}}
    result.update(schema_version="adaw.result@1", request_id=request_id, operation=operation,
                  warnings=[], evidence_refs=[], time_utc=datetime.now(timezone.utc).isoformat())
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())

