"""Record an unfiltered full smoke retry with bounded process-group cleanup."""

import hashlib
import json
import os
import signal
import subprocess
import time
from pathlib import Path

root = Path.cwd()
folder = root / "dev/docs/install-cli-coordinator-evidence"
manifest = root / "dev/docs/install-cli-implementation-evidence/r1/final/source-hashes.json"
expected = json.loads(manifest.read_text())


def fingerprint():
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in expected}


before = fingerprint()
if before != expected:
    raise SystemExit("R1 source mismatch; no tests started")
env = os.environ.copy()
env.update(UV_OFFLINE="1", PYTHONUNBUFFERED="1")
removed = ["PYTEST_ADDOPTS", "BASH_ENV", "ENV", "REMOTE_ENV_DIR"]
for name in removed:
    env.pop(name, None)
command = ["just", "smoke"]
started = time.monotonic()
timed_out = False
print("Frozen R1 verified. Starting unfiltered full smoke using project Python.", flush=True)
with (folder / "r1-smoke-retry.log").open("w") as logfile:
    process = subprocess.Popen(
        command, cwd=root, env=env, stdin=subprocess.DEVNULL,
        stdout=logfile, stderr=subprocess.STDOUT, start_new_session=True,
    )
    try:
        process.wait(timeout=900)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=3)
after = fingerprint()
result = {
    "command": command,
    "exit_code": process.returncode,
    "timed_out": timed_out,
    "timeout_seconds": 900,
    "elapsed_seconds": time.monotonic() - started,
    "outside_sandbox": True,
    "start_new_session": True,
    "stdin": "DEVNULL",
    "environment_overrides": {"UV_OFFLINE": "1", "PYTHONUNBUFFERED": "1"},
    "environment_removed": removed,
    "launcher_python": os.sys.executable,
    "source_manifest": str(manifest.relative_to(root)),
    "source_hashes_before": before,
    "source_hashes_after": after,
    "hashes_match": before == after == expected,
}
(folder / "r1-smoke-retry-result.json").write_text(json.dumps(result, indent=2) + "\n")
print("\n".join((folder / "r1-smoke-retry.log").read_text().splitlines()[-35:]))
print("Source fingerprints unchanged:", result["hashes_match"])
raise SystemExit(124 if timed_out else process.returncode if result["hashes_match"] else 2)
