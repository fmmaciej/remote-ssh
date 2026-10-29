"""Untimed exec and Bash trace of the same frozen candidate and populated fixture."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from harness import BASHES, HERE, MARKER, SCRATCH, environment, executable, fingerprint


def main() -> None:
    repo = Path("/private/tmp/remote-ssh-welcome-candidate-r1")
    before = fingerprint(repo)
    records = []
    for version, bash in BASHES.items():
        for route in ("worker-and-user", "external-and-user"):
            root = SCRATCH / f"trace-{version}-{route}"
            if root.exists():
                shutil.rmtree(root)
            env = environment(repo, bash, "healthy", "remote-ssh-default-preseed", root)
            log = root / "executions"
            shim = Path(env["HOME"]) / "probes" / "bash"
            shim.unlink()
            executable(
                shim, '#!/bin/sh\nprintf "%s\\n" "$1" >>"$TRACE_LOG"\nexec "$TRACE_BASH" -x "$@"\n'
            )
            env.update({"TRACE_LOG": str(log), "TRACE_BASH": bash, "REMOTE_SSH_WELCOME_DEBUG": "1"})
            user = Path(env["XDG_CONFIG_HOME"]) / "remote-ssh" / "welcome.d" / "50-trace-user.sh"
            executable(user, '#!/usr/bin/env bash\nprintf "user-external\\n"\n')
            setup = "" if route == "worker-and-user" else "export BASH_ENV=/dev/null; "
            command = (
                '. "$1/shell/welcome.lib.sh"; '
                + setup
                + 'remote_ssh_welcome_run; printf "%s\\n" "$2"'
            )
            result = subprocess.run(
                [bash, "-c", command, "_", str(repo), MARKER],
                env=env,
                cwd=SCRATCH / "cwd",
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                start_new_session=True,
                check=False,
            )
            executions = log.read_text().splitlines()
            expected = (
                [str(repo / "shell" / "welcome" / "bundled-runner.sh"), str(user)]
                if route == "worker-and-user"
                else [
                    str(repo / "shell" / "welcome.d" / name)
                    for name in ("00-remote-ssh.sh", "10-hw.sh", "20-sw.sh")
                ]
                + [str(user)]
            )
            assert executions == expected, executions
            expected_screen = (
                (HERE / "screens" / f"{version}-healthy-isolated.txt")
                .read_text()
                .replace(MARKER, "user-external\n" + MARKER)
            )
            assert result.returncode == 0 and result.stdout == expected_screen
            stem = f"trace-{version}-{route}"
            (HERE / f"{stem}.stdout.txt").write_text(result.stdout)
            (HERE / f"{stem}.stderr.txt").write_text(result.stderr)
            records.append(
                {
                    "bash": version,
                    "route": route,
                    "args": [bash, "-c", command, "_", str(repo), MARKER],
                    "executions": executions,
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr_path": f"{stem}.stderr.txt",
                    "method": "env-Bash probe logs executable script then execs the selected real Bash with -x; ordinary timed samples use a direct bash symlink instead",
                }
            )
            shutil.rmtree(root)
    assert fingerprint(repo) == before
    (HERE / "execution-trace.json").write_text(
        json.dumps({"runtime_fingerprint": before["aggregate"], "records": records}, indent=2)
        + "\n"
    )


if __name__ == "__main__":
    main()
