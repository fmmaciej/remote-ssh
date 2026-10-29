"""Bounded offline focused check; project uv Python, no inherited pytest filters."""
from __future__ import annotations

import json
import os
import signal
import subprocess
import time
from pathlib import Path

root = Path(__file__).resolve().parents[3]
out = Path(__file__).resolve().parent
name = os.environ.get("SHELL_CHECK_NAME", "focused-first")
command = [
    "uv", "run", "--project", str(root / "dev"), "pytest", "-vv", "-ra",
    "dev/tests/test_shell_command.py", "dev/tests/test_entrypoint.py",
    "dev/tests/test_install_cli.py", "dev/tests/test_post_install.py",
    "dev/tests/test_guide.py", "dev/tests/test_runme.py", "dev/tests/test_rc_flow.py",
]
env = dict(os.environ)
for key in list(env):
    if key.startswith(("REMOTE_", "BASH_FUNC_", "PYTEST_")) or key in (
        "BASH_ENV", "ENV", "SHELLOPTS", "BASHOPTS", "CDPATH", "ZDOTDIR",
    ):
        env.pop(key, None)
env.update(UV_OFFLINE="1", UV_CACHE_DIR="/tmp/remote-ssh-uv-cache", PYTHONUNBUFFERED="1", PYTHONDONTWRITEBYTECODE="1")
started = time.monotonic()
with (out / (name + ".log")).open("wb") as log:
    proc = subprocess.Popen(command, cwd=root, env=env, stdin=subprocess.DEVNULL,
                            stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    timeout = False
    try:
        code = proc.wait(timeout=240)
    except subprocess.TimeoutExpired:
        timeout = True
        os.killpg(proc.pid, signal.SIGTERM)
        try:
            code = proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            code = proc.wait(timeout=5)
result = dict(command=command, exit_code=code, timeout=timeout, elapsed_seconds=time.monotonic()-started,
              supervisor_pid=os.getpid(), child_pid=proc.pid, offline=True, closed_stdin=True, fresh_session=True)
(out / (name + "-result.json")).write_text(json.dumps(result, indent=2)+"\n")
print(json.dumps(result), flush=True)
raise SystemExit(code if code >= 0 else 1)
