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


def test_sshf_default_flow(repo_dir: Path, isolated_env: IsolatedEnv) -> None:
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
        sed -n '1p'
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
            . "$1/shell/rc.d/30-sshf.sh"
            sshf -- true
            """,
            "_",
            repo_dir,
        ],
        cwd=repo_dir,
        env=env,
    )

    assert_ok(result)
    assert out.read_text(encoding="utf-8").rstrip("\n") == "devbox -- true"


def test_sshf_reports_parser_failure(repo_dir: Path, isolated_env: IsolatedEnv) -> None:
    result = run_cmd(
        [
            "bash",
            "-c",
            """
            set -euo pipefail
            . "$1/shell/env.sh"
            . "$1/shell/rc.d/30-sshf.sh"
            SSH_HOSTS_CMD=false sshf
            """,
            "_",
            repo_dir,
        ],
        cwd=repo_dir,
        env=isolated_env.env,
    )

    assert_failed(result)
    output = result.stdout + result.stderr
    assert "sshf could not list SSH hosts" in output
    assert "requires python3" in output
