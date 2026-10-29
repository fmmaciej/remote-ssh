"""Record the pre-existing fresh-executable environment boundary, without timing."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess

from harness import BASHES, MARKER, SCRATCH, environment

CASES = {
    "ordinary": "",
    "strict": "set -euo pipefail",
    "private_banner": "REMOTE_SSH_WELCOME_BANNER=0",
    "exported_banner": "export REMOTE_SSH_WELCOME_BANNER=0",
    "private_columns": "export -n COLUMNS; COLUMNS=30",
    "exported_columns": "export COLUMNS=30",
    "narrow_columns": "export COLUMNS=60",
    "color": "export REMOTE_SSH_WELCOME_COLOR=1",
    "private_no_color": "export REMOTE_SSH_WELCOME_COLOR=1; NO_COLOR=1",
    "exported_no_color": "export REMOTE_SSH_WELCOME_COLOR=1; export NO_COLOR=1",
    "private_provider": "hostname() { printf 'private-provider\\n'; }; REMOTE_SSH_STATUS_LIB_LOADED=1",
    "exported_provider": "hostname() { printf 'exported-provider\\n'; }; export -f hostname",
    "empty_bash_env": "export BASH_ENV=",
    "nonempty_bash_env": 'export BASH_ENV="$3"',
    "exported_shellopts": "set -e; shopt -u nullglob; export SHELLOPTS",
    "exported_bashopts": "set -e; shopt -u nullglob; if ((BASH_VERSINFO[0] > 3)); then export BASHOPTS; fi",
    "caller_state": "IFS=:; trap ':' USR1; private=preserved; shopt -s nocasematch",
    "debug": "export REMOTE_SSH_WELCOME_DEBUG=1",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo")
    parser.add_argument("out")
    args = parser.parse_args()
    from pathlib import Path

    repo = Path(args.repo).resolve()
    rows = []
    for version, bash in BASHES.items():
        for fixture in ("healthy", "actionable"):
            for name, setup in CASES.items():
                root = SCRATCH / f"compatibility-{version}-{fixture}-{name}"
                if root.exists():
                    shutil.rmtree(root)
                env = environment(repo, bash, fixture, "remote-ssh-default-preseed", root)
                hook = root / "bash-env"
                hook.write_text('printf "HOOK:%s\\n" "${0##*/}"\n')
                command = (
                    '. "$1/shell/welcome.lib.sh"\n'
                    + setup
                    + '\nremote_ssh_welcome_run\nprintf "%s\\n" "$2"\n'
                )
                result = subprocess.run(
                    [bash, "-c", command, "_", str(repo), MARKER, str(hook)],
                    env=env,
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    text=True,
                    start_new_session=True,
                    check=False,
                )
                rows.append(
                    {
                        "bash": version,
                        "fixture": fixture,
                        "case": name,
                        "setup": setup,
                        "returncode": result.returncode,
                        "stdout": result.stdout.replace(str(repo), "<RUNTIME>"),
                        "stderr": result.stderr.replace(str(repo), "<RUNTIME>"),
                    }
                )
                shutil.rmtree(root)
    Path(args.out).write_text(json.dumps(rows, indent=2) + "\n")


if __name__ == "__main__":
    main()
