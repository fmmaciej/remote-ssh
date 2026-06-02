from __future__ import annotations

from pathlib import Path

from conftest import IsolatedEnv, assert_ok, run_cmd, write_executable


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


def test_ssh_find_backend_indexes_ssh_config_and_bssh_records(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    ssh_dir = isolated_env.home / ".ssh"
    config_d = ssh_dir / "config.d"
    config_d.mkdir(parents=True)
    ssh_config = ssh_dir / "config"
    ssh_config.write_text(
        """\
Include config.d/*.conf
""",
        encoding="utf-8",
    )
    (config_d / "10-lab.conf").write_text(
        """\
Host lab-a
  HostName labbox
""",
        encoding="utf-8",
    )
    bssh_config = isolated_env.home / ".config" / "bssh" / "config.yaml"
    bssh_config.parent.mkdir(parents=True)
    bssh_config.write_text(
        """\
defaults:
  user: fallback
  port: 22
clusters:
  prod:
    user: deploy
    port: 2200
    nodes:
      - user1@web1:2221
      - web2:2222
      - name: gpu-a
        host: gpu-host
      - alias: npu-a
        host: 10.1.2.9
        user: root
        port: 2229
""",
        encoding="utf-8",
    )
    hosts_file = isolated_env.home / "hosts"
    hosts_file.write_text(
        """\
127.0.0.1 localhost
255.255.255.255 broadcasthost
10.1.2.3 labbox
10.1.2.4 gpu-host
10.1.2.5 web1
10.1.2.6 web2
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
        "SSH_FIND_SSH_CONFIG": str(ssh_config),
        "SSH_FIND_BSSH_CONFIG": str(bssh_config),
        "SSH_HOSTS_FILE": str(hosts_file),
    }
    result = run_cmd([repo_dir / "scripts" / "ssh_find.py"], env=env)

    assert_ok(result)
    assert result.stdout.splitlines() == [
        "gpu-a\t10.1.2.4\tdeploy\t.config/bssh/config.yaml\t2200\tdirect\tgpu-host",
        "lab-a\t10.1.2.3\talice\t.ssh/config\t2222\tssh-config\tlab-a",
        "npu-a\t10.1.2.9\troot\t.config/bssh/config.yaml\t2229\tdirect\t10.1.2.9",
        "web1\t10.1.2.5\tuser1\t.config/bssh/config.yaml\t2221\tdirect\tweb1",
        "web2\t10.1.2.6\tdeploy\t.config/bssh/config.yaml\t2222\tdirect\tweb2",
    ]


def test_ssh_find_opens_fzf_without_query(repo_dir: Path, isolated_env: IsolatedEnv) -> None:
    write_executable(
        isolated_env.bin_dir / "ssh_find_backend",
        """\
        #!/usr/bin/env bash
        printf 'lab-a\\t10.1.2.3\\talice\\t.ssh/config\\t2222\\tssh-config\\tlab-a\\n'
        printf 'gpu-a\\t10.1.2.4\\tdeploy\\t.config/bssh/config.yaml\\t2200\\tdirect\\tgpu-host\\n'
        """,
    )
    write_executable(
        isolated_env.bin_dir / "fzf",
        """
        #!/usr/bin/env bash
        printf '%s\\n' "$*" >"${FZF_ARGS_OUT:?}"
        sed -n '2p'
        """,
    )
    fzf_args_out = isolated_env.home / "fzf.args"
    env = isolated_env.env | {
        "FZF_ARGS_OUT": str(fzf_args_out),
        "SSH_FIND_BACKEND": str(isolated_env.bin_dir / "ssh_find_backend"),
    }

    result = run_cmd([repo_dir / "bin" / "ssh-find"], env=env)

    assert_ok(result)
    assert result.stdout.rstrip("\n") == (
        "gpu-a\t10.1.2.4\tdeploy\t.config/bssh/config.yaml\t2200\tdirect\tgpu-host"
    )
    fzf_args = fzf_args_out.read_text(encoding="utf-8")
    assert "--with-nth=1,2,3,4" in fzf_args
    assert "--nth=1,2,3,4" in fzf_args
    assert "--query=" not in fzf_args


def test_ssh_find_passes_query_to_fzf(repo_dir: Path, isolated_env: IsolatedEnv) -> None:
    write_executable(
        isolated_env.bin_dir / "ssh_find_backend",
        """\
        #!/usr/bin/env bash
        printf 'lab-a\\t10.1.2.3\\talice\\t.ssh/config\\t2222\\tssh-config\\tlab-a\\n'
        """,
    )
    write_executable(
        isolated_env.bin_dir / "fzf",
        """
        #!/usr/bin/env bash
        printf '%s\\n' "$*" >"${FZF_ARGS_OUT:?}"
        sed -n '1p'
        """,
    )
    fzf_args_out = isolated_env.home / "fzf.args"
    env = isolated_env.env | {
        "FZF_ARGS_OUT": str(fzf_args_out),
        "SSH_FIND_BACKEND": str(isolated_env.bin_dir / "ssh_find_backend"),
    }

    result = run_cmd([repo_dir / "bin" / "ssh-find", "10.1"], env=env)

    assert_ok(result)
    assert "--query=10.1" in fzf_args_out.read_text(encoding="utf-8")
    assert result.stdout.rstrip("\n") == (
        "lab-a\t10.1.2.3\talice\t.ssh/config\t2222\tssh-config\tlab-a"
    )


def test_ssh_find_cancel_returns_fzf_status(repo_dir: Path, isolated_env: IsolatedEnv) -> None:
    write_executable(
        isolated_env.bin_dir / "ssh_find_backend",
        """\
        #!/usr/bin/env bash
        printf 'lab-a\\t10.1.2.3\\talice\\t.ssh/config\\t2222\\tssh-config\\tlab-a\\n'
        """,
    )
    write_executable(
        isolated_env.bin_dir / "fzf",
        """
        #!/usr/bin/env bash
        exit 130
        """,
    )
    env = isolated_env.env | {
        "SSH_FIND_BACKEND": str(isolated_env.bin_dir / "ssh_find_backend"),
    }

    result = run_cmd([repo_dir / "bin" / "ssh-find"], env=env)

    assert result.returncode == 130


def test_ssh_pick_connects_to_ssh_config_alias(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    write_executable(
        isolated_env.bin_dir / "ssh_find",
        """\
        #!/usr/bin/env bash
        printf '%s\\n' "$*" >"${SSH_FIND_ARGS_OUT:?}"
        printf 'lab-a\\t10.1.2.3\\talice\\t.ssh/config\\t2222\\tssh-config\\tlab-a\\n'
        """,
    )
    write_executable(
        isolated_env.bin_dir / "ssh",
        """\
        #!/usr/bin/env bash
        printf '%s\\n' "$*" >"${SSH_STUB_OUT:?}"
        """,
    )
    find_args_out = isolated_env.home / "ssh-find.args"
    out = isolated_env.home / "ssh.out"
    env = isolated_env.env | {
        "SSH_FIND_ARGS_OUT": str(find_args_out),
        "SSH_FIND_CMD": str(isolated_env.bin_dir / "ssh_find"),
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
            ssh-pick --query 10.1 uptime
            """,
            "_",
            repo_dir,
        ],
        cwd=repo_dir,
        env=env,
    )

    assert_ok(result)
    assert find_args_out.read_text(encoding="utf-8").rstrip("\n") == "10.1"
    assert out.read_text(encoding="utf-8").rstrip("\n") == "lab-a uptime"


def test_ssh_pick_connects_to_bssh_direct_target(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    write_executable(
        isolated_env.bin_dir / "ssh_find",
        """\
        #!/usr/bin/env bash
        printf 'gpu-a\\t10.1.2.4\\tdeploy\\t.config/bssh/config.yaml\\t2200\\tdirect\\tgpu-host\\n'
        """,
    )
    write_executable(
        isolated_env.bin_dir / "ssh",
        """\
        #!/usr/bin/env bash
        printf '%s\\n' "$*" >"${SSH_STUB_OUT:?}"
        """,
    )
    out = isolated_env.home / "ssh.out"
    env = isolated_env.env | {
        "SSH_FIND_CMD": str(isolated_env.bin_dir / "ssh_find"),
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
            ssh-pick -- uptime
            """,
            "_",
            repo_dir,
        ],
        cwd=repo_dir,
        env=env,
    )

    assert_ok(result)
    assert out.read_text(encoding="utf-8").rstrip("\n") == "-p 2200 deploy@gpu-host uptime"


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
