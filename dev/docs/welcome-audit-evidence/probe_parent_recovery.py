#!/usr/bin/env python3
"""Untimed independent W1 parent-recovery check with actual provider output."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from probe_baseline import BASHES, executable


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records = []
    with tempfile.TemporaryDirectory(prefix="welcome-parent-audit-") as temporary:
        root = Path(temporary).resolve()
        tree = root / "runtime"
        shutil.copytree(args.candidate, tree)
        library = tree / "shell" / "welcome.lib.sh"
        library.write_text(library.read_text() + '''
if [[ "${0##*/}" == bundled-runner.sh ]]; then
  unset -f remote_ssh_welcome_cpu_count
fi
''')
        for index, bash in enumerate(BASHES):
            for debug in ("0", "1"):
                home = root / f"home-{index}-{debug}"
                shims, temp = home / "bin", home / "tmp"
                shims.mkdir(parents=True)
                temp.mkdir()
                execution_log = home / "executions"
                executable(shims / "bash", '#!/bin/sh\nprintf "%s\\n" "$1" >>"$AUDIT_EXEC_LOG"\nexec "$AUDIT_REAL_BASH" "$@"\n')
                executable(shims / "hostname", '#!/bin/sh\ncase "$1" in -I) printf "203.0.113.9\\n";; *) printf "audit-host\\n";; esac\n')
                executable(shims / "sysctl", '#!/bin/sh\ncase "$2" in hw.ncpu) printf "8\\n";; hw.memsize) printf "17179869184\\n";; *) exit 1;; esac\n')
                user = home / ".config" / "remote-ssh" / "welcome.d" / "00-remote-ssh.sh"
                executable(user, '#!/usr/bin/awk -f\nBEGIN { print "actual-non-Bash-user" }\n')
                env = {"HOME": str(home), "XDG_CONFIG_HOME": str(home / ".config"),
                       "PATH": f"{shims}:/usr/bin:/bin", "TMPDIR": str(temp), "LC_ALL": "C",
                       "REMOTE_ENV_DIR": str(tree), "REMOTE_SSH_WELCOME_BANNER": "0",
                       "REMOTE_SSH_WELCOME_COLOR": "0", "REMOTE_SSH_UPDATE_CHECK": "0",
                       "REMOTE_SSH_GIT_SESSION_IDENTITY_STATUS": "ok",
                       "REMOTE_SSH_WELCOME_DEBUG": debug,
                       "AUDIT_EXEC_LOG": str(execution_log), "AUDIT_REAL_BASH": str(bash)}
                pair = {}
                for mode, setup in (("external-reference", "export BASH_ENV=/dev/null"),
                                    ("worker-preflight-fallback", ":")):
                    execution_log.write_text("")
                    command = 'set -e; . "$1/shell/welcome.lib.sh"; ' + setup + '; remote_ssh_welcome_run; printf "CALLER-NEXT\\n"'
                    result = subprocess.run([str(bash), "-c", command, "_", str(tree)],
                                            env=env, cwd=home, stdin=subprocess.DEVNULL,
                                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                            start_new_session=True, timeout=10, check=False)
                    pair[mode] = {"returncode": result.returncode, "stdout": result.stdout.decode(),
                                  "stderr": result.stderr.decode(),
                                  "executions": execution_log.read_text().splitlines()}
                before, after = pair["external-reference"], pair["worker-preflight-fallback"]
                record = {"bash": str(bash), "debug": debug, "runs": pair}
                records.append(record)
                assert before["returncode"] == after["returncode"] == 0, record
                assert before["stdout"] == after["stdout"], record
                assert str(after["stdout"]).count("host:    audit-host") == 1, record
                assert str(after["stdout"]).count("hw:      8 cpu / 16 GiB ram") == 1, record
                assert str(after["stdout"]).count("actual-non-Bash-user") == 1, record
                assert str(after["stdout"]).endswith("CALLER-NEXT\n"), record
                wrappers = [str(tree / "shell" / "welcome.d" / name)
                            for name in ("00-remote-ssh.sh", "10-hw.sh", "20-sw.sh")]
                assert before["executions"] == wrappers, record
                assert after["executions"] == [str(tree / "shell" / "welcome" / "bundled-runner.sh"), *wrappers], record
                assert before["stderr"] == "", record
                assert after["stderr"] == ("remote-ssh welcome: required function unavailable: remote_ssh_welcome_cpu_count\n" if debug == "1" else ""), record
                assert not list(temp.iterdir())
    args.output.write_text(json.dumps({"status": "PASS", "candidate": str(args.candidate),
                                      "records": records}, indent=2) + "\n")
    print(f"PASS {len(records)} independent parent recovery pairs")


if __name__ == "__main__":
    main()
