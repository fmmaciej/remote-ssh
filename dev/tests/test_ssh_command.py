from __future__ import annotations

from pathlib import Path

from conftest import (
    IsolatedEnv,
    assert_failed,
    assert_ok,
    copy_repo_for_git_setup,
    git_config,
    require_git,
    run_remote_ssh,
    run_setup,
    run_ssh_setup,
    write_executable,
    write_fake_ssh_add,
)


def test_remote_ssh_ssh_usage_and_unknown_command(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    result = run_remote_ssh(repo_dir, ["ssh", "--help"], env=isolated_env.env)
    assert_ok(result)
    assert "Usage: remote-ssh ssh <command> [args]" in result.stdout
    assert "setup" in result.stdout
    assert "status [host]" in result.stdout

    result = run_remote_ssh(repo_dir, ["ssh", "wat"], env=isolated_env.env)
    assert_failed(result)
    assert "Unknown remote-ssh ssh command: wat" in result.stderr


def test_remote_ssh_ssh_setup_creates_local_config_and_include_once(
    repo_dir: Path,
    tmp_path: Path,
    isolated_env: IsolatedEnv,
) -> None:
    repo_copy = copy_repo_for_git_setup(repo_dir, tmp_path)
    ssh_config_local = repo_copy / "dots" / "ssh" / "config.local"
    ssh_config_local.unlink(missing_ok=True)
    ssh_config = isolated_env.home / ".ssh" / "config"
    ssh_config.parent.mkdir(parents=True)
    ssh_config.write_text("Host existing\n  HostName example.com\n", encoding="utf-8")

    result = run_ssh_setup(repo_copy, env=isolated_env.env)
    assert_ok(result)
    result = run_ssh_setup(repo_copy, env=isolated_env.env)
    assert_ok(result)

    local_config = ssh_config_local.read_text(encoding="utf-8")
    assert "Host github.com-myuser\n" in local_config
    assert "  IdentitiesOnly no\n" in local_config
    assert oct(ssh_config.parent.stat().st_mode & 0o777)[2:] == "700"
    assert oct(ssh_config.stat().st_mode & 0o777)[2:] == "600"
    assert ssh_config.read_text(encoding="utf-8") == (
        f"Include {ssh_config_local}\n"
        "\n"
        "Host existing\n"
        "  HostName example.com\n"
    )


def test_remote_ssh_setup_runs_ssh_and_git_setup_idempotently(
    repo_dir: Path,
    tmp_path: Path,
    isolated_env: IsolatedEnv,
) -> None:
    require_git()
    repo_copy = copy_repo_for_git_setup(repo_dir, tmp_path)
    user_local = repo_copy / "dots" / "git" / "user.local"
    ssh_config_local = repo_copy / "dots" / "ssh" / "config.local"
    user_local.unlink(missing_ok=True)
    ssh_config_local.unlink(missing_ok=True)

    result = run_setup(repo_copy, env=isolated_env.env)
    assert_ok(result)
    result = run_setup(repo_copy, env=isolated_env.env)
    assert_ok(result)

    assert user_local.exists()
    assert ssh_config_local.exists()
    assert "==> remote-ssh ssh setup" in result.stdout
    assert "==> remote-ssh git setup" in result.stdout
    assert "remote-ssh setup complete." in result.stdout

    include = git_config(["--global", "--get-all", "include.path"], env=isolated_env.env)
    assert_ok(include)
    assert include.stdout.rstrip("\n") == str(repo_copy / "dots" / "git" / "config.base")

    ssh_config = isolated_env.home / ".ssh" / "config"
    assert ssh_config.read_text(encoding="utf-8").count(f"Include {ssh_config_local}") == 1


def test_remote_ssh_ssh_status_reports_config_and_agent_without_host(
    repo_dir: Path,
    tmp_path: Path,
    isolated_env: IsolatedEnv,
) -> None:
    repo_copy = copy_repo_for_git_setup(repo_dir, tmp_path)
    write_fake_ssh_add(isolated_env.bin_dir, "256 SHA256:testkey forwarded-key (ED25519)")
    result = run_ssh_setup(repo_copy, env=isolated_env.env)
    assert_ok(result)
    env = isolated_env.env | {"SSH_AUTH_SOCK": str(isolated_env.home / "agent.sock")}

    result = run_remote_ssh(repo_copy, ["ssh", "status"], env=env)

    assert_ok(result)
    output = result.stdout
    assert "remote-ssh ssh status" in output
    assert f"  home config:       {isolated_env.home / '.ssh' / 'config'} [readable]" in output
    assert f"  include:           Include {repo_copy / 'dots' / 'ssh' / 'config.local'}" in output
    assert "  include status:    present" in output
    assert f"  local config:      {repo_copy / 'dots' / 'ssh' / 'config.local'} [readable]" in output
    assert f"  SSH_AUTH_SOCK:     {isolated_env.home / 'agent.sock'}" in output
    assert "  key:              256 SHA256:testkey forwarded-key (ED25519)" in output
    assert "  ssh config:        ok" in output
    assert "  ssh agent:         ok" in output
    assert "  [none]" in output


def test_remote_ssh_ssh_status_resolves_host_without_auth(
    repo_dir: Path,
    tmp_path: Path,
    isolated_env: IsolatedEnv,
) -> None:
    repo_copy = copy_repo_for_git_setup(repo_dir, tmp_path)
    args_path = isolated_env.home / "ssh-args.txt"
    write_fake_ssh_add(isolated_env.bin_dir, "256 SHA256:testkey forwarded-key (ED25519)")
    write_executable(
        isolated_env.bin_dir / "ssh",
        """
        #!/usr/bin/env bash
        printf '%s\\n' "$*" >"$FAKE_SSH_ARGS"
        if [[ "$1" == "-G" && "$2" == "github.com-myuser" ]]; then
          cat <<'EOF'
        hostname github.com
        user git
        port 2222
        identityfile ~/.ssh/id_ed25519
        proxyjump jump.example
        EOF
          exit 0
        fi
        printf 'unexpected ssh args: %s\\n' "$*" >&2
        exit 99
        """,
    )
    result = run_ssh_setup(repo_copy, env=isolated_env.env)
    assert_ok(result)
    env = isolated_env.env | {
        "FAKE_SSH_ARGS": str(args_path),
        "SSH_AUTH_SOCK": str(isolated_env.home / "agent.sock"),
    }

    result = run_remote_ssh(repo_copy, ["ssh", "status", "github.com-myuser"], env=env)

    assert_ok(result)
    output = result.stdout
    assert args_path.read_text(encoding="utf-8").strip() == "-G github.com-myuser"
    assert "git@github.com-myuser" not in output
    assert "  command:           ssh -G github.com-myuser" in output
    assert "  status:            ok" in output
    assert "  hostname:          github.com" in output
    assert "  user:              git" in output
    assert "  port:              2222" in output
    assert "  identityfile:      ~/.ssh/id_ed25519" in output
    assert "  proxyjump:         jump.example" in output
