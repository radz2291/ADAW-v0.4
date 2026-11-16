"""Frontend replacement contract exercised over HTTP and the real CLI."""

from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
import subprocess
import sys
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from zipfile import ZipFile

import numpy as np
import pytest
import soundfile as sf

from app.service import binary_identity
from app.studio_api import make_server


def run_cli(module, *args, expect_success=True):
    result = subprocess.run(
        [sys.executable, "-m", module, *map(str, args)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
    )
    assert (result.returncode == 0) == expect_success, result.stdout + result.stderr
    envelope = json.loads(result.stdout)
    assert envelope["ok"] == expect_success
    return envelope


def cli(root, *args, expect_success=True):
    envelope = run_cli("app", "--root", root, "--timeout", 30, *args, expect_success=expect_success)
    assert envelope["schema_version"] == "adaw.result@1"
    return envelope["data" if expect_success else "error"]


def create_fixture(root, folder, vst=None):
    rate = 48000
    path = folder / "tone.wav"
    audio = .2 * np.sin(2 * np.pi * 440 * np.arange(rate * 2) / rate)
    sf.write(path, audio, rate, subtype="FLOAT")
    asset = cli(root, "asset-import", "--path", path, "--kind", "audio", "--provenance", "synthetic test input")
    source = {
        "schema": "adaw.arrangement@1",
        "title": "Independent client fixture",
        "brief": "Two-second test tone for HTTP and CLI parity",
        "tempo": 120,
        "ppq": 960,
        "sample_rate": rate,
        "block_size": 256,
        "length_ticks": 3840,
        "tail_frames": 0,
        "fade_frames": 240,
        "sections": [{"id": "test", "start_tick": 0, "end_tick": 3840, "mood": "test", "swing": .5}],
        "tracks": [{
            "id": "tone", "role": "test", "kind": "samples", "bus": "main",
            "gain_db": -3, "pan": 0, "protected": False, "inserts": [],
            "instrument": {"asset_sha256": asset["sha256"], "fade_frames": 24},
            "events": [{"id": "hit", "start_tick": 0, "duration_ticks": 3840, "note": 60, "velocity": 127}],
        }],
        "buses": [{"id": "main", "gain_db": 0, "inserts": []}],
        "master": {"gain_db": 0, "inserts": []},
        "profile": {
            "id": "contract-test", "status": "temporary_engineering_profile", "purpose": "test only",
            "sample_rate": rate, "channels": 2, "subtype": "PCM_24", "min_lufs": -30,
            "max_lufs": -10, "max_sample_peak_dbfs": -1, "max_estimated_true_peak_dbfs": -1,
            "true_peak_margin_db": .25, "max_dc": .001, "dither_seed": 1,
        },
    }
    if vst:
        source["tracks"][0].update(kind="vst", instrument=vst)
    source_path = folder / "source.json"
    source_path.write_text(json.dumps(source), encoding="utf-8")
    return cli(root, "project-create", "--source", source_path)["revision"]


def request(url, endpoint, payload=None, headers=None):
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    req = Request(url + endpoint, data=body, headers=headers or {})
    try:
        with urlopen(req, timeout=60) as response:
            return response.status, response.headers, response.read()
    except HTTPError as exc:
        with exc:
            return exc.code, exc.headers, exc.read()


def response_data(response):
    status, headers, body = response
    assert 200 <= status < 300, body.decode("utf-8")
    assert headers.get_content_type() == "application/json"
    envelope = json.loads(body)
    assert envelope["ok"], envelope
    return envelope["data"]


def test_desktop_assets_are_local_and_scripts_remain_restricted(tmp_path):
    root = tmp_path / "project"
    create_fixture(root, tmp_path)
    frontend = Path(__file__).resolve().parents[1] / "apps" / "studio"
    server = make_server(root, port=0, studio_dir=frontend)
    url = f"http://127.0.0.1:{server.server_port}"
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        for path in ("/", "/studio.js", "/studio.css", "/desktop.css", "/favicon.svg"):
            status, headers, body = request(url, path)
            assert status == 200 and body
            policy = headers["Content-Security-Policy"]
            assert "script-src 'self';" in policy
            assert "style-src 'self' 'unsafe-inline';" in policy
            assert "object-src 'none'" in policy
        assert request(url, "/studio.js")[2] == (frontend / "dist" / "studio.js").read_bytes()
        for forbidden in ("/package-lock.json", "/node_modules/wavesurfer.js/package.json",
                          "/../AGENTS.md", "/dist/../desktop.js"):
            assert request(url, forbidden)[0] == 404
        assert request(url, "/studio.js", headers={"Origin": "https://example.invalid"})[0] == 403
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_independent_client_and_cli_share_one_project(tmp_path):
    root = tmp_path / "project"
    base = create_fixture(root, tmp_path)
    server = make_server(root, port=0, studio_dir=None)
    host, port = server.server_address
    assert host == "127.0.0.1"
    url = f"http://{host}:{port}"
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        assert request(url, "/")[0] == 404
        state = response_data(request(url, "/api/v1/state"))
        assert state["project"] == cli(root, "project-inspect")
        source = response_data(request(url, f"/api/v1/revisions/{base}"))["source"]
        assert state["project"]["source"] == source
        token = response_data(request(url, "/api/v1/session"))["token"]
        headers = {"Content-Type": "application/json", "X-ADAW-Client": "studio", "X-ADAW-Token": token}

        proposal = {
            "command_id": "client-edit", "base_revision": base, "reason": "independent client timing edit",
            "operations": [{"kind": "edit_event", "track_id": "tone", "event_id": "hit",
                            "changes": {"start_tick": 480, "duration_ticks": 3360}}],
        }
        no_token = {"Content-Type": "application/json", "X-ADAW-Client": "studio"}
        for denied_headers in (no_token, {**headers, "Origin": "https://example.invalid"}):
            status, _, body = request(url, "/api/v1/proposals", proposal, denied_headers)
            assert status == 403 and json.loads(body)["error"]["code"] == "FORBIDDEN"
        assert cli(root, "history")["proposals"] == []

        response_data(request(url, "/api/v1/proposals", proposal, headers))
        staged = response_data(request(url, "/api/v1/proposals/client-edit"))
        assert staged["command"] == proposal
        assert staged["source"]["tracks"][0]["events"][0]["start_tick"] == 480
        assert cli(root, "project-inspect")["revision"] == base

        cli_proposal = {
            "command_id": "cli-edit", "base_revision": base, "reason": "disjoint level edit",
            "operations": [{"kind": "set_track_gain", "track_id": "tone", "value": -6}],
        }
        command_path = tmp_path / "command.json"
        command_path.write_text(json.dumps(cli_proposal), encoding="utf-8")
        cli(root, "proposal-create", "--command", command_path)
        cli(root, "proposal-apply", "--id", "cli-edit")
        revision = response_data(request(url, "/api/v1/apply", {"proposal_id": "client-edit"}, headers))["revision"]
        snapshot = cli(root, "project-inspect")
        assert snapshot["revision"] == revision
        track = snapshot["source"]["tracks"][0]
        assert track["gain_db"] == -6 and track["events"][0]["start_tick"] == 480
        assert response_data(request(url, "/api/v1/state"))["project"] == snapshot

        rendered = response_data(request(url, "/api/v1/render", {"revision": revision}, headers))
        assert rendered["revision"] == revision
        result = response_data(request(url, f"/api/v1/renditions/{rendered['id']}"))
        assert result["manifest"] == rendered["manifest"]
        audio_url = f"/api/v1/renditions/{rendered['id']}/audio"
        status, audio_headers, wav = request(url, audio_url)
        assert status == 200 and audio_headers.get_content_type() in {"audio/wav", "audio/x-wav"}
        audio, rate = sf.read(BytesIO(wav), always_2d=True)
        assert audio.shape == (96000, 2) and rate == 48000
        assert np.count_nonzero(audio[:12000]) == 0
        assert np.max(np.abs(audio[13000:])) > .09
        status, range_headers, prefix = request(url, audio_url, headers={"Range": "bytes=0-63"})
        assert status == 206 and range_headers["Content-Range"] == f"bytes 0-63/{len(wav)}"
        assert prefix == wav[:64]

        analysis = cli(root, "analyze", "--rendition", rendered["id"])
        assert response_data(request(url, "/api/v1/analyze", {"rendition_id": rendered["id"]}, headers)) == analysis
        assert analysis["status"] == "PASS" and analysis["audio_sha256"] == sha256(wav).hexdigest()
        export = cli(root, "export", "--rendition", rendered["id"], "--path", tmp_path / "delivery.wav")
        assert export["quality"]["status"] == "PASS"
        assert sha256((tmp_path / "delivery.wav").read_bytes()).hexdigest() == export["audio_sha256"]

        review = {"export_id": export["id"], "owner": "Synthetic test owner", "decision": "APPROVED",
                  "notes": "Test-only owner action in a temporary fixture"}
        created = response_data(request(url, "/api/v1/reviews", review, headers))
        assert response_data(request(url, "/api/v1/reviews", review, headers))["id"] == created["id"]
        recorded = response_data(request(url, f"/api/v1/renditions/{rendered['id']}"))["reviews"]
        assert [entry["decision"] for entry in recorded] == ["APPROVED"]
        assert recorded[0]["revision"] == revision
        assert recorded[0]["audio_sha256"] == export["audio_sha256"]
        assert recorded[0]["profile_sha256"] == export["profile_sha256"]
        new_revision = response_data(request(url, "/api/v1/undo", {"revision": revision}, headers))["revision"]
        track = cli(root, "project-inspect")["source"]["tracks"][0]
        assert track["gain_db"] == -6 and track["events"][0]["start_tick"] == 0
        new_render = response_data(request(url, "/api/v1/render", {"revision": new_revision}, headers))
        assert new_render["revision"] != revision
        assert response_data(request(url, f"/api/v1/renditions/{new_render['id']}"))["reviews"] == []
        assert response_data(request(url, f"/api/v1/renditions/{rendered['id']}"))["reviews"] == recorded
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=10)


@pytest.mark.skipif(os.environ.get("ADAW_TEST_APPROVED_DEXED") != "1", reason="Opt in to the approved native fixture")
def test_real_vst_parameter_http_cli_parity(tmp_path):
    plugin = Path(".local/plugins/dexed/Dexed.vst3").resolve()
    approved = "9632e3f90d2fda672e70e235dacced05ded975206b468ad867292928155fc279"
    assert plugin.is_dir() and binary_identity(plugin)["sha256"] == approved
    root = tmp_path / "vst-project"
    entry = cli(root, "plugin-allow", "--path", plugin, "--provenance", "G0/G1 approved Dexed 1.1.0 fixture")
    registry_id = entry["registry_id"]
    cli(root, "plugin-probe", "--id", registry_id, "--sample-rate", 48000, "--block-size", 256)
    captured = cli(root, "plugin-state-capture", "--id", registry_id, "--sample-rate", 48000, "--block-size", 256)
    vst = {key: captured[key] for key in ("state_sha256", "registry_id", "catalog_sha256")}
    vst["parameters"] = {"0": .8}
    base = create_fixture(root, tmp_path, vst=vst)

    server = make_server(root, port=0, studio_dir=None)
    url = "http://{}:{}".format(*server.server_address)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        state = response_data(request(url, "/api/v1/state"))
        catalog = next(entry for entry in state["plugins"] if entry.get("track_id") == "tone")
        assert any(param["index"] == 0 and param["name"] == "Output" for param in catalog["parameters"])
        token = response_data(request(url, "/api/v1/session"))["token"]
        headers = {"Content-Type": "application/json", "X-ADAW-Client": "studio", "X-ADAW-Token": token}
        baseline = cli(root, "project-render", "--revision", base)
        proposal = {
            "command_id": "ui-vst-edit", "base_revision": base, "reason": "exercise VST output binding",
            "operations": [{"kind": "set_instrument_parameter", "track_id": "tone", "binding": "0", "value": .4}],
        }
        response_data(request(url, "/api/v1/proposals", proposal, headers))
        conflicting = {**proposal, "command_id": "agent-vst-edit",
                       "operations": [{**proposal["operations"][0], "value": .6}]}
        command_path = tmp_path / "command.json"
        command_path.write_text(json.dumps(conflicting), encoding="utf-8")
        cli(root, "proposal-create", "--command", command_path)
        cli(root, "proposal-apply", "--id", "agent-vst-edit")
        status, _, body = request(url, "/api/v1/apply", {"proposal_id": "ui-vst-edit"}, headers)
        error = json.loads(body)["error"]
        assert status == 409 and error["code"] == "CONFLICT"
        assert ["tracks", "tone", "instrument", "parameters", "0"] in [
            entry["path"] for entry in error["details"]["conflicts"]
        ]
        revision = cli(root, "project-inspect")["revision"]
        proposal["command_id"] = "ui-vst-edit-retry"
        proposal["base_revision"] = revision
        response_data(request(url, "/api/v1/proposals", proposal, headers))
        revision = response_data(request(url, "/api/v1/apply", {"proposal_id": "ui-vst-edit-retry"}, headers))["revision"]
        assert cli(root, "project-inspect")["source"]["tracks"][0]["instrument"]["parameters"] == {"0": .4}
        final = response_data(request(url, "/api/v1/render", {"revision": revision}, headers))
        assert final["manifest"]["plugin_dependencies"]["tone"]["binary_sha256"] == approved
        assert final["manifest"]["plugin_dependencies"]["tone"]["state_sha256"] == captured["state_sha256"]
        assert baseline["render"]["quality"]["rms"] > 0
        ratio = final["quality"]["rms"] / baseline["render"]["quality"]["rms"]
        assert ratio == pytest.approx(.5, abs=.04)
        print(f"Dexed Output 0.8 to 0.4 RMS ratio {ratio:.9f}")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=10)

    package = tmp_path / "native.adaw"
    archived = run_cli("app.portability", "backup", "--root", root, "--archive", package)["data"]
    assert archived["sha256"] == sha256(package.read_bytes()).hexdigest()
    restored_root = tmp_path / "native-restored"
    restored = run_cli("app.portability", "restore", "--archive", package, "--root", restored_root)["data"]
    assert restored["revision"] == revision and restored["missing_plugins"] == [registry_id]
    assert cli(restored_root, "project-inspect") == cli(root, "project-inspect")
    assert cli(restored_root, "history") == cli(root, "history")
    error = cli(restored_root, "project-render", expect_success=False)
    assert error["code"] == "PLUGIN_MISSING"
    cli(restored_root, "plugin-allow", "--path", plugin, "--provenance", "Reauthorize approved G0 fixture")
    reopened = cli(restored_root, "project-render", "--revision", revision)
    assert reopened["manifest"]["source_sha256"] == final["manifest"]["source_sha256"]
    assert reopened["manifest"]["graph_sha256"] == final["manifest"]["graph_sha256"]
    assert reopened["manifest"]["plugin_dependencies"] == final["manifest"]["plugin_dependencies"]
    restored_ratio = reopened["render"]["quality"]["rms"] / final["quality"]["rms"]
    assert restored_ratio == pytest.approx(1, abs=.04)
    print(f"Restored Dexed same-source RMS ratio {restored_ratio:.9f}, package {archived['sha256']}")

    command = {"command_id": "restore-independent-edit", "base_revision": revision, "reason": "test isolated history",
               "operations": [{"kind": "set_track_gain", "track_id": "tone", "value": -12}]}
    command_path.write_text(json.dumps(command), encoding="utf-8")
    cli(restored_root, "proposal-create", "--command", command_path)
    separate_revision = cli(restored_root, "proposal-apply", "--id", command["command_id"])["revision"]
    assert separate_revision != revision
    assert cli(root, "project-inspect")["revision"] == revision


def test_archive_rejects_altered_member_and_manifest(tmp_path):
    root = tmp_path / "source"
    revision = create_fixture(root, tmp_path)
    package = tmp_path / "original.adaw"
    run_cli("app.portability", "backup", "--root", root, "--archive", package)
    good = tmp_path / "restored"
    assert run_cli("app.portability", "restore", "--root", good, "--archive", package)["data"]["revision"] == revision

    for what in ("member", "manifest"):
        altered = tmp_path / f"altered-{what}.adaw"
        with ZipFile(package) as source, ZipFile(altered, "w") as destination:
            asset = next(name for name in source.namelist() if name.startswith("content/"))
            for name in source.namelist():
                content = source.read(name)
                if what == "member" and name == asset:
                    content = bytes([content[0] ^ 1]) + content[1:]
                if what == "manifest" and name == "manifest.json":
                    manifest = json.loads(content)
                    del manifest["files"][asset]
                    content = json.dumps(manifest).encode("utf-8")
                destination.writestr(name, content)
        rejected = tmp_path / f"rejected-{what}"
        response = run_cli("app.portability", "restore", "--root", rejected, "--archive", altered, expect_success=False)
        assert response["error"]["message"] == {
            "member": "Package checksum mismatch", "manifest": "Package inventory differs from manifest",
        }[what]
        assert not rejected.exists()


def test_everyday_rubric_is_frozen():
    from hashlib import sha256
    from pathlib import Path
    folder = Path(__file__).resolve().parents[1] / "docs" / "evaluation"
    expected = "904217d07d250e4fa1677b522372313fbf449c9a15177f022a229457f0d78253"
    assert sha256((folder / "EVERYDAY-INTERACTION-v1.md").read_bytes()).hexdigest() == expected
    assert expected in (folder / "EVERYDAY-INTERACTION-v1.sha256").read_text()
