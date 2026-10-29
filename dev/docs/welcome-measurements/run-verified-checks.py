"""Run fixed verification commands without an inherited controlling terminal."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("probe", "smoke"))
    args = parser.parse_args()
    if args.mode == "probe":
        command = [
            str(REPO / "dev/.venv/bin/python"), "-m", "pytest", "-q",
            "dev/tests/test_history_backend.py::test_atuin_removal_and_reactivation_in_full_rc[/bin/bash-none]",
            "dev/tests/test_welcome.py::test_welcome_runner_is_standalone_without_remote_shell_dir",
            "dev/tests/test_welcome.py::test_welcome_runner_orders_bundled_and_user_modules",
        ]
    else:
        command = ["just", "smoke"]
    log_path = HERE / f"r1-detached-{args.mode}.log"
    metadata_path = log_path.with_suffix(".metadata.json")
    assert not log_path.exists() and not metadata_path.exists(), "preserve previous evidence"
    started = time.monotonic()
    with log_path.open("xb") as output:
        process = subprocess.Popen(
            command, cwd=REPO, stdin=subprocess.DEVNULL, stdout=output,
            stderr=subprocess.STDOUT, start_new_session=True,
        )
        while True:
            try:
                returncode = process.wait(timeout=30)
                break
            except subprocess.TimeoutExpired:
                elapsed = time.monotonic() - started
                tail = log_path.read_text(errors="replace").splitlines()[-3:]
                print(f"verification elapsed={elapsed:.0f}s; " + " | ".join(tail), flush=True)
                if elapsed >= 600:
                    os.killpg(process.pid, signal.SIGTERM)
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait(timeout=5)
                    raise TimeoutError("verification exceeded 600 seconds; process group stopped")
    payload = log_path.read_bytes()
    result = {
        "command": command,
        "start_new_session": True,
        "stdin": "/dev/null",
        "returncode": returncode,
        "elapsed_seconds": time.monotonic() - started,
        "raw_log": log_path.name,
        "raw_log_sha256": hashlib.sha256(payload).hexdigest(),
        "driver_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "runtime_test_freeze_sha256": hashlib.sha256(
            (HERE / "r1-runtime-tests-final-freeze.json").read_bytes()
        ).hexdigest(),
    }
    metadata_path.write_text(json.dumps(result, indent=2) + "\n")
    print("\n".join(payload.decode(errors="replace").splitlines()[-8:]), flush=True)
    print(json.dumps(result), flush=True)
    raise SystemExit(returncode)


if __name__ == "__main__":
    main()
