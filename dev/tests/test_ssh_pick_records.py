from __future__ import annotations

import json
import shlex
import shutil
import sys
from pathlib import Path

import pytest
from conftest import IsolatedEnv, assert_ok, run_cmd, write_executable


@pytest.mark.parametrize("user,port", [("", ""), ("alice", ""), ("", "2200")])
def test_ssh_pick_preserves_empty_columns(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str, user: str, port: str
) -> None:
    record = f"lab\t192.0.2.1\t{user}\t.config/bssh/config.yaml\t{port}\tdirect\t192.0.2.1"
    script = """
        set -euo pipefail
        . "$1/lib/guards.sh"
        . "$1/shell/rc.d/30-ssh-pick.sh"
        finder() { printf '%s\n' "$RECORD"; }
        ssh() { printf '%s\n' "$@"; }
        SSH_FIND_CMD=finder
        ssh-pick -- printf '%s' 'argument with spaces'
    """
    result = run_cmd(
        [runtime_bash, "-c", script, "_", repo_dir], env=isolated_env.env | {"RECORD": record}
    )
    assert_ok(result)
    expected = (["-p", port] if port else []) + [
        f"{user}@192.0.2.1" if user else "192.0.2.1",
        "printf",
        "%s",
        "argument with spaces",
    ]
    assert result.stdout.splitlines() == expected


def test_ssh_pick_uses_config_selected_by_backend(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str
) -> None:
    real_ssh = shutil.which("ssh")
    assert real_ssh
    config = isolated_env.home / "config with spaces"
    config.write_text("Host lab\n  HostName 192.0.2.17\n  User alice\n  Port 2200\n")
    (isolated_env.bin_dir / "bash").symlink_to(runtime_bash)
    # -G is the real offline OpenSSH resolver; a connection only records argv.
    write_executable(
        isolated_env.bin_dir / "ssh",
        f"""#!/bin/sh
        if [ "$1" = -G ]; then exec {shlex.quote(real_ssh)} "$@"; fi
        printf '%s\\n' "$@"
    """,
    )
    write_executable(isolated_env.bin_dir / "fzf", "#!/bin/sh\ncat\n")
    env = isolated_env.env | {
        "PATH": f"{isolated_env.bin_dir}:{repo_dir / 'bin'}:/usr/bin:/bin",
        "SSH_FIND_SSH_CONFIG": str(config),
        "SSH_FIND_BSSH_CONFIG": str(config.parent / "absent"),
    }
    # Use the same current Python interpreter that runs the test suite.
    backend = isolated_env.bin_dir / "backend"
    write_executable(
        backend,
        f"#!/bin/sh\nexec {shlex.quote(sys.executable)} {shlex.quote(str(repo_dir / 'scripts/ssh_find.py'))}\n",
    )
    env["SSH_FIND_BACKEND"] = str(backend)
    result = run_cmd(
        [
            runtime_bash,
            "-c",
            """
        . "$1/lib/guards.sh"
        . "$1/shell/rc.d/30-ssh-pick.sh"
        ssh-pick -- uptime
        """,
            "_",
            repo_dir,
        ],
        env=env,
    )
    assert_ok(result)
    assert result.stdout.splitlines() == ["-F", str(config.resolve()), "lab", "uptime"]


@pytest.mark.parametrize(
    "selection",
    ["default", "empty", "primary", "fallback", "precedence", "empty-primary", "explicit-default"],
)
def test_ssh_pick_config_selection_matches_resolution(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str, selection: str
) -> None:
    default = isolated_env.home / ".ssh/config"
    custom = isolated_env.home / "config with spaces"
    fallback = isolated_env.home / "fallback config"
    default.parent.mkdir()
    for config in (default, custom, fallback):
        config.write_text("Host lab\n  HostName 192.0.2.17\n")
    log = isolated_env.home / "ssh.jsonl"
    record = isolated_env.home / "selected-record"
    (isolated_env.bin_dir / "bash").symlink_to(runtime_bash)
    # Model a system-wide port that is unavailable when -F is passed. Never
    # consult the real account's home or system SSH config in default mode.
    write_executable(
        isolated_env.bin_dir / "ssh",
        f"""#!{sys.executable}
import json
import os
import sys
with open(os.environ['SSH_LOG'], 'a') as output:
    output.write(json.dumps(sys.argv[1:]) + '\\n')
port = '2222' if '-F' in sys.argv[1:] else '2201'
if sys.argv[1] == '-G':
    print('hostname 192.0.2.17\\nuser alice\\nport ' + port)
else:
    print('connected-port=' + port)
""",
    )
    write_executable(isolated_env.bin_dir / "fzf", '#!/bin/sh\ntee "$SELECTED_RECORD"\n')
    backend = isolated_env.bin_dir / "backend"
    write_executable(
        backend,
        f"#!/bin/sh\nexec {shlex.quote(sys.executable)} {shlex.quote(str(repo_dir / 'scripts/ssh_find.py'))}\n",
    )
    env = isolated_env.env | {
        "PATH": f"{isolated_env.bin_dir}:{repo_dir / 'bin'}:/usr/bin:/bin",
        "SSH_FIND_BACKEND": str(backend),
        "SSH_FIND_BSSH_CONFIG": str(isolated_env.home / "absent"),
        "SSH_HOSTS_FILE": str(isolated_env.home / "absent"),
        "SSH_LOG": str(log),
        "SELECTED_RECORD": str(record),
    }
    for key in ("SSH_FIND_SSH_CONFIG", "SSH_CONFIG"):
        env.pop(key, None)
    override: Path | None = None
    if selection == "empty":
        env.update(SSH_FIND_SSH_CONFIG="", SSH_CONFIG="")
    elif selection == "primary":
        env["SSH_FIND_SSH_CONFIG"] = str(custom)
        override = custom
    elif selection == "fallback":
        env["SSH_CONFIG"] = str(fallback)
        override = fallback
    elif selection == "precedence":
        env.update(SSH_FIND_SSH_CONFIG=str(custom), SSH_CONFIG=str(fallback))
        override = custom
    elif selection == "empty-primary":
        env.update(SSH_FIND_SSH_CONFIG="", SSH_CONFIG=str(fallback))
        override = fallback
    elif selection == "explicit-default":
        env["SSH_FIND_SSH_CONFIG"] = str(default)
        override = default
    result = run_cmd(
        [
            runtime_bash,
            "-c",
            """
        set -euo pipefail
        . "$1/lib/guards.sh"
        . "$1/shell/rc.d/30-ssh-pick.sh"
        ssh-pick -- printf '%s' 'argument with spaces'
        """,
            "_",
            repo_dir,
        ],
        env=env,
    )
    assert_ok(result)
    config_args = ["-F", str(override.resolve())] if override else []
    assert [json.loads(line) for line in log.read_text().splitlines()] == [
        ["-G", *config_args, "lab"],
        [*config_args, "lab", "printf", "%s", "argument with spaces"],
    ]
    port = "2222" if override else "2201"
    fields = ["lab", "192.0.2.17", "alice", ".ssh/config", port, "ssh-config", "lab"]
    if override:
        fields.append(str(override.resolve()))
    assert record.read_text().rstrip("\n").split("\t") == fields
    assert result.stdout.strip() == f"connected-port={port}"
