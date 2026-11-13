"""Generate a measured, loudness-matched listening comparison."""

import argparse
import json
from pathlib import Path

from app.production import matched_comparison
from app.project import ProjectService


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--target-lufs", type=float, required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("renditions", nargs="+")
    args = parser.parse_args()
    report = matched_comparison(ProjectService(args.root), args.renditions, args.target_lufs, args.output)
    (Path(args.output) / "comparison.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
