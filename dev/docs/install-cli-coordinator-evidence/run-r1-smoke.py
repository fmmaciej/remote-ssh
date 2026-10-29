"""Run the complete approved verification in a fresh session; record evidence."""

import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

root = Path.cwd()
folder = root / "dev/docs/install-cli-coordinator-evidence"
source_manifest = root / "dev/docs/install-cli-implementation-evidence/r1/final/source-hashes.json"
expected = json.loads(source_manifest.read_text())


def fingerprint():
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in expected}


before = fingerprint()
if before != expected:
    raise SystemExit("R1 source fingerprint mismatch before smoke; not started")
command = ["just", "smoke"]
env = os.environ.copy()
env["UV_OFFLINE"] = "1"
removed = ["PYTEST_ADDOPTS", "BASH_ENV", "ENV", "REMOTE_ENV_DIR"]
for name in removed:
    env.pop(name, None)
started = time.monotonic()
print("Final R1 source freeze verified; starting complete just smoke in a fresh session.", flush=True)
with (folder / "r1-smoke.log").open("w") as logfile:
    result = subprocess.run(
        command, cwd=root, env=env, stdout=logfile, stderr=subprocess.STDOUT,
        text=True, start_new_session=True, timeout=1200,
    )
after = fingerprint()
metadata = {
    "command": command,
    "cwd": str(root),
    "exit_code": result.returncode,
    "elapsed_seconds": time.monotonic() - started,
    "outside_sandbox": True,
    "start_new_session": True,
    "environment_overrides": {"UV_OFFLINE": "1"},
    "environment_removed": removed,
    "source_manifest": str(source_manifest.relative_to(root)),
    "source_hashes_before": before,
    "source_hashes_after": after,
    "hashes_match": before == after == expected,
}
(folder / "r1-smoke-result.json").write_text(json.dumps(metadata, indent=2) + "\n")
print("\n".join((folder / "r1-smoke.log").read_text().splitlines()[-35:]))
print("Source fingerprints unchanged:", metadata["hashes_match"])
raise SystemExit(result.returncode if metadata["hashes_match"] else 2)
