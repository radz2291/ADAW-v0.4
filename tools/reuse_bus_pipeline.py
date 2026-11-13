"""Capture an ordered bus recipe and stage it on a separate project."""

import argparse
import json
from pathlib import Path

from app.contracts import canonical, require
from app.project import ProjectService
from app.service import binary_identity

SCHEMA = "adaw.bus-pipeline@1"


def capture(source, bus_id):
    revision, arrangement = source.source()
    bus = next((bus for bus in arrangement["buses"] if bus["id"] == bus_id), None)
    require(bus is not None and bus["inserts"], "Choose a bus with an existing insert chain")
    plugins = {}
    for insert in bus["inserts"]:
        if "registry_id" in insert:
            identity = source.plugin(insert["registry_id"])
            plugins[insert["registry_id"]] = {"sha256": identity["sha256"], "files": identity["files"]}
    return {"schema": SCHEMA, "source_revision": revision, "source_bus": bus_id,
            "inserts": bus["inserts"], "plugins": plugins,
            "state_policy": "Capture a fresh approved destination state and apply explicit parameter overrides"}


def stage(source, destination, recipe, bus_id, command_id, allowed_paths, overrides=()):
    require(recipe["schema"] == SCHEMA, "Unsupported pipeline recipe")
    require(source.root != destination.root, "Choose a separate destination project")
    revision, arrangement = destination.source()
    bus = next((item for item in arrangement["buses"] if item["id"] == bus_id), None)
    require(bus is not None and not bus["inserts"], "Choose an existing bus with an empty insert chain")
    approved = {"plugin-" + item["sha256"]: item for item in map(binary_identity, allowed_paths)}
    for ident, fingerprint in recipe["plugins"].items():
        require(ident in approved and approved[ident]["files"] == fingerprint["files"],
                f"Explicit matching plugin path required for {ident}")
    operations = []
    for index, entry in enumerate(recipe["inserts"]):
        insert = {**entry, "parameters": dict(entry["parameters"])}
        if "registry_id" in entry:
            ident = entry["registry_id"]
            destination.authorize_plugin(approved[ident]["path"], "Explicit operator path for bus pipeline")
            rate, block = arrangement["sample_rate"], arrangement["block_size"]
            destination.probe_plugin(ident, rate, block, 60)
            state = destination.capture_plugin_state(ident, 60, rate, block)
            require(state["catalog_sha256"] == entry["catalog_sha256"], "Pipeline catalog fingerprint differs")
            insert["state_sha256"] = state["state_sha256"]
        else:
            identity = insert["module_sha256"]
            source.read_content(identity)
            destination.import_file(source.content / identity, "faust", "Reusable bus recipe module", 30)
        operations.append({"kind": "append_bus_insert", "bus_id": bus_id, "insert": insert})
        for slot, binding, value in overrides:
            if index == slot:
                operations.append({"kind": "set_bus_insert_parameter", "bus_id": bus_id,
                                   "insert_index": index, "binding": binding, "value": value})
    command = {"command_id": command_id, "base_revision": revision,
               "reason": "Stage reusable bus pipeline on separate project", "operations": operations}
    return destination.propose(command)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-project", required=True)
    parser.add_argument("--root", required=True)
    parser.add_argument("--source-bus", required=True)
    parser.add_argument("--destination-bus", required=True)
    parser.add_argument("--command-id", required=True)
    parser.add_argument("--allow-plugin", action="append", default=[])
    parser.add_argument("--recipe", required=True)
    args = parser.parse_args()
    source = ProjectService(args.from_project)
    recipe = capture(source, args.source_bus)
    Path(args.recipe).write_bytes(canonical(recipe))
    result = stage(source, ProjectService(args.root), recipe, args.destination_bus, args.command_id,
                   args.allow_plugin)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
