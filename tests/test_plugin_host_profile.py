"""Host opt-in must not turn failed native work into success."""
import os

import pytest

from app.errors import AdawError
from app.service import Service

PROFILE = "windows-stereo-zero-aux-isolated-v1"


def test_host_profile_requires_approved_unchanged_plugin(tmp_path):
    service = Service(tmp_path / "project")
    with pytest.raises(AdawError):
        service.configure_plugin_host("missing", "standard", "test")
    binary = tmp_path / "fixture.dll"
    binary.write_bytes(b"not executable; identity-only test")
    identity = service.authorize_plugin(binary, "identity test")
    ident = identity["registry_id"]
    assert service.plugin(ident)["host_profile"] == "standard"
    service.configure_plugin_host(ident, "standard", "test reset")
    assert Service(service.root).plugin(ident)["host_profile"] == "standard"
    with pytest.raises(AdawError):
        service.configure_plugin_host(ident, "unknown", "test")
    binary.write_bytes(b"changed")
    with pytest.raises(AdawError):
        service.configure_plugin_host(ident, "standard", "test")


@pytest.mark.skipif(os.name != "nt", reason="Windows-only completion policy")
def test_completed_worker_can_exit_without_dll_detach(tmp_path):
    result = Service(tmp_path).run_worker({"operation": "doctor", "host_profile": PROFILE}, 20)
    assert result["ok"] and result["exit_code"] == 0
    assert result["warnings"][0]["code"] == "HOST_SHUTDOWN_BYPASSED"


@pytest.mark.skipif(os.name != "nt", reason="Windows-only completion policy")
@pytest.mark.parametrize("payload,timeout,code", [
    ({"operation": "fault_crash"}, 10, "WORKER_CRASHED"),
    ({"operation": "fault_timeout", "sleep_seconds": 10}, .2, "TIMEOUT"),
    ({"operation": "not_implemented"}, 10, "NOT_IMPLEMENTED"),
])
def test_completion_policy_does_not_mask_failed_work(tmp_path, payload, timeout, code):
    service = Service(tmp_path)
    with pytest.raises(AdawError) as error:
        service.run_worker({**payload, "host_profile": PROFILE}, timeout)
    assert error.value.code == code
    assert service.inspect()["head"] is None
    assert service.inspect()["last_playable"] is None
