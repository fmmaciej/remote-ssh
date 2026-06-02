from __future__ import annotations

from pathlib import Path

from conftest import IsolatedEnv, assert_failed, assert_ok, run_cmd, write_executable


def test_ssh_hosts_parser(repo_dir: Path, isolated_env: IsolatedEnv) -> None:
    ssh_dir = isolated_env.home / ".ssh"
    config_d = ssh_dir / "config.d"
    config_d.mkdir(parents=True)
    (ssh_dir / "config").write_text(
        """\
Host direct
  HostName direct.example

Include config.d/*.conf

Host *
  User ignored
""",
        encoding="utf-8",
    )
    (config_d / "10-lab.conf").write_text(
        """\
Host lab-a lab-b
  HostName lab.example

Host *.wildcard
  HostName ignored.example
""",
        encoding="utf-8",
    )

    env = isolated_env.env | {"PYTHONDONTWRITEBYTECODE": "1"}
    result = run_cmd([repo_dir / "scripts" / "ssh_hosts.py"], env=env)

    assert_ok(result)
    assert result.stdout.rstrip("\n") == "direct\nlab-a\nlab-b"


def test_ssh_hosts_pick_format_includes_resolved_hosts_file_addresses(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    ssh_dir = isolated_env.home / ".ssh"
    ssh_dir.mkdir(parents=True)
    ssh_config = ssh_dir / "config"
    ssh_config.write_text(
        """\
Host lab-a
  HostName labbox
""",
        encoding="utf-8",
    )
    hosts_file = isolated_env.home / "hosts"
    hosts_file.write_text(
        """\
127.0.0.1 localhost
255.255.255.255 broadcasthost
10.1.2.3 labbox lab-a-hosts
""",
        encoding="utf-8",
    )
    write_executable(
        isolated_env.bin_dir / "ssh",
        """
        #!/usr/bin/env bash
        printf 'hostname labbox\\n'
        printf 'user alice\\n'
        printf 'port 2222\\n'
        """,
    )

    env = isolated_env.env | {
        "PYTHONDONTWRITEBYTECODE": "1",
        "SSH_CONFIG": str(ssh_config),
        "SSH_HOSTS_FILE": str(hosts_file),
    }
    result = run_cmd([repo_dir / "scripts" / "ssh_hosts.py", "--format", "pick"], env=env)

    assert_ok(result)
    assert result.stdout.splitlines() == [
        "lab-a\thostname=labbox\tip=10.1.2.3\tuser=alice\tport=2222",
        "lab-a-hosts\tip=10.1.2.3",
    ]


def test_ssh_pick_default_flow(repo_dir: Path, isolated_env: IsolatedEnv) -> None:
    ssh_dir = isolated_env.home / ".ssh"
    ssh_dir.mkdir(parents=True)
    (ssh_dir / "config").write_text(
        """\
Host devbox
  HostName devbox.example
""",
        encoding="utf-8",
    )
    write_executable(
        isolated_env.bin_dir / "fzf",
        """
        #!/usr/bin/env bash
        sed -n '/^devbox/p'
        """,
    )
    write_executable(
        isolated_env.bin_dir / "ssh",
        """
        #!/usr/bin/env bash
        printf '%s\\n' "$*" >"${SSH_STUB_OUT:?}"
        """,
    )
    out = isolated_env.home / "ssh.out"
    env = isolated_env.env | {"SSH_STUB_OUT": str(out)}

    result = run_cmd(
        [
            "bash",
            "-c",
            """
            set -euo pipefail
            . "$1/shell/env.sh"
            . "$1/shell/rc.d/30-ssh-pick.sh"
            ssh-pick -- true
            """,
            "_",
            repo_dir,
        ],
        cwd=repo_dir,
        env=env,
    )

    assert_ok(result)
    assert out.read_text(encoding="utf-8").rstrip("\n") == "devbox -- true"


def test_ssh_pick_query_selects_unique_ip_match(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    ssh_dir = isolated_env.home / ".ssh"
    ssh_dir.mkdir(parents=True)
    ssh_config = ssh_dir / "config"
    ssh_config.write_text(
        """\
Host lab-a
  HostName labbox
""",
        encoding="utf-8",
    )
    hosts_file = isolated_env.home / "hosts"
    hosts_file.write_text("10.1.2.3 labbox\n", encoding="utf-8")
    write_executable(
        isolated_env.bin_dir / "ssh",
        """
        #!/usr/bin/env bash
        if [[ "$1" == "-G" ]]; then
          printf 'hostname labbox\\n'
          printf 'user alice\\n'
          printf 'port 2222\\n'
          exit 0
        fi
        printf '%s\\n' "$*" >"${SSH_STUB_OUT:?}"
        """,
    )
    write_executable(
        isolated_env.bin_dir / "fzf",
        """
        #!/usr/bin/env bash
        printf 'fzf should not be called for a unique query match\\n' >&2
        exit 1
        """,
    )
    out = isolated_env.home / "ssh.out"
    env = isolated_env.env | {
        "SSH_HOSTS_FILE": str(hosts_file),
        "SSH_STUB_OUT": str(out),
    }

    result = run_cmd(
        [
            "bash",
            "-c",
            """
            set -euo pipefail
            . "$1/shell/env.sh"
            . "$1/shell/rc.d/30-ssh-pick.sh"
            ssh-pick --query 10.1.2.3
            """,
            "_",
            repo_dir,
        ],
        cwd=repo_dir,
        env=env,
    )

    assert_ok(result)
    assert out.read_text(encoding="utf-8").rstrip("\n") == "lab-a"


def test_ssh_pick_reports_parser_failure(repo_dir: Path, isolated_env: IsolatedEnv) -> None:
    result = run_cmd(
        [
            "bash",
            "-c",
            """
            set -euo pipefail
            . "$1/shell/env.sh"
            . "$1/shell/rc.d/30-ssh-pick.sh"
            SSH_HOSTS_CMD=false ssh-pick
            """,
            "_",
            repo_dir,
        ],
        cwd=repo_dir,
        env=isolated_env.env,
    )

    assert_failed(result)
    output = result.stdout + result.stderr
    assert "ssh-pick could not list SSH hosts" in output
    assert "requires python3" in output


def test_bssh_wrapper_uses_default_shared_config(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    write_executable(
        isolated_env.bin_dir / "bssh",
        """
        #!/usr/bin/env bash
        printf '%s\\n' "$*" >"${BSSH_STUB_OUT:?}"
        """,
    )
    out = isolated_env.home / "bssh.out"
    env = isolated_env.env | {"BSSH_STUB_OUT": str(out)}

    result = run_cmd(
        [
            "bash",
            "-c",
            """
            set -euo pipefail
            . "$1/shell/env.sh"
            . "$1/shell/rc.d/26-bssh.sh"
            bssh lab --plain
            """,
            "_",
            repo_dir,
        ],
        cwd=repo_dir,
        env=env,
    )

    assert_ok(result)
    default_config = isolated_env.home / ".ssh" / "config.d" / "00-all.conf"
    assert out.read_text(encoding="utf-8").rstrip("\n") == (
        f"--stream --ssh-config {default_config} lab --plain"
    )


def test_bssh_config_can_be_overridden_before_rc_load(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    custom_config = isolated_env.home / "custom-ssh.conf"
    result = run_cmd(
        [
            "bash",
            "-c",
            """
            set -euo pipefail
            . "$1/shell/env.sh"
            . "$1/shell/rc.d/26-bssh.sh"
            printf '%s\\n' "$BSSH_SSH_CONFIG"
            """,
            "_",
            repo_dir,
        ],
        cwd=repo_dir,
        env=isolated_env.env | {"BSSH_SSH_CONFIG": str(custom_config)},
    )

    assert_ok(result)
    assert result.stdout.rstrip("\n") == str(custom_config)


def test_bssh_ip_resolves_host_with_shared_config(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    write_executable(
        isolated_env.bin_dir / "ssh",
        """
        #!/usr/bin/env bash
        printf '%s\\n' "$*" >"${SSH_STUB_OUT:?}"
        printf 'hostname 10.1.2.3\\n'
        printf 'user alice\\n'
        printf 'port 2222\\n'
        """,
    )
    out = isolated_env.home / "ssh.out"
    env = isolated_env.env | {"SSH_STUB_OUT": str(out)}

    result = run_cmd(
        [
            "bash",
            "-c",
            """
            set -euo pipefail
            . "$1/shell/env.sh"
            . "$1/shell/rc.d/26-bssh.sh"
            bssh-ip lab-a
            """,
            "_",
            repo_dir,
        ],
        cwd=repo_dir,
        env=env,
    )

    assert_ok(result)
    default_config = isolated_env.home / ".ssh" / "config.d" / "00-all.conf"
    assert out.read_text(encoding="utf-8").rstrip("\n") == f"-G -F {default_config} lab-a"
    assert result.stdout.rstrip("\n") == "10.1.2.3  # user=alice port=2222"


def test_bssh_ip_without_host_returns_usage_without_exiting_shell(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    result = run_cmd(
        [
            "bash",
            "-c",
            """
            set -euo pipefail
            . "$1/shell/env.sh"
            . "$1/shell/rc.d/26-bssh.sh"
            set +e
            bssh-ip
            status=$?
            set -e
            printf 'status=%s\\n' "$status"
            printf 'alive\\n'
            """,
            "_",
            repo_dir,
        ],
        cwd=repo_dir,
        env=isolated_env.env,
    )

    assert_ok(result)
    assert result.stdout.splitlines() == ["status=2", "alive"]
    assert "usage: bssh-ip HOST" in result.stderr


def test_bssh_ip_returns_one_when_hostname_is_missing(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    write_executable(
        isolated_env.bin_dir / "ssh",
        """
        #!/usr/bin/env bash
        printf 'user alice\\n'
        """,
    )

    result = run_cmd(
        [
            "bash",
            "-c",
            """
            set -euo pipefail
            . "$1/shell/env.sh"
            . "$1/shell/rc.d/26-bssh.sh"
            set +e
            bssh-ip lab-a
            status=$?
            set -e
            printf 'status=%s\\n' "$status"
            """,
            "_",
            repo_dir,
        ],
        cwd=repo_dir,
        env=isolated_env.env,
    )

    assert_ok(result)
    assert result.stdout.rstrip("\n") == "status=1"
