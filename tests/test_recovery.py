"""Exercise interrupted worker ownership through a real process exit."""

from contextlib import closing
import subprocess
import sys
import time

from app.project import ProjectService


def test_interrupted_owner_does_not_promote_worker(tmp_path):
    project = ProjectService(tmp_path)
    script = ("import sys; from app.project import ProjectService; "
              "ProjectService(sys.argv[1]).run_worker("
              "{'operation':'fault_timeout','sleep_seconds':4},20)")
    owner = subprocess.Popen([sys.executable, "-c", script, str(tmp_path)])
    try:
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            with closing(project.connect()) as db:
                row = db.execute("SELECT id FROM jobs WHERE status='running'").fetchone()
            if row:
                break
            time.sleep(.05)
        assert row
        job_id = row[0]
        assert project.reconcile_jobs()["active"] == [job_id]
        owner.kill()
        owner.wait(timeout=10)
        # Windows may signal the exited process before releasing its byte-range lock.
        deadline = time.monotonic() + 5
        while True:
            recovery = project.reconcile_jobs()
            if recovery["interrupted"] or time.monotonic() >= deadline:
                break
            assert recovery["active"] == [job_id]
            time.sleep(.05)
        assert recovery["interrupted"] == [job_id]
        assert project.job_status(job_id)["status"] == "interrupted"
        assert project.job_status(job_id)["result"]["error"]["code"] == "SERVICE_INTERRUPTED"
        assert project.reconcile_jobs()["interrupted"] == []
        assert project.inspect()["head"] is None
    finally:
        if owner.poll() is None:
            owner.kill()
            owner.wait(timeout=10)
