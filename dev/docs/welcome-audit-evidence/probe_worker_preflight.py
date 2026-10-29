#!/usr/bin/env python3
"""Untimed worker preflight fault injection in a disposable runtime copy."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from probe_baseline import BASHES


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records = []
    with tempfile.TemporaryDirectory(prefix="welcome-preflight-audit-") as temporary:
        root = Path(temporary)
        tree = root / "runtime"
        shutil.copytree(args.candidate, tree)
        # Preserve the faulted provider's fingerprint without copying its text
        # into the evidence. No worktree or frozen snapshot file is changed.
        missing = tree / "shell" / "welcome" / "hw.sh"
        removed_sha = hashlib.sha256(missing.read_bytes()).hexdigest()
        missing.unlink()
        for index, bash in enumerate(BASHES):
            home = root / f"home-{index}"
            home.mkdir()
            shims = home / "bin"
            shims.mkdir()
            (shims / "bash").symlink_to(bash)
            env = {
                "HOME": str(home), "XDG_CONFIG_HOME": str(home / ".config"),
                "PATH": f"{shims}:/usr/bin:/bin", "LC_ALL": "C",
                "REMOTE_ENV_DIR": str(tree), "REMOTE_SSH_WELCOME_BANNER": "0",
                "REMOTE_SSH_WELCOME_COLOR": "0", "REMOTE_SSH_WELCOME_USER": "0",
                "REMOTE_SSH_UPDATE_CHECK": "0",
                "REMOTE_SSH_GIT_SESSION_IDENTITY_STATUS": "ok",
            }
            command = [str(bash), str(tree / "shell" / "welcome" / "bundled-runner.sh"), "--",
                       *[str(tree / "shell" / "welcome.d" / module)
                         for module in ("00-remote-ssh.sh", "10-hw.sh", "20-sw.sh")]]
            result = subprocess.run(command, env=env, cwd=home, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, start_new_session=True, timeout=10,
                                    check=False)
            records.append({"bash": str(bash), "returncode": result.returncode,
                            "stdout": result.stdout.decode(), "stderr": result.stderr.decode(),
                            "expected_preflight_status": 125, "expected_stdout": "",
                            "preflight_contract_passes": result.returncode == 125 and result.stdout == b""})
    output = {"candidate": str(args.candidate), "fault": "remove shell/welcome/hw.sh from disposable copy",
              "removed_sha256": removed_sha, "records": records,
              "status": "PASS" if all(r["preflight_contract_passes"] for r in records) else "FAIL"}
    args.output.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
