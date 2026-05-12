from __future__ import annotations

from pathlib import Path

from conftest import (
    IsolatedEnv,
    assert_ok,
    init_git_repo,
    require_git,
    run_cmd,
    run_remote_ssh,
    write_fake_ssh,
    write_fake_ssh_add,
)


def test_remote_ssh_git_status_reports_git_and_ssh_state(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    require_git()
    repo = init_git_repo(isolated_env.home / "repo", env=isolated_env.env)
    write_fake_ssh_add(isolated_env.bin_dir, "256 SHA256:testkey forwarded-key (ED25519)")
    write_fake_ssh(
        isolated_env.bin_dir,
        "Hi test-user! You've successfully authenticated, but GitHub does not provide shell access.",
        1,
    )
    for args in (
        ["user.name", "Test User"],
        ["user.email", "test@example.com"],
        ["user.useConfigOnly", "true"],
    ):
        result = run_cmd(["git", "config", *args], cwd=repo, env=isolated_env.env)
        assert_ok(result)
    result = run_cmd(
        ["git", "remote", "add", "origin", "git@github.com-myuser:fmmaciej/remote-ssh.git"],
        cwd=repo,
        env=isolated_env.env,
    )
    assert_ok(result)
    env = isolated_env.env | {"SSH_AUTH_SOCK": str(isolated_env.home / "agent.sock")}

    result = run_remote_ssh(repo_dir, ["git", "status"], cwd=repo, env=env)

    assert_ok(result)
    output = result.stdout
    assert "remote-ssh git status" in output
    assert "  user.name:         Test User " in output
    assert "  user.email:        test@example.com " in output
    assert "  user.useConfigOnly: true " in output
    assert "  origin:            git@github.com-myuser:fmmaciej/remote-ssh.git" in output
    assert "  ssh host:          github.com-myuser" in output
    assert f"  SSH_AUTH_SOCK:     {isolated_env.home / 'agent.sock'}" in output
    assert "  key:              256 SHA256:testkey forwarded-key (ED25519)" in output
    assert "  command:           ssh -T git@github.com-myuser" in output
    assert "  status:            ok" in output
    assert "  output:           Hi test-user!" in output
    assert "Diagnosis" in output
    assert "  ssh agent:         ok" in output
    assert "  ssh auth:          ok" in output
    assert "Next steps" in output
    assert "  [none]" in output


def test_remote_ssh_git_status_accepts_explicit_host_without_remote(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    require_git()
    repo = init_git_repo(isolated_env.home / "repo", env=isolated_env.env)
    write_fake_ssh_add(
        isolated_env.bin_dir,
        "Could not open a connection to your authentication agent.",
        2,
    )
    write_fake_ssh(isolated_env.bin_dir, "Permission denied (publickey).", 255)

    env = isolated_env.env.copy()
    env.pop("SSH_AUTH_SOCK", None)

    result = run_remote_ssh(
        repo_dir,
        ["git", "status", "github.com-myuser"],
        cwd=repo,
        env=env,
    )

    assert_ok(result)
    output = result.stdout
    assert "  origin:            [missing]" in output
    assert "  ssh host:          github.com-myuser" in output
    assert "  SSH_AUTH_SOCK:     [missing]" in output
    assert "  keys:              Could not open a connection to your authentication agent." in output
    assert "  status:            exit 255" in output
    assert "  ssh agent:         missing-sock" in output
    assert "  ssh auth:          denied-publickey" in output
    assert "  - Start or forward an SSH agent, then reopen this shell." in output
    assert "  - Fix the SSH agent first, then retry remote-ssh git status github.com-myuser." in output


def test_remote_ssh_git_status_reports_stale_agent_socket(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    require_git()
    repo = init_git_repo(isolated_env.home / "repo", env=isolated_env.env)
    write_fake_ssh_add(
        isolated_env.bin_dir,
        "Error connecting to agent: No such file or directory",
        2,
    )
    write_fake_ssh(isolated_env.bin_dir, "Permission denied (publickey).", 255)
    env = isolated_env.env | {"SSH_AUTH_SOCK": str(isolated_env.home / "missing-agent.sock")}

    result = run_remote_ssh(
        repo_dir,
        ["git", "status", "github.com-myuser"],
        cwd=repo,
        env=env,
    )

    assert_ok(result)
    output = result.stdout
    assert f"  SSH_AUTH_SOCK:     {isolated_env.home / 'missing-agent.sock'}" in output
    assert "  keys:              Error connecting to agent: No such file or directory" in output
    assert "  ssh agent:         stale-sock" in output
    assert "  ssh auth:          denied-publickey" in output
    assert (
        "  - SSH_AUTH_SOCK points to a dead socket; reconnect or refresh agent forwarding."
        in output
    )
    assert "  - Fix the SSH agent first, then retry remote-ssh git status github.com-myuser." in output


def test_remote_ssh_git_status_reports_agent_without_keys(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    require_git()
    repo = init_git_repo(isolated_env.home / "repo", env=isolated_env.env)
    write_fake_ssh_add(isolated_env.bin_dir, "The agent has no identities.", 1)
    write_fake_ssh(isolated_env.bin_dir, "Permission denied (publickey).", 255)
    env = isolated_env.env | {"SSH_AUTH_SOCK": str(isolated_env.home / "agent.sock")}

    result = run_remote_ssh(
        repo_dir,
        ["git", "status", "github.com-myuser"],
        cwd=repo,
        env=env,
    )

    assert_ok(result)
    output = result.stdout
    assert "  keys:              The agent has no identities." in output
    assert "  ssh agent:         no-keys" in output
    assert "  ssh auth:          denied-publickey" in output
    assert "  - Load a key with ssh-add, or check that your forwarded agent has identities." in output
    assert "  - Fix the SSH agent first, then retry remote-ssh git status github.com-myuser." in output


def test_remote_ssh_git_status_reports_publickey_denied_with_keys(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    require_git()
    repo = init_git_repo(isolated_env.home / "repo", env=isolated_env.env)
    write_fake_ssh_add(isolated_env.bin_dir, "256 SHA256:testkey forwarded-key (ED25519)")
    write_fake_ssh(isolated_env.bin_dir, "Permission denied (publickey).", 255)
    env = isolated_env.env | {"SSH_AUTH_SOCK": str(isolated_env.home / "agent.sock")}

    result = run_remote_ssh(
        repo_dir,
        ["git", "status", "github.com-myuser"],
        cwd=repo,
        env=env,
    )

    assert_ok(result)
    output = result.stdout
    assert "  key:              256 SHA256:testkey forwarded-key (ED25519)" in output
    assert "  ssh agent:         ok" in output
    assert "  ssh auth:          denied-publickey" in output
    assert (
        "  - Check the SSH alias, IdentityFile, and whether the public key is registered "
        "with your Git provider."
    ) in output
    assert "  - Run remote-ssh git setup if the Git SSH aliases are not configured yet." in output


def test_remote_ssh_git_status_reports_session_override(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    require_git()
    repo = init_git_repo(isolated_env.home / "repo", env=isolated_env.env)
    write_fake_ssh_add(isolated_env.bin_dir, "256 SHA256:testkey forwarded-key (ED25519)")
    write_fake_ssh(
        isolated_env.bin_dir,
        "Hi test-user! You've successfully authenticated, but GitHub does not provide shell access.",
        1,
    )
    for args in (
        ["--local", "user.name", "Repo User"],
        ["--local", "user.email", "repo@example.com"],
    ):
        result = run_cmd(["git", "config", *args], cwd=repo, env=isolated_env.env)
        assert_ok(result)
    env = isolated_env.env | {
        "SSH_AUTH_SOCK": str(isolated_env.home / "agent.sock"),
        "REMOTE_SSH_GIT_SESSION_IDENTITY": "1",
        "GIT_CONFIG_COUNT": "3",
        "GIT_CONFIG_KEY_0": "user.name",
        "GIT_CONFIG_VALUE_0": "Session User",
        "GIT_CONFIG_KEY_1": "user.email",
        "GIT_CONFIG_VALUE_1": "session@example.com",
        "GIT_CONFIG_KEY_2": "user.useConfigOnly",
        "GIT_CONFIG_VALUE_2": "true",
    }

    result = run_remote_ssh(
        repo_dir,
        ["git", "status", "github.com-myuser"],
        cwd=repo,
        env=env,
    )

    assert_ok(result)
    output = result.stdout
    assert "  user.name:         Session User " in output
    assert "  user.email:        session@example.com " in output
    assert "Git session override" in output
    assert "  enabled:           1" in output
    assert "  GIT_CONFIG_COUNT:  3" in output
    assert "  session name:      Session User" in output
    assert "  session email:     session@example.com" in output
    assert "  session useConfigOnly: true" in output
