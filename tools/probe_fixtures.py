"""Explicitly authorize and probe only the user-requested downloaded fixtures."""
import argparse
import json
from pathlib import Path
from app.service import Service


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True)
    p.add_argument("--timeout", type=float, required=True)
    p.add_argument("--approval", required=True)
    args = p.parse_args()
    s = Service(args.root)
    results = {}
    for role, path in {"instrument": ".local/plugins/dexed/Dexed.vst3",
                       "effect": ".local/plugins/consolidated/Airwindows Consolidated.vst3",
                       "limited_effect": ".local/plugins/airwindows/PurestGain64.dll"}.items():
        entry = s.authorize_plugin(path, args.approval)
        probe = s.probe_plugin(entry["registry_id"], 48000, 256, args.timeout)
        results[role] = {"entry": entry, "probe": probe}
        print(role, entry["registry_id"], flush=True)
        print("parameters:", len(probe["data"]["parameters"]), flush=True)
    Path(".local/fixture-plugins.json").write_text(json.dumps(results, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

