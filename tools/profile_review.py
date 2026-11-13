"""Render a preview under an explicitly supplied destination profile."""

import argparse
import json
from pathlib import Path

from app.project import ProjectService


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--proposal-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    project = ProjectService(args.root)
    profile = json.loads(Path(args.profile).read_text(encoding="utf-8"))
    base, _ = project.source()
    project.propose({"command_id": args.proposal_id, "base_revision": base,
                     "reason": "Compare explicit delivery profile: " + profile["id"],
                     "operations": [{"kind": "set_delivery_profile", "profile": profile}]})
    preview = project.render_project(180, proposal_id=args.proposal_id)
    print(json.dumps(project.export(preview["id"], args.output)))


if __name__ == "__main__":
    main()
