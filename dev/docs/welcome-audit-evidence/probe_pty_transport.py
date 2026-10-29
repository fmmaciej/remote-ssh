#!/usr/bin/env python3
"""Untimed independent controlling-terminal and redirected-stdout probe."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import pty
import select
import signal
import subprocess
import tarfile
import tempfile
import time

from probe_baseline import BASHES, PINNED, REPO, executable


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tree", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records = []
    with tempfile.TemporaryDirectory(prefix="welcome-pty-audit-") as temporary:
        root = Path(temporary)
        tree = args.tree.resolve() if args.tree else root / "baseline"
        if not args.tree:
            tree.mkdir()
            archive = subprocess.check_output(["git", "archive", PINNED], cwd=REPO)
            with tarfile.open(fileobj=io.BytesIO(archive)) as packed:
                packed.extractall(tree, filter="data")
        for bash_index, bash in enumerate(BASHES):
            for debug in ("0", "1"):
                fixture = root / f"bash-{bash_index}-{debug}"
                fixture.mkdir()
                modules = fixture / "shell" / "welcome.d"
                modules.mkdir(parents=True)
                executable(modules / "00-module", "#!/bin/sh\nif read value; then printf 'BAD-stdin\\n'; else printf 'eof\\n'; fi\nprintf ' \\\\hello\\rX\\n\\nlast'\nprintf 'module-stderr\\n' >&2\nexit 7\n")
                executable(modules / "10-after", "#!/bin/sh\nprintf 'sibling\\n'\n")
                stdout, stderr = fixture / "stdout", fixture / "stderr"
                shims = fixture / "bin"
                shims.mkdir()
                (shims / "bash").symlink_to(bash)
                temporary_files = fixture / "tmp"
                temporary_files.mkdir()
                env = {
                    "HOME": str(fixture), "XDG_CONFIG_HOME": str(fixture / "config"),
                    "PATH": f"{shims}:/usr/bin:/bin", "LC_ALL": "C",
                    "TERM": "xterm-256color", "TMPDIR": str(temporary_files),
                    "REMOTE_SHELL_DIR": str(fixture / "shell"),
                    "REMOTE_SSH_WELCOME_COLOR": "0", "REMOTE_SSH_WELCOME_USER": "0",
                    "REMOTE_SSH_WELCOME_DEBUG": debug,
                }
                command = '''exec >"$2" 2>"$3"
set -euo pipefail
. "$1/shell/welcome.lib.sh"
remote_ssh_welcome_run
printf 'input-ready\\n' >/dev/tty
read -r value
printf 'caller=%s\\n' "$value"
'''
                pid, terminal = pty.fork()
                if pid == 0:
                    os.chdir(fixture)
                    os.execve(str(bash), [str(bash), "--noprofile", "--norc", "-c", command,
                                          "_", str(tree), str(stdout), str(stderr)], env)
                output = bytearray()
                sent = False
                status = None
                deadline = time.monotonic() + 10
                try:
                    while time.monotonic() < deadline:
                        readable, _, _ = select.select([terminal], [], [], 0.05)
                        if readable:
                            try:
                                chunk = os.read(terminal, 4096)
                            except OSError:
                                chunk = b""
                            if chunk:
                                output.extend(chunk)
                            if not sent and b"input-ready\r\n" in output:
                                os.write(terminal, b"kept\n")
                                sent = True
                        if status is None:
                            waited, child_status = os.waitpid(pid, os.WNOHANG)
                            if waited:
                                status = child_status
                        if status is not None and not readable:
                            break
                        if status is not None and readable and not chunk:
                            break
                    if status is None:
                        os.kill(pid, signal.SIGKILL)
                        _, status = os.waitpid(pid, 0)
                finally:
                    os.close(terminal)
                record = {"bash": str(bash), "debug": debug,
                          "returncode": os.waitstatus_to_exitcode(status),
                          "terminal": output.decode(), "stdout": stdout.read_text(),
                          "stderr": stderr.read_text(), "input_sent_after_panel": sent}
                records.append(record)
                assert record["returncode"] == 0, record
                assert record["terminal"] == "eof\r\n \\hello\rX\r\n\r\nlast\r\nsibling\r\ninput-ready\r\nkept\r\n", record
                assert record["stdout"] == "caller=kept\n", record
                if debug == "0":
                    assert record["stderr"] == "", record
                else:
                    assert "module-stderr\n" in record["stderr"], record
                    assert "(exit 7)\n" in record["stderr"], record
                assert not list(temporary_files.iterdir())
    args.output.write_text(json.dumps({"status": "PASS", "baseline": PINNED,
                                      "tree": str(args.tree) if args.tree else "pinned git archive",
                                      "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                                      "records": records}, indent=2) + "\n")
    print(f"PASS {len(records)} untimed PTY probes; output: {args.output}")


if __name__ == "__main__":
    main()
