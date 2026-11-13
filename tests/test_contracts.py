import copy
import json
import subprocess
import sys

import pytest

from app.contracts import RenderGraph, canonical, catalog_hash, tick_sample
from app.errors import AdawError
from app.service import Service
from tools.fixtures import faust_fixture


def test_hash_is_order_independent_and_rejects_nonfinite():
    assert canonical({"b": 2, "a": 1}) == canonical({"a": 1, "b": 2})
    with pytest.raises(ValueError):
        canonical({"x": float("nan")})


@pytest.mark.parametrize("bpm", [120, 123.45, 87])
def test_tick_origin_has_no_accumulated_drift(bpm):
    assert tick_sample(960 * 4 * 1000, bpm, 960, 48000) == round(4 * 1000 * 60 * 48000 / bpm)
    assert tick_sample(0, bpm, 960, 48000) == 0


@pytest.mark.parametrize("change", [
    lambda g: g.update(unknown="discard me"),
    lambda g: g["nodes"][0].update(inputs=["master"]),
    lambda g: g["nodes"][0].update(id="../escape"),
    lambda g: g["nodes"][0]["config"].update(amplitude=float("nan")),
    lambda g: g["nodes"].append(copy.deepcopy(g["nodes"][0])),
])
def test_invalid_graph_rejected(change):
    g = faust_fixture()
    change(g)
    with pytest.raises(AdawError):
        RenderGraph.parse(g)


def test_snapshot_is_immutable():
    g = faust_fixture()
    snapshot = RenderGraph.parse(g)
    original = snapshot.sha256
    g["frames"] = 1
    exposed = snapshot.value
    exposed["frames"] = 1
    assert snapshot.sha256 == original
    assert snapshot.value["frames"] == 768000


def test_catalog_binding_ignores_current_values_but_detects_renamed_parameters():
    base = [{"index": 0, "name": "gain", "currentValText": "0.5", "text": "0.5"}]
    moved = [{"index": 0, "name": "gain", "currentValText": "0.8", "text": "0.8"}]
    assert catalog_hash(base) == catalog_hash(moved)
    moved[0]["name"] = "cutoff"
    assert catalog_hash(base) != catalog_hash(moved)


def test_unapproved_plugin_cannot_be_probed(tmp_path):
    s = Service(tmp_path)
    with pytest.raises(AdawError, match="not authorized"):
        s.probe_plugin("unapproved", 48000, 256, 10)
    assert list(s.staging.iterdir()) == []
    assert s.inspect()["head"] is None


def test_content_corruption_rejected(tmp_path):
    s = Service(tmp_path)
    sha = s.put(b"fixture")
    (s.content / sha).write_bytes(b"broken")  # deliberate fault fixture
    with pytest.raises(AdawError, match="Corrupt"):
        s.put(b"fixture")


def test_cli_invalid_command_is_json(tmp_path):
    r = subprocess.run([sys.executable, "-m", "app", "--root", str(tmp_path), "--timeout", "10", "missing"], capture_output=True, text=True)
    assert r.returncode == 1
    data = json.loads(r.stdout)
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert data["schema_version"] == "adaw.result@1"

