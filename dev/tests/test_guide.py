from __future__ import annotations

from pathlib import Path

from conftest import IsolatedEnv, assert_ok, run_remote_ssh


def test_remote_ssh_guide_lists_core_entries(repo_dir: Path, isolated_env: IsolatedEnv) -> None:
    result = run_remote_ssh(repo_dir, ["guide"], env=isolated_env.env)

    assert_ok(result)
    assert "remote-ssh guide" in result.stdout
    assert "Commands" in result.stdout
    assert "  remote-ssh guide [section]  Show this configuration guide" in result.stdout
    assert "  remote-ssh uninstall [tool ...]" in result.stdout
    assert "  remote-ssh git setup        Add remote-ssh Git config via include.path" in result.stdout
    assert "  remote-ssh git status       Check Git identity, SSH agent, and Git SSH auth" in result.stdout
    assert "  remote-ssh scripts --list   List bundled helper scripts" in result.stdout
    assert "  sshf                        Pick an SSH host with fzf and connect" in result.stdout
    assert "  remote-ssh guide starship   Explain prompt and Git status symbols" in result.stdout
    assert "  remote-ssh guide post-install" in result.stdout
    assert "  alias rhelp='remote-ssh guide'" in result.stdout
    assert "  log" in result.stdout
    assert "  logrun" in result.stdout
    assert "  remote_atuin_debug" in result.stdout
    assert "Git SSH flow" in result.stdout
    assert "Tools" in result.stdout
    assert "Scripts" in result.stdout
    assert "remote-ssh Starship prompt" in result.stdout
    assert f"    {repo_dir}/dots/git/user.local" in result.stdout
    assert "    git remote set-url origin git@github.com-myuser:OWNER/REPO.git" in result.stdout


def test_remote_ssh_guide_supports_aliases_section(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    result = run_remote_ssh(repo_dir, ["guide", "aliases"], env=isolated_env.env)

    assert_ok(result)
    assert "Aliases" in result.stdout
    assert "  alias rcrc='source \"$REMOTE_SHELL_DIR/rc.sh\"'" in result.stdout
    assert "  alias rhelp='remote-ssh guide'" in result.stdout
    assert "Commands" not in result.stdout


def test_remote_ssh_guide_supports_functions_section(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    result = run_remote_ssh(repo_dir, ["guide", "functions"], env=isolated_env.env)

    assert_ok(result)
    assert "Functions" in result.stdout
    assert "  log" in result.stdout
    assert "  logrun" in result.stdout
    assert "  sshf" in result.stdout
    assert "  remote_atuin_debug" in result.stdout
    assert "Commands" not in result.stdout


def test_remote_ssh_guide_supports_git_section(repo_dir: Path, isolated_env: IsolatedEnv) -> None:
    result = run_remote_ssh(repo_dir, ["guide", "git"], env=isolated_env.env)

    assert_ok(result)
    assert "Git SSH flow" in result.stdout
    assert "    remote-ssh git setup" in result.stdout
    assert f"    {repo_dir}/dots/git/user.local" in result.stdout
    assert "    remote-ssh git status github.com-myuser" in result.stdout
    assert f"    {repo_dir}/dots/ssh/config.local" in result.stdout
    assert "    ssh -T git@github.com-myuser" in result.stdout
    assert "Commands" not in result.stdout


def test_remote_ssh_guide_supports_tools_section(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    result = run_remote_ssh(repo_dir, ["guide", "tools"], env=isolated_env.env)

    assert_ok(result)
    assert "Tools" in result.stdout
    assert "  install      remote-ssh install" in result.stdout
    assert "Default tools on this platform" in result.stdout
    assert "  rg" in result.stdout
    assert "Commands" not in result.stdout


def test_remote_ssh_guide_supports_scripts_section(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    result = run_remote_ssh(repo_dir, ["guide", "scripts"], env=isolated_env.env)

    assert_ok(result)
    output = result.stdout
    assert "Scripts" in output
    assert "ci-run" in output
    assert "helm-chart-diff" in output
    assert "sshf" in output
    assert "Requires: gh" in output
    assert "Commands" not in output
    assert "Tools" not in output


def test_remote_ssh_guide_supports_starship_section(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    env = isolated_env.env | {
        "HOME": "/tmp/starship-guide-test",
        "REMOTE_DOTS_DIR": "/opt/remote-ssh/dots",
    }
    result = run_remote_ssh(repo_dir, ["guide", "starship"], env=env)

    assert_ok(result)
    lines = set(result.stdout.splitlines())
    for expected in (
        "remote-ssh Starship prompt",
        "  git::<branch>          Current branch",
        "  [!]                    Merge conflict",
        "  [+]                    Staged changes",
        "  [~]                    Modified tracked files",
        "  [?]                    Untracked files",
        "  [$]                    Stashed changes",
        "  [<>A/B]                Local branch has A ahead and B behind commits",
        "  /opt/remote-ssh/dots/starship.toml",
        "  starship explain",
    ):
        assert expected in lines
    assert "Commands" not in result.stdout


def test_remote_ssh_guide_supports_post_install_section(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    result = run_remote_ssh(repo_dir, ["guide", "post-install"], env=isolated_env.env)

    assert_ok(result)
    output = result.stdout
    assert "Interactive usage" in output
    assert "SSH configuration" in output
    assert "VS Code Remote-SSH terminal profile" in output
    assert "Optional Git setup" in output
    assert f'bash --rcfile "{repo_dir}/shell/rc.sh"' in output
    assert '"terminal.integrated.defaultProfile.linux": "bash + remote-ssh"' in output
    assert "Commands" not in output
    assert "@INSTALL_DIR@" not in output
