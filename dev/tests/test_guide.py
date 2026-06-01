from __future__ import annotations

from pathlib import Path

from conftest import IsolatedEnv, assert_failed, assert_ok, run_cmd, run_remote_ssh


def test_remote_ssh_guide_lists_core_entries(repo_dir: Path, isolated_env: IsolatedEnv) -> None:
    result = run_remote_ssh(repo_dir, ["guide"], env=isolated_env.env)

    assert_ok(result)
    assert "remote-ssh guide" in result.stdout
    assert "Commands" in result.stdout
    assert "  remote-ssh guide [section]  Show this configuration guide" in result.stdout
    assert "  remote-ssh uninstall [tool ...]" in result.stdout
    assert "  remote-ssh setup            Configure bundled SSH and Git defaults" in result.stdout
    assert "  remote-ssh git setup        Add remote-ssh Git config via include.path" in result.stdout
    assert "  remote-ssh git status       Check Git identity, SSH agent, and Git SSH auth" in result.stdout
    assert "  remote-ssh ssh setup        Add remote-ssh SSH config include" in result.stdout
    assert "  remote-ssh ssh status       Check SSH config, host resolution, and agent" in result.stdout
    assert "  remote-ssh scripts --list   List bundled helper scripts" in result.stdout
    assert "  remote-ssh guide config     Show runtime config sources and values" in result.stdout
    assert "  bssh                        Run bssh with the shared SSH config" in result.stdout
    assert "  bssh-ip                     Print resolved SSH host address" in result.stdout
    assert "  ssh-pick                    Pick an SSH host with fzf and connect" in result.stdout
    assert "  remote-ssh guide starship   Explain prompt and Git status symbols" in result.stdout
    assert "  remote-ssh guide post-install" in result.stdout
    assert "  alias rhelp='remote-ssh guide'" in result.stdout
    assert "  log" in result.stdout
    assert "  logrun" in result.stdout
    assert "  remote_atuin_debug" in result.stdout
    assert "Git and SSH flow" in result.stdout
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
    assert "  bssh" in result.stdout
    assert "  bssh-ip" in result.stdout
    assert "  ssh-pick" in result.stdout
    assert "  remote_atuin_debug" in result.stdout
    assert "Commands" not in result.stdout


def test_remote_ssh_guide_supports_git_section(repo_dir: Path, isolated_env: IsolatedEnv) -> None:
    result = run_remote_ssh(repo_dir, ["guide", "git"], env=isolated_env.env)

    assert_ok(result)
    assert "Git and SSH flow" in result.stdout
    assert "    remote-ssh setup" in result.stdout
    assert "    remote-ssh ssh setup" in result.stdout
    assert "    remote-ssh git setup" in result.stdout
    assert f"    {repo_dir}/dots/git/user.local" in result.stdout
    assert "    remote-ssh ssh status github.com-myuser" in result.stdout
    assert "    remote-ssh git status github.com-myuser" in result.stdout
    assert f"    {repo_dir}/dots/ssh/config.local" in result.stdout
    assert "Commands" not in result.stdout


def test_remote_ssh_guide_supports_tools_section(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    result = run_remote_ssh(repo_dir, ["guide", "tools"], env=isolated_env.env)

    assert_ok(result)
    assert "Tools" in result.stdout
    assert "  install      remote-ssh install" in result.stdout
    assert "  install quick remote-ssh install --profile quick" in result.stdout
    assert "Install profiles" in result.stdout
    assert "  mini  remote-ssh install --profile mini" in result.stdout
    assert "  quick remote-ssh install --profile quick" in result.stdout
    assert "  full  remote-ssh install --profile full" in result.stdout
    assert "Default tools on this platform" in result.stdout
    assert "  rg" in result.stdout
    assert "Commands" not in result.stdout


def test_remote_ssh_guide_supports_config_section(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    config = Path(isolated_env.env["XDG_CONFIG_HOME"]) / "remote-ssh" / "config"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        "REMOTE_SSH_WELCOME_BANNER=0\n"
        "REMOTE_SSH_WELCOME_USER=1\n"
        "REMOTE_SSH_WELCOME_USER=0\n",
        encoding="utf-8",
    )

    result = run_remote_ssh(
        repo_dir,
        ["guide", "config"],
        env=isolated_env.env | {"REMOTE_SSH_WELCOME_COLOR": "0"},
    )

    assert_ok(result)
    output = result.stdout
    assert "Runtime config" in output
    assert f"  file:    {config}" in output
    assert "  loading: enabled" in output
    assert "  REMOTE_SSH_WELCOME_BANNER=0 [config]" in output
    assert "  REMOTE_SSH_WELCOME_COLOR=0 [env]" in output
    assert "  REMOTE_SSH_WELCOME_USER=0 [config]" in output
    assert "  REMOTE_SSH_UPDATE_CHECK_INTERVAL=86400 [default]" in output
    assert "Commands" not in output

    disabled = run_remote_ssh(
        repo_dir,
        ["guide", "config"],
        env=isolated_env.env | {"REMOTE_SSH_CONFIG": "0"},
    )

    assert_ok(disabled)
    assert "  loading: disabled" in disabled.stdout
    assert "  REMOTE_SSH_WELCOME_BANNER=1 [default]" in disabled.stdout


def test_remote_ssh_guide_config_ignores_legacy_and_stale_source_markers(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    config = Path(isolated_env.env["XDG_CONFIG_HOME"]) / "remote-ssh" / "config"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text("REMOTE_SSH_WELCOME_USER=0\n", encoding="utf-8")

    disabled = run_remote_ssh(
        repo_dir,
        ["guide", "config"],
        env=isolated_env.env
        | {
            "REMOTE_SSH_CONFIG": "0",
            "REMOTE_SSH_WELCOME_USER": "0",
            "REMOTE_SSH_CONFIG_SOURCE_REMOTE_SSH_WELCOME_USER": "config",
        },
    )

    assert_ok(disabled)
    assert "  loading: disabled" in disabled.stdout
    assert "  REMOTE_SSH_WELCOME_USER=0 [env]" in disabled.stdout

    override = run_remote_ssh(
        repo_dir,
        ["guide", "config"],
        env=isolated_env.env
        | {
            "REMOTE_SSH_WELCOME_USER": "1",
            "REMOTE_SSH_CONFIG_SOURCE_REMOTE_SSH_WELCOME_USER": "config",
        },
    )

    assert_ok(override)
    assert "  REMOTE_SSH_WELCOME_USER=1 [env]" in override.stdout

    post_load_override = run_cmd(
        [
            "bash",
            "--rcfile",
            repo_dir / "shell" / "rc.sh",
            "-i",
            "-c",
            'export REMOTE_SSH_WELCOME_USER=1; . "$REMOTE_SHELL_DIR/rc.sh"; remote-ssh guide config',
        ],
        env=isolated_env.env | {"REMOTE_SSH_WELCOME": "0", "REMOTE_SSH_UPDATE_CHECK": "0"},
    )

    assert_ok(post_load_override)
    assert "  REMOTE_SSH_WELCOME_USER=1 [env]" in post_load_override.stdout

    disabled_after_load = run_cmd(
        [
            "bash",
            "--rcfile",
            repo_dir / "shell" / "rc.sh",
            "-i",
            "-c",
            'export REMOTE_SSH_CONFIG=0; . "$REMOTE_SHELL_DIR/rc.sh"; remote-ssh guide config',
        ],
        env=isolated_env.env | {"REMOTE_SSH_WELCOME": "0", "REMOTE_SSH_UPDATE_CHECK": "0"},
    )

    assert_ok(disabled_after_load)
    assert "  loading: disabled" in disabled_after_load.stdout
    assert "  REMOTE_SSH_WELCOME_USER=1 [default]" in disabled_after_load.stdout
    assert "  REMOTE_SSH_WELCOME_USER=1 [config]" not in disabled_after_load.stdout


def test_remote_ssh_guide_config_preserves_rc_config_provenance(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    config = Path(isolated_env.env["XDG_CONFIG_HOME"]) / "remote-ssh" / "config"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        "REMOTE_SSH_WELCOME_BANNER=0\nREMOTE_SSH_WELCOME_USER=0\n",
        encoding="utf-8",
    )

    result = run_cmd(
        [
            "bash",
            "--rcfile",
            repo_dir / "shell" / "rc.sh",
            "-i",
            "-c",
            "remote-ssh guide config",
        ],
        env=isolated_env.env | {"REMOTE_SSH_WELCOME": "0", "REMOTE_SSH_UPDATE_CHECK": "0"},
    )

    assert_ok(result)
    assert "  REMOTE_SSH_WELCOME_BANNER=0 [config]" in result.stdout
    assert "  REMOTE_SSH_WELCOME_USER=0 [config]" in result.stdout
    assert "  REMOTE_SSH_WELCOME=0 [env]" in result.stdout

    override = run_cmd(
        [
            "bash",
            "--rcfile",
            repo_dir / "shell" / "rc.sh",
            "-i",
            "-c",
            "remote-ssh guide config",
        ],
        env=isolated_env.env
        | {
            "REMOTE_SSH_WELCOME": "0",
            "REMOTE_SSH_UPDATE_CHECK": "0",
            "REMOTE_SSH_WELCOME_USER": "1",
        },
    )

    assert_ok(override)
    assert "  REMOTE_SSH_WELCOME_USER=1 [env]" in override.stdout


def test_remote_ssh_guide_config_uses_shared_config_entries(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    env = {
        key: value
        for key, value in isolated_env.env.items()
        if not key.startswith("REMOTE_SSH_") and key != "NO_COLOR"
    }
    entries = run_cmd(
        [
            "bash",
            "-c",
            '. "$1/shell/config.lib.sh"; remote_ssh_config_entries',
            "_",
            repo_dir,
        ],
        env=env,
    )
    assert_ok(entries)

    result = run_remote_ssh(repo_dir, ["guide", "config"], env=env | {"REMOTE_SSH_CONFIG": "0"})
    assert_ok(result)

    for line in entries.stdout.splitlines():
        key, default = line.split("|", 1)
        assert f"  {key}={default} [default]" in result.stdout


def test_remote_ssh_guide_supports_scripts_section(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    result = run_remote_ssh(repo_dir, ["guide", "scripts"], env=isolated_env.env)

    assert_ok(result)
    output = result.stdout
    assert "Scripts" in output
    assert "bssh" in output
    assert "bssh-ip" in output
    assert "ci-run" in output
    assert "helm-chart-diff" in output
    assert "ssh-pick" in output
    assert "Requires: bssh" in output
    assert "Requires: gh" in output
    assert "Commands" not in output
    assert "Tools" not in output


def test_remote_ssh_guide_scripts_supports_single_helper(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    result = run_remote_ssh(repo_dir, ["guide", "scripts", "ssh-pick"], env=isolated_env.env)

    assert_ok(result)
    output = result.stdout
    assert "Scripts" in output
    assert "ssh-pick" in output
    assert "ssh-pick [ssh-args...]" in output
    assert "Entry point: shell/rc.d/30-ssh-pick.sh" in output
    assert "Docs: docs/shell/helpers.md#ssh-pick" in output
    assert "ci-run" not in output
    assert "helm-chart-diff" not in output
    assert "sshf" not in output


def test_remote_ssh_guide_scripts_supports_bssh_ip_helper(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    result = run_remote_ssh(repo_dir, ["guide", "scripts", "bssh-ip"], env=isolated_env.env)

    assert_ok(result)
    output = result.stdout
    assert "Scripts" in output
    assert "bssh-ip" in output
    assert "bssh-ip <host>" in output
    assert "Requires: ssh, awk" in output
    assert "Entry point: shell/rc.d/26-bssh.sh" in output
    assert "Docs: docs/shell/helpers.md#bssh" in output
    assert "ci-run" not in output
    assert "helm-chart-diff" not in output
    assert "ssh-pick" not in output


def test_remote_ssh_guide_scripts_rejects_unknown_helper(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    result = run_remote_ssh(repo_dir, ["guide", "scripts", "sshf"], env=isolated_env.env)

    assert_failed(result)
    assert "Unknown remote-ssh script helper: sshf" in result.stderr
    assert "Usage:" in result.stderr
    assert "remote-ssh guide scripts [helper]" in result.stderr


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
    assert "Optional Git and SSH setup" in output
    assert f'bash --rcfile "{repo_dir}/shell/rc.sh"' in output
    assert '"terminal.integrated.defaultProfile.linux": "bash + remote-ssh"' in output
    assert "Commands" not in output
    assert "@INSTALL_DIR@" not in output
