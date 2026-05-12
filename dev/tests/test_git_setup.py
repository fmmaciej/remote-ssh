from __future__ import annotations

from pathlib import Path

from conftest import (
    IsolatedEnv,
    assert_ok,
    copy_repo_for_git_setup,
    git_config,
    require_git,
    run_git_setup,
)


def test_remote_ssh_git_setup_adds_include_once(
    repo_dir: Path,
    tmp_path: Path,
    isolated_env: IsolatedEnv,
) -> None:
    require_git()
    repo_copy = copy_repo_for_git_setup(repo_dir, tmp_path)

    result = run_git_setup(repo_copy, env=isolated_env.env)
    assert_ok(result)
    result = run_git_setup(repo_copy, env=isolated_env.env)
    assert_ok(result)
    result = git_config(["--global", "--get-all", "include.path"], env=isolated_env.env)

    assert_ok(result)
    assert result.stdout.rstrip("\n") == str(repo_copy / "dots" / "git" / "config.base")


def test_remote_ssh_git_setup_creates_local_examples(
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

    result = run_git_setup(repo_copy, env=isolated_env.env)

    assert_ok(result)
    output = user_local.read_text(encoding="utf-8") + "\n--- ssh ---\n"
    output += ssh_config_local.read_text(encoding="utf-8")
    assert "[user]\n" in output
    assert "    name = Your Name\n" in output
    assert "    email = your.email@example.com\n" in output
    assert "Host github.com-myuser\n" in output
    assert "  IdentitiesOnly no\n" in output


def test_remote_ssh_git_setup_adds_ssh_include_once(
    repo_dir: Path,
    tmp_path: Path,
    isolated_env: IsolatedEnv,
) -> None:
    require_git()
    repo_copy = copy_repo_for_git_setup(repo_dir, tmp_path)
    ssh_config = isolated_env.home / ".ssh" / "config"
    ssh_config.parent.mkdir(parents=True)
    ssh_config.write_text("Host existing\n  HostName example.com\n", encoding="utf-8")

    result = run_git_setup(repo_copy, env=isolated_env.env)
    assert_ok(result)
    result = run_git_setup(repo_copy, env=isolated_env.env)
    assert_ok(result)

    mode = oct(ssh_config.stat().st_mode & 0o777)[2:]
    assert ssh_config.read_text(encoding="utf-8") + f"mode:{mode}\n" == (
        f"Include {repo_copy / 'dots' / 'ssh' / 'config.local'}\n"
        "\n"
        "Host existing\n"
        "  HostName example.com\n"
        "mode:600\n"
    )


def test_remote_ssh_git_setup_exposes_base_defaults_via_include(
    repo_dir: Path,
    tmp_path: Path,
    isolated_env: IsolatedEnv,
) -> None:
    require_git()
    repo_copy = copy_repo_for_git_setup(repo_dir, tmp_path)
    (repo_copy / "dots" / "git" / "user.local").write_text(
        "[user]\n"
        "    name = Test User\n"
        "    email = test@example.com\n"
        "\n"
        "[core]\n"
        "    editor = vim\n",
        encoding="utf-8",
    )

    result = run_git_setup(repo_copy, env=isolated_env.env)
    assert_ok(result)

    keys = [
        "init.defaultBranch",
        "fetch.prune",
        "pull.rebase",
        "rebase.autoStash",
        "push.autoSetupRemote",
        "rerere.enabled",
        "merge.conflictStyle",
        "diff.algorithm",
        "help.autoCorrect",
        "user.useConfigOnly",
        "user.name",
        "core.editor",
    ]
    values = []
    for key in keys:
        result = git_config([key], env=isolated_env.env)
        assert_ok(result)
        values.append(result.stdout.rstrip("\n"))

    assert values == [
        "main",
        "true",
        "true",
        "true",
        "true",
        "true",
        "zdiff3",
        "histogram",
        "prompt",
        "true",
        "Test User",
        "vim",
    ]
