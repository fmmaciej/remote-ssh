"""Bounded verification-launcher diagnosis; does not modify repository tests."""

import json
import os
import signal
import subprocess
import time
from pathlib import Path

root = Path.cwd()
folder = root / "dev/docs/install-cli-coordinator-evidence"
command = [
    str(root / "dev/.venv/bin/python"), "-m", "pytest", "-vv", "-s",
    "-o", "faulthandler_timeout=10",
    "dev/tests/test_atuin_lifecycle.py::test_upstream_atuin_full_rc_lifecycle",
]
env = os.environ.copy()
env.update(UV_OFFLINE="1", PYTHONUNBUFFERED="1")
for name in ("PYTEST_ADDOPTS", "BASH_ENV", "ENV", "REMOTE_ENV_DIR"):
    env.pop(name, None)
started = time.monotonic()
timed_out = False
with (folder / "r1-atuin-diagnostic.log").open("w") as logfile:
    process = subprocess.Popen(
        command, cwd=root, env=env, stdout=logfile, stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    try:
        process.wait(timeout=45)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=3)
result = {
    "command": command, "outside_sandbox": True, "start_new_session": True,
    "timeout_seconds": 45, "timed_out": timed_out,
    "exit_code": process.returncode, "elapsed_seconds": time.monotonic() - started,
}
(folder / "r1-atuin-diagnostic-result.json").write_text(json.dumps(result, indent=2) + "\n")
print((folder / "r1-atuin-diagnostic.log").read_text())
print(json.dumps(result))
raise SystemExit(124 if timed_out else process.returncode)
