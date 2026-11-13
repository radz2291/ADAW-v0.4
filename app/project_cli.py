"""JSON CLI routes for the G1 service. Explicit file paths are local grants."""
import json
from pathlib import Path
from app.project import ProjectService


COMMANDS = {"project-create", "project-inspect", "history", "asset-import", "proposal-create", "proposal-apply",
            "project-render", "analyze", "export", "job-status", "plugin-state-capture"}


def add_commands(sub):
    sub.add_parser("project-inspect")
    sub.add_parser("history")
    create = sub.add_parser("project-create")
    create.add_argument("--source", required=True)
    asset = sub.add_parser("asset-import")
    asset.add_argument("--path", required=True)
    asset.add_argument("--kind", required=True, choices=("audio", "faust"))
    asset.add_argument("--provenance", required=True)
    proposal = sub.add_parser("proposal-create")
    proposal.add_argument("--command", dest="command_file", required=True)
    apply = sub.add_parser("proposal-apply")
    apply.add_argument("--id", required=True)
    render = sub.add_parser("project-render")
    render.add_argument("--revision")
    render.add_argument("--proposal")
    analyze = sub.add_parser("analyze")
    analyze.add_argument("--rendition", required=True)
    export = sub.add_parser("export")
    export.add_argument("--rendition", required=True)
    export.add_argument("--path", required=True)
    job = sub.add_parser("job-status")
    job.add_argument("--id", required=True)
    state = sub.add_parser("plugin-state-capture")
    state.add_argument("--id", required=True)
    state.add_argument("--sample-rate", required=True, type=int)
    state.add_argument("--block-size", required=True, type=int)


def execute(args):
    service = ProjectService(args.root)
    if args.command == "project-create":
        return service.create(json.loads(Path(args.source).read_text(encoding="utf-8")))
    if args.command == "project-inspect":
        return service.project_inspect()
    if args.command == "history":
        return service.history()
    if args.command == "asset-import":
        return service.import_file(args.path, args.kind, args.provenance, args.timeout)
    if args.command == "proposal-create":
        return service.propose(json.loads(Path(args.command_file).read_text(encoding="utf-8")))
    if args.command == "proposal-apply":
        return service.apply(args.id)
    if args.command == "project-render":
        return service.render_project(args.timeout, args.revision, args.proposal)
    if args.command == "analyze":
        return service.analyze_rendition(args.rendition)
    if args.command == "export":
        return service.export(args.rendition, args.path)
    if args.command == "job-status":
        return service.job_status(args.id)
    if args.command == "plugin-state-capture":
        return service.capture_plugin_state(args.id, args.timeout, args.sample_rate, args.block_size)
