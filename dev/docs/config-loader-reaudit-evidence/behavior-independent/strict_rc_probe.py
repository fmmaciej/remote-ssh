#!/usr/bin/env python3
"""Locate the shared strict-rc failure using frozen R0 integration trees."""

import argparse
import base64
import json
from pathlib import Path
import sys
import tempfile

sys.dont_write_bytecode = True
import behavior_probe as probe


parser = argparse.ArgumentParser()
parser.add_argument("--integration-evidence", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
evidence = json.loads(args.integration_evidence.read_text())
trees = {version: Path(evidence["workspace"]) / version for version in ("baseline", "current")}
workspace = Path(tempfile.mkdtemp(prefix="config-reaudit-strict-rc-", dir="/private/tmp"))
item = probe.case(
    "strict-rc-trace",
    b"REMOTE_SSH_WELCOME_USER=0\n",
    script='export REMOTE_SSH_WELCOME=0 REMOTE_SSH_UPDATE_CHECK=0; set -x; . "$probe_root/shell/rc.sh"; printf "RC-SURVIVED\\0"',
)
records = []
for bash in probe.BASHES:
    record = probe.run_case(workspace, trees, bash, "strict", item)
    for result in record["results"].values():
        stderr = base64.b64decode(result.pop("stderr_b64")).decode()
        result["stderr_tail"] = stderr.splitlines()[-45:]
    records.append(record)
args.output.write_text(json.dumps({"baseline_commit": evidence["baseline_commit"], "source_sha256": evidence["source_sha256"], "records": records}, indent=2) + "\n")
for record in records:
    for version, result in record["results"].items():
        print(record["bash"], version, "status", result["status"])
        print("\n".join(result["stderr_tail"][-12:]))
