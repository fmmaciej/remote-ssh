#!/usr/bin/env python3
"""R1 current-only fault injection: generic status 7, gate policy, no path I/O."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
import behavior_probe as probe


parser = argparse.ArgumentParser()
parser.add_argument("--repo", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
workspace = Path(tempfile.mkdtemp(prefix="config-reaudit-r1-fault-", dir="/private/tmp"))
tree = probe.snapshot(args.repo, workspace)["current"]
records = []
for bash in probe.BASHES:
    for strict in (False, True):
        for gate in ("on", "off"):
            for operation in ("load", "raw", "gated"):
                name = f"{bash.replace('/', '_')}-{strict}-{gate}-{operation}"
                home = workspace / "runs" / name
                home.mkdir(parents=True)
                marker = home / "path-resolved"
                command = {
                    "load": "remote_ssh_config_load",
                    "raw": "remote_ssh_config_file_value_raw REMOTE_SSH_WELCOME_USER",
                    "gated": "remote_ssh_config_file_value REMOTE_SSH_WELCOME_USER",
                }[operation]
                script = r'''
if [[ "$3" == strict ]]; then set -euo pipefail; fi
. "$1/shell/config.lib.sh"
probe_init_calls=0
probe_path_marker="$2"
remote_ssh_config_snapshot_init() { probe_init_calls=$((probe_init_calls + 1)); return 7; }
remote_ssh_config_file() { printf 'unexpected path resolution\n' >"$probe_path_marker"; return 1; }
REMOTE_SSH_WELCOME_USER=old
REMOTE_SSH_CONFIG_SOURCE_WELCOME_USER=config
REMOTE_SSH_CONFIG_LOADED_VALUE_WELCOME_USER=old
REMOTE_SSH_CONFIG="$4"
trap 'probe_exit=$?; printf "EXIT:%s:%s:%s:%s:%s\n" "$probe_exit" "$REMOTE_SSH_WELCOME_USER" "$REMOTE_SSH_CONFIG_SOURCE_WELCOME_USER" "$REMOTE_SSH_CONFIG_LOADED_VALUE_WELCOME_USER" "$probe_init_calls"' EXIT
''' + command + r'''
probe_return=$?
printf 'RETURN:%s\nREACHED\n' "$probe_return"
'''
                result = subprocess.run(
                    [bash, "--noprofile", "--norc", "-c", script, "_", str(tree), str(marker), "strict" if strict else "ordinary", gate],
                    env={"HOME": str(home), "PATH": "/usr/bin:/bin", "LC_ALL": "C"},
                    text=True, capture_output=True, timeout=10,
                )
                call_status = 0 if operation == "load" and gate == "off" else 1 if operation == "gated" and gate == "off" else 7
                process_status = call_status if strict and call_status else 0
                init_calls = 0 if operation == "gated" and gate == "off" else 1
                expected = [] if process_status else [f"RETURN:{call_status}", "REACHED"]
                expected += [f"EXIT:{process_status}:old:config:old:{init_calls}"]
                passed = result.returncode == process_status and result.stdout.splitlines() == expected and not marker.exists() and not result.stderr
                records.append({"bash": bash, "strict": strict, "gate": gate, "operation": operation, "status": result.returncode, "stdout": result.stdout, "stderr": result.stderr, "path_resolved": marker.exists(), "expected_status": process_status, "expected_lines": expected, "passed": passed})
                print(name, "PASS" if passed else "FAIL", flush=True)
payload = {"source_sha256": {relative: hashlib.sha256((tree / relative).read_bytes()).hexdigest() for relative in probe.CHANGED}, "records": records, "passed": sum(r["passed"] for r in records), "total": len(records)}
args.output.write_text(json.dumps(payload, indent=2) + "\n")
raise SystemExit(0 if all(r["passed"] for r in records) else 1)
