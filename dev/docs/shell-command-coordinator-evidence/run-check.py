"""Offline check supervisor; capture descendant identities before cleanup."""
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

root = Path(__file__).resolve().parents[3]
folder = Path(__file__).resolve().parent
name = sys.argv[1]
assert name in ("focused", "focused-rerun", "focused-final", "smoke")
command = ["just", "smoke"] if name == "smoke" else [
    "uv", "run", "--offline", "--project", "dev", "pytest", "-vv", "-ra",
    *["dev/tests/test_" + part + ".py" for part in (
        "shell_command", "entrypoint", "install_cli", "post_install", "guide", "runme", "rc_flow")],
]
protected = json.loads((root / "dev/docs/shell-command-planning-evidence/protected-before-implementation.json").read_text())
paths = list(protected["sha256"]) + protected["owned_source_paths"]

def hashes():
    return {p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in paths}

def processes():
    output = subprocess.check_output(["/bin/ps", "-axo", "pid=,ppid=,lstart="], text=True)
    return {int(p): (int(parent), birth) for p, parent, birth in
            (line.split(None, 2) for line in output.splitlines())}

before = hashes()
assert all(before[p] == h for p, h in protected["sha256"].items()), "protected baseline changed"
env = dict(os.environ)
removed = []
for key in list(env):
    if key.startswith(("REMOTE_", "BASH_FUNC_", "PYTEST_")) or key in (
        "BASH_ENV", "ENV", "SHELLOPTS", "BASHOPTS", "CDPATH", "ZDOTDIR"):
        removed.append(key)
        env.pop(key)
env.update(UV_OFFLINE="1", UV_CACHE_DIR="/tmp/remote-ssh-uv-cache", PYTHONUNBUFFERED="1", PYTHONDONTWRITEBYTECODE="1")
started = time.monotonic()
owned = {}
timeout = False
limit = 900 if name == "smoke" else 300
with (folder / (name + ".log")).open("wb") as log:
    proc = subprocess.Popen(command, cwd=root, env=env, stdin=subprocess.DEVNULL,
                            stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    while proc.poll() is None:
        rows = processes()
        parents = {proc.pid} | set(owned)
        while True:
            added = {pid: birth for pid, (ppid, birth) in rows.items() if ppid in parents and pid not in parents}
            if not added:
                break
            owned.update(added)
            parents.update(added)
        if time.monotonic() - started > limit:
            timeout = True
            break
        time.sleep(0.2)
    # Check birth identities to avoid touching a reused PID. Include separate
    # foreground process groups created by interactive job-control shells.
    survivors = []
    for sig in (signal.SIGTERM, signal.SIGKILL):
        rows = processes()
        survivors = [pid for pid, birth in owned.items() if pid in rows and rows[pid][1] == birth]
        for pid in survivors:
            try:
                os.kill(pid, sig)
            except ProcessLookupError:
                pass
        if proc.poll() is None:
            proc.send_signal(sig)
        if survivors or proc.poll() is None:
            time.sleep(0.5)
    code = proc.wait(timeout=5)
after = hashes()
rows = processes()
survivors = [pid for pid, birth in owned.items() if pid in rows and rows[pid][1] == birth]
result = dict(command=command, exit_code=code, timed_out=timeout, timeout_seconds=limit,
              elapsed_seconds=time.monotonic()-started, outside_sandbox=True,
              supervisor_python=sys.executable, child_pid=proc.pid, stdin="DEVNULL",
              start_new_session=True, offline=True, environment_removed=removed,
              source_hashes_before=before, source_hashes_after=after, hashes_match=before == after,
              tracked_descendants=len(owned), survivors=survivors)
(folder / (name + "-result.json")).write_text(json.dumps(result, indent=2)+"\n")
print("\n".join((folder / (name + ".log")).read_text().splitlines()[-25:]))
print(json.dumps({k:v for k,v in result.items() if not k.startswith("source_hashes")}))
raise SystemExit(124 if timeout else code if before == after and not survivors else 2)
