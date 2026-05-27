from __future__ import annotations

import shutil
from pathlib import Path

from conftest import (
    IsolatedEnv,
    ToolStateEnv,
    assert_ok,
    make_managed_tool,
    prepare_minimal_remote_tree,
    run_cmd,
    write_executable,
    write_expected_tools,
    write_git_user_local,
)


def _copy_welcome_lib(repo_dir: Path, remote: Path) -> None:
    shutil.copy2(
        repo_dir / "shell" / "update-check.lib.sh",
        remote / "shell" / "update-check.lib.sh",
    )
    shutil.copytree(
        repo_dir / "shell" / "update-check",
        remote / "shell" / "update-check",
        dirs_exist_ok=True,
    )
    shutil.copy2(
        repo_dir / "shell" / "welcome.lib.sh",
        remote / "shell" / "welcome.lib.sh",
    )
    shutil.copytree(
        repo_dir / "shell" / "welcome",
        remote / "shell" / "welcome",
        dirs_exist_ok=True,
    )


def _copy_welcome_runner(repo_dir: Path, remote: Path) -> None:
    shutil.copy2(
        repo_dir / "shell" / "config.lib.sh",
        remote / "shell" / "config.lib.sh",
    )
    shutil.copytree(
        repo_dir / "shell" / "config",
        remote / "shell" / "config",
        dirs_exist_ok=True,
    )
    shutil.copy2(
        repo_dir / "shell" / "rc.d" / "08-welcome.sh",
        remote / "shell" / "rc.d" / "08-welcome.sh",
    )
    _copy_welcome_lib(repo_dir, remote)


def test_welcome_user_module_template_is_documentation_only(repo_dir: Path) -> None:
    template = repo_dir / "shell" / "welcome.d" / "user-module.sh.example"

    assert template.exists()
    assert template.stat().st_mode & 0o111 == 0
    text = template.read_text(encoding="utf-8")
    assert "${XDG_CONFIG_HOME:-$HOME/.config}/remote-ssh/welcome.d/10-example.sh" in text
    assert "REMOTE_SSH_WELCOME_ISSUES_FILE" not in text


def test_welcome_runner_is_standalone_without_remote_shell_dir(repo_dir: Path, tmp_path: Path) -> None:
    temp_dir = tmp_path / "tmp"
    temp_dir.mkdir()
    inherited_issue_file = tmp_path / "inherited-issues"
    inherited_issue_file.write_text("original\n", encoding="utf-8")

    result = run_cmd(
        [
            "bash",
            "-c",
            """
            set -euo pipefail
            cd "$1"
            . shell/welcome.lib.sh
            unset REMOTE_SHELL_DIR
            export REMOTE_SSH_WELCOME_BANNER=0
            export REMOTE_SSH_WELCOME_USER=0
            export REMOTE_SSH_UPDATE_CHECK=0
            export TMPDIR="$2"
            export REMOTE_SSH_WELCOME_ISSUES_FILE="$3"
            REMOTE_SSH_WELCOME_ISSUES=(inherited)
            remote_ssh_welcome_run
            if [[ -z "${REMOTE_SSH_WELCOME_ISSUES_FILE+x}" ]]; then
              printf 'issues-file=unset\n'
            else
              printf 'issues-file=%s\n' "$REMOTE_SSH_WELCOME_ISSUES_FILE"
            fi
            if declare -p REMOTE_SSH_WELCOME_ISSUES >/dev/null 2>&1; then
              printf 'issues-array=set\n'
            else
              printf 'issues-array=unset\n'
            fi
            """,
            "_",
            repo_dir,
            temp_dir,
            inherited_issue_file,
        ],
    )

    assert_ok(result)
    assert "REMOTE_SHELL_DIR" not in result.stderr
    assert "update:  disabled" in result.stdout
    assert "hw:" in result.stdout
    assert "issues-file=unset" in result.stdout
    assert "issues-array=unset" in result.stdout
    assert inherited_issue_file.read_text(encoding="utf-8") == "original\n"


def test_welcome_runner_skips_noninteractive_shells(repo_dir: Path, tmp_path: Path) -> None:
    remote = prepare_minimal_remote_tree(repo_dir, tmp_path)
    _copy_welcome_runner(repo_dir, remote)
    called = tmp_path / "called"
    write_executable(
        remote / "shell" / "welcome.d" / "00-test.sh",
        f"""
        #!/usr/bin/env bash
        touch {called}
        """,
    )

    result = run_cmd(
        [
            "bash",
            "-c",
            """
            set -euo pipefail
            . "$1/shell/rc.sh"
            [[ ! -e "$2" ]]
            """,
            "_",
            remote,
            called,
        ]
    )

    assert_ok(result)


def test_welcome_runner_orders_bundled_and_user_modules(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    tmp_path: Path,
) -> None:
    remote = prepare_minimal_remote_tree(repo_dir, tmp_path)
    _copy_welcome_runner(repo_dir, remote)
    write_executable(
        remote / "shell" / "welcome.d" / "00-bundled.sh",
        """
        #!/usr/bin/env bash
        printf 'bundled-00\n'
        """,
    )
    write_executable(
        remote / "shell" / "welcome.d" / "10-failing.sh",
        """
        #!/usr/bin/env bash
        printf 'bundled-10\n'
        exit 7
        """,
    )
    user_dir = Path(isolated_env.env["XDG_CONFIG_HOME"]) / "remote-ssh" / "welcome.d"
    write_executable(
        user_dir / "50-user.sh",
        """
        #!/usr/bin/env bash
        printf 'user-50\n'
        """,
    )
    (user_dir / "40-ignored.sh").write_text(
        "#!/usr/bin/env bash\nprintf 'ignored\\n'\n",
        encoding="utf-8",
    )

    result = run_cmd(
        [
            "bash",
            "-i",
            "-c",
            """
            . "$1/shell/rc.sh"
            """,
            "_",
            remote,
        ],
        env=isolated_env.env,
    )

    assert_ok(result)
    lines = result.stdout.splitlines()
    assert lines == ["bundled-00", "bundled-10", "user-50"]


def test_welcome_runner_can_disable_user_modules(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    tmp_path: Path,
) -> None:
    remote = prepare_minimal_remote_tree(repo_dir, tmp_path)
    _copy_welcome_runner(repo_dir, remote)
    write_executable(
        remote / "shell" / "welcome.d" / "00-bundled.sh",
        """
        #!/usr/bin/env bash
        printf 'bundled\n'
        """,
    )
    user_dir = Path(isolated_env.env["XDG_CONFIG_HOME"]) / "remote-ssh" / "welcome.d"
    write_executable(
        user_dir / "50-user.sh",
        """
        #!/usr/bin/env bash
        printf 'user\n'
        """,
    )

    env_disabled = run_cmd(
        ["bash", "-i", "-c", '. "$1/shell/rc.sh"', "_", remote],
        env=isolated_env.env | {"REMOTE_SSH_WELCOME_USER": "0"},
    )
    assert_ok(env_disabled)
    assert env_disabled.stdout.splitlines() == ["bundled"]

    config = Path(isolated_env.env["XDG_CONFIG_HOME"]) / "remote-ssh" / "config"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text("REMOTE_SSH_WELCOME_USER=0\n", encoding="utf-8")
    config_disabled = run_cmd(
        ["bash", "-i", "-c", '. "$1/shell/rc.sh"', "_", remote],
        env=isolated_env.env,
    )
    assert_ok(config_disabled)
    assert config_disabled.stdout.splitlines() == ["bundled"]


def test_welcome_runner_toggle_and_red_next(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    tmp_path: Path,
) -> None:
    remote = prepare_minimal_remote_tree(repo_dir, tmp_path)
    _copy_welcome_runner(repo_dir, remote)
    write_executable(
        remote / "shell" / "welcome.d" / "00-test.sh",
        """
        #!/usr/bin/env bash
        printf 'status-line\n'
        printf 'update\n' >>"${REMOTE_SSH_WELCOME_ISSUES_FILE}"
        """,
    )

    disabled = run_cmd(
        [
            "bash",
            "-i",
            "-c",
            '. "$1/shell/rc.sh"',
            "_",
            remote,
        ],
        env=isolated_env.env | {"REMOTE_SSH_WELCOME": "0"},
    )
    assert_ok(disabled)
    assert "status-line" not in disabled.stdout

    colored = run_cmd(
        [
            "bash",
            "-i",
            "-c",
            '. "$1/shell/rc.sh"',
            "_",
            remote,
        ],
        env=isolated_env.env | {"NO_COLOR": ""},
    )
    assert_ok(colored)
    assert "status-line" in colored.stdout
    assert "\x1b[31mnext:    remote-ssh update\x1b[0m" in colored.stdout

    plain = run_cmd(
        [
            "bash",
            "-i",
            "-c",
            '. "$1/shell/rc.sh"',
            "_",
            remote,
        ],
        env=isolated_env.env | {"REMOTE_SSH_WELCOME_COLOR": "0"},
    )
    assert_ok(plain)
    assert "next:    remote-ssh update" in plain.stdout
    assert "\x1b[31m" not in plain.stdout


def test_remote_ssh_config_loads_allowlisted_values(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    tmp_path: Path,
) -> None:
    remote = prepare_minimal_remote_tree(repo_dir, tmp_path)
    _copy_welcome_runner(repo_dir, remote)
    config = Path(isolated_env.env["XDG_CONFIG_HOME"]) / "remote-ssh" / "config"
    config.parent.mkdir(parents=True)
    config.write_text(
        "\n".join(
            [
                "# remote-ssh config",
                "REMOTE_SSH_WELCOME_BANNER=1",
                "REMOTE_SSH_WELCOME_BANNER=0",
                "REMOTE_SSH_WELCOME_COLOR=0",
                "REMOTE_SSH_WELCOME_USER=1",
                "REMOTE_SSH_WELCOME_USER=0",
                "NO_COLOR=1",
                "UNKNOWN_KEY=ignored",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    write_executable(
        remote / "shell" / "welcome.d" / "00-config.sh",
        """
        #!/usr/bin/env bash
        printf 'banner=%s\n' "${REMOTE_SSH_WELCOME_BANNER:-missing}"
        printf 'color=%s\n' "${REMOTE_SSH_WELCOME_COLOR:-missing}"
        printf 'user=%s\n' "${REMOTE_SSH_WELCOME_USER:-missing}"
        printf 'no_color=%s\n' "${NO_COLOR:-missing}"
        printf 'unknown=%s\n' "${UNKNOWN_KEY:-missing}"
        """,
    )

    result = run_cmd(
        ["bash", "-i", "-c", '. "$1/shell/rc.sh"', "_", remote],
        env=isolated_env.env,
    )

    assert_ok(result)
    assert "banner=0" in result.stdout
    assert "color=0" in result.stdout
    assert "user=0" in result.stdout
    assert "no_color=1" in result.stdout
    assert "unknown=missing" in result.stdout


def test_remote_ssh_config_env_override_and_disable(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    tmp_path: Path,
) -> None:
    remote = prepare_minimal_remote_tree(repo_dir, tmp_path)
    _copy_welcome_runner(repo_dir, remote)
    config = Path(isolated_env.env["XDG_CONFIG_HOME"]) / "remote-ssh" / "config"
    config.parent.mkdir(parents=True)
    config.write_text("REMOTE_SSH_WELCOME_BANNER=0\n", encoding="utf-8")
    write_executable(
        remote / "shell" / "welcome.d" / "00-config.sh",
        """
        #!/usr/bin/env bash
        printf 'banner=%s\n' "${REMOTE_SSH_WELCOME_BANNER:-missing}"
        """,
    )

    override = run_cmd(
        ["bash", "-i", "-c", '. "$1/shell/rc.sh"', "_", remote],
        env=isolated_env.env | {"REMOTE_SSH_WELCOME_BANNER": "1"},
    )
    assert_ok(override)
    assert "banner=1" in override.stdout

    disabled = run_cmd(
        ["bash", "-i", "-c", '. "$1/shell/rc.sh"', "_", remote],
        env=isolated_env.env | {"REMOTE_SSH_CONFIG": "0"},
    )
    assert_ok(disabled)
    assert "banner=missing" in disabled.stdout


def test_remote_ssh_config_reload_updates_config_owned_values(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    tmp_path: Path,
) -> None:
    remote = prepare_minimal_remote_tree(repo_dir, tmp_path)
    _copy_welcome_runner(repo_dir, remote)
    config = Path(isolated_env.env["XDG_CONFIG_HOME"]) / "remote-ssh" / "config"
    config.parent.mkdir(parents=True)
    config.write_text("REMOTE_SSH_WELCOME_USER=0\n", encoding="utf-8")

    result = run_cmd(
        [
            "bash",
            "-c",
            """
            set -euo pipefail
            . "$1/shell/config.lib.sh"
            remote_ssh_config_load
            printf 'first=%s:%s:%s\n' \
              "$REMOTE_SSH_WELCOME_USER" \
              "$(remote_ssh_config_source REMOTE_SSH_WELCOME_USER)" \
              "${REMOTE_SSH_CONFIG_LOADED_VALUE_WELCOME_USER-unset}"
            printf 'REMOTE_SSH_WELCOME_USER=1\n' >"$2/remote-ssh/config"
            remote_ssh_config_load
            printf 'second=%s:%s:%s\n' \
              "$REMOTE_SSH_WELCOME_USER" \
              "$(remote_ssh_config_source REMOTE_SSH_WELCOME_USER)" \
              "${REMOTE_SSH_CONFIG_LOADED_VALUE_WELCOME_USER-unset}"
            : >"$2/remote-ssh/config"
            remote_ssh_config_load
            if [[ -z "${REMOTE_SSH_WELCOME_USER+x}" ]]; then
              printf 'third=unset:%s:%s\n' \
                "$(remote_ssh_config_source REMOTE_SSH_WELCOME_USER)" \
                "${REMOTE_SSH_CONFIG_LOADED_VALUE_WELCOME_USER-unset}"
            else
              printf 'third=%s:%s:%s\n' \
                "$REMOTE_SSH_WELCOME_USER" \
                "$(remote_ssh_config_source REMOTE_SSH_WELCOME_USER)" \
                "${REMOTE_SSH_CONFIG_LOADED_VALUE_WELCOME_USER-unset}"
            fi
            """,
            "_",
            remote,
            Path(isolated_env.env["XDG_CONFIG_HOME"]),
        ],
        env=isolated_env.env,
    )

    assert_ok(result)
    assert result.stdout.splitlines() == [
        "first=0:config:0",
        "second=1:config:1",
        "third=unset::unset",
    ]


def test_remote_ssh_config_loader_preserves_true_env_override_and_clears_stale_marker(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    tmp_path: Path,
) -> None:
    remote = prepare_minimal_remote_tree(repo_dir, tmp_path)
    _copy_welcome_runner(repo_dir, remote)
    config = Path(isolated_env.env["XDG_CONFIG_HOME"]) / "remote-ssh" / "config"
    config.parent.mkdir(parents=True)
    config.write_text("REMOTE_SSH_WELCOME_USER=0\n", encoding="utf-8")

    override = run_cmd(
        [
            "bash",
            "-c",
            """
            set -euo pipefail
            . "$1/shell/config.lib.sh"
            remote_ssh_config_load
            export REMOTE_SSH_WELCOME_USER=1
            remote_ssh_config_load
            printf 'value=%s\n' "$REMOTE_SSH_WELCOME_USER"
            printf 'source=%s\n' "$(remote_ssh_config_source REMOTE_SSH_WELCOME_USER)"
            printf 'loaded=%s\n' "${REMOTE_SSH_CONFIG_LOADED_VALUE_WELCOME_USER-unset}"
            """,
            "_",
            remote,
        ],
        env=isolated_env.env,
    )
    assert_ok(override)
    assert override.stdout.splitlines() == ["value=1", "source=", "loaded=unset"]

    disabled = run_cmd(
        [
            "bash",
            "-c",
            """
            set -euo pipefail
            . "$1/shell/config.lib.sh"
            remote_ssh_config_load
            REMOTE_SSH_CONFIG=0
            remote_ssh_config_load
            if [[ -z "${REMOTE_SSH_WELCOME_USER+x}" ]]; then
              printf 'value=unset\n'
            else
              printf 'value=%s\n' "$REMOTE_SSH_WELCOME_USER"
            fi
            printf 'source=%s\n' "$(remote_ssh_config_source REMOTE_SSH_WELCOME_USER)"
            printf 'loaded=%s\n' "${REMOTE_SSH_CONFIG_LOADED_VALUE_WELCOME_USER-unset}"
            """,
            "_",
            remote,
        ],
        env=isolated_env.env,
    )
    assert_ok(disabled)
    assert disabled.stdout.splitlines() == ["value=unset", "source=", "loaded=unset"]

    disabled_with_manual_env = run_cmd(
        [
            "bash",
            "-c",
            """
            set -euo pipefail
            . "$1/shell/config.lib.sh"
            remote_ssh_config_load
            export REMOTE_SSH_WELCOME_USER=1
            REMOTE_SSH_CONFIG=0
            remote_ssh_config_load
            printf 'value=%s\n' "$REMOTE_SSH_WELCOME_USER"
            printf 'source=%s\n' "$(remote_ssh_config_source REMOTE_SSH_WELCOME_USER)"
            printf 'loaded=%s\n' "${REMOTE_SSH_CONFIG_LOADED_VALUE_WELCOME_USER-unset}"
            """,
            "_",
            remote,
        ],
        env=isolated_env.env,
    )
    assert_ok(disabled_with_manual_env)
    assert disabled_with_manual_env.stdout.splitlines() == [
        "value=1",
        "source=",
        "loaded=unset",
    ]


def test_remote_ssh_config_loader_ignores_legacy_source_markers(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    tmp_path: Path,
) -> None:
    remote = prepare_minimal_remote_tree(repo_dir, tmp_path)
    _copy_welcome_runner(repo_dir, remote)
    config = Path(isolated_env.env["XDG_CONFIG_HOME"]) / "remote-ssh" / "config"
    config.parent.mkdir(parents=True)
    config.write_text("REMOTE_SSH_WELCOME_USER=0\n", encoding="utf-8")

    result = run_cmd(
        [
            "bash",
            "-c",
            """
            set -euo pipefail
            . "$1/shell/config.lib.sh"
            remote_ssh_config_load
            printf 'value=%s\n' "$REMOTE_SSH_WELCOME_USER"
            printf 'source=%s\n' "$(remote_ssh_config_source REMOTE_SSH_WELCOME_USER)"
            printf 'loaded=%s\n' "${REMOTE_SSH_CONFIG_LOADED_VALUE_WELCOME_USER-unset}"
            """,
            "_",
            remote,
        ],
        env=isolated_env.env
        | {
            "REMOTE_SSH_WELCOME_USER": "1",
            "REMOTE_SSH_CONFIG_SOURCE_REMOTE_SSH_WELCOME_USER": "config",
        },
    )
    assert_ok(result)
    assert result.stdout.splitlines() == [
        "value=1",
        "source=",
        "loaded=unset",
    ]


def test_remote_ssh_config_loader_tracks_empty_loaded_value(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    tmp_path: Path,
) -> None:
    remote = prepare_minimal_remote_tree(repo_dir, tmp_path)
    _copy_welcome_runner(repo_dir, remote)
    config = Path(isolated_env.env["XDG_CONFIG_HOME"]) / "remote-ssh" / "config"
    config.parent.mkdir(parents=True)
    config.write_text("REMOTE_SSH_WELCOME_USER=\n", encoding="utf-8")

    result = run_cmd(
        [
            "bash",
            "-c",
            """
            set -euo pipefail
            . "$1/shell/config.lib.sh"
            remote_ssh_config_load
            printf 'first=<%s>:%s:%s\n' \
              "$REMOTE_SSH_WELCOME_USER" \
              "$(remote_ssh_config_source REMOTE_SSH_WELCOME_USER)" \
              "${REMOTE_SSH_CONFIG_LOADED_VALUE_WELCOME_USER}"
            printf 'REMOTE_SSH_WELCOME_USER=1\n' >"$2/remote-ssh/config"
            remote_ssh_config_load
            printf 'second=%s:%s:%s\n' \
              "$REMOTE_SSH_WELCOME_USER" \
              "$(remote_ssh_config_source REMOTE_SSH_WELCOME_USER)" \
              "${REMOTE_SSH_CONFIG_LOADED_VALUE_WELCOME_USER}"
            """,
            "_",
            remote,
            Path(isolated_env.env["XDG_CONFIG_HOME"]),
        ],
        env=isolated_env.env,
    )

    assert_ok(result)
    assert result.stdout.splitlines() == ["first=<>:config:", "second=1:config:1"]


def test_welcome_runner_uses_issue_file_and_ignores_magic_stdout(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    tmp_path: Path,
) -> None:
    remote = prepare_minimal_remote_tree(repo_dir, tmp_path)
    _copy_welcome_runner(repo_dir, remote)
    write_executable(
        remote / "shell" / "welcome.d" / "00-test.sh",
        """
        #!/usr/bin/env bash
        printf '__REMOTE_SSH_WELCOME_ISSUE__=update\n'
        """,
    )

    result = run_cmd(
        ["bash", "-i", "-c", '. "$1/shell/rc.sh"', "_", remote],
        env=isolated_env.env,
    )

    assert_ok(result)
    assert "__REMOTE_SSH_WELCOME_ISSUE__=update" in result.stdout
    assert "next:" not in result.stdout


def test_welcome_runner_does_not_use_inherited_issue_file(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    tmp_path: Path,
) -> None:
    remote = prepare_minimal_remote_tree(repo_dir, tmp_path)
    _copy_welcome_runner(repo_dir, remote)
    inherited_issue_file = tmp_path / "inherited-issues"
    write_executable(
        remote / "shell" / "welcome.d" / "00-test.sh",
        """
        #!/usr/bin/env bash
        printf 'status-line\n'
        printf 'update\n' >>"${REMOTE_SSH_WELCOME_ISSUES_FILE}"
        """,
    )

    result = run_cmd(
        [
            "bash",
            "-i",
            "-c",
            """
            . "$1/shell/rc.sh"
            if [[ -z "${REMOTE_SSH_WELCOME_ISSUES_FILE+x}" ]]; then
              printf 'issues-env=unset\n'
            else
              printf 'issues-env=%s\n' "$REMOTE_SSH_WELCOME_ISSUES_FILE"
            fi
            """,
            "_",
            remote,
        ],
        env=isolated_env.env | {"REMOTE_SSH_WELCOME_ISSUES_FILE": str(inherited_issue_file)},
    )

    assert_ok(result)
    assert "status-line" in result.stdout
    assert "next:    remote-ssh update" in result.stdout
    assert "issues-env=unset" in result.stdout
    assert not inherited_issue_file.exists()


def test_welcome_runner_removes_temp_files(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    tmp_path: Path,
) -> None:
    remote = prepare_minimal_remote_tree(repo_dir, tmp_path)
    _copy_welcome_runner(repo_dir, remote)
    tmpdir = tmp_path / "tmp"
    tmpdir.mkdir()
    issue_path_record = tmp_path / "issue-path"
    write_executable(
        remote / "shell" / "welcome.d" / "00-test.sh",
        f"""
        #!/usr/bin/env bash
        printf '%s\n' "$REMOTE_SSH_WELCOME_ISSUES_FILE" >{issue_path_record}
        printf 'module-output\n'
        printf 'update\n' >>"$REMOTE_SSH_WELCOME_ISSUES_FILE"
        exit 7
        """,
    )

    result = run_cmd(
        [
            "bash",
            "-i",
            "-c",
            """
            set -e
            . "$1/shell/rc.sh"
            printf 'after-rc\n'
            """,
            "_",
            remote,
        ],
        env=isolated_env.env | {"TMPDIR": str(tmpdir)},
    )

    assert_ok(result)
    assert "module-output" in result.stdout
    assert "after-rc" in result.stdout
    issue_path = Path(issue_path_record.read_text(encoding="utf-8").strip())
    assert not issue_path.exists()
    assert list(tmpdir.glob("remote-ssh-welcome-issues.*")) == []
    assert list(tmpdir.glob("remote-ssh-welcome-module.*")) == []


def test_welcome_runner_ignores_unknown_issues(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    tmp_path: Path,
) -> None:
    remote = prepare_minimal_remote_tree(repo_dir, tmp_path)
    _copy_welcome_runner(repo_dir, remote)
    write_executable(
        remote / "shell" / "welcome.d" / "00-test.sh",
        """
        #!/usr/bin/env bash
        printf 'custom-line\n'
        printf 'mystery\n' >>"${REMOTE_SSH_WELCOME_ISSUES_FILE}"
        """,
    )

    quiet = run_cmd(
        ["bash", "-i", "-c", '. "$1/shell/rc.sh"', "_", remote],
        env=isolated_env.env,
    )
    assert_ok(quiet)
    assert "custom-line" in quiet.stdout
    assert "next:" not in quiet.stdout
    assert "ignoring unknown issue" not in quiet.stderr

    debug = run_cmd(
        ["bash", "-i", "-c", '. "$1/shell/rc.sh"', "_", remote],
        env=isolated_env.env | {"REMOTE_SSH_WELCOME_DEBUG": "1"},
    )
    assert_ok(debug)
    assert "next:" not in debug.stdout
    assert "remote-ssh welcome: ignoring unknown issue: mystery" in debug.stderr


def test_welcome_runner_gives_modules_empty_stdin(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    tmp_path: Path,
) -> None:
    remote = prepare_minimal_remote_tree(repo_dir, tmp_path)
    _copy_welcome_runner(repo_dir, remote)
    write_executable(
        remote / "shell" / "welcome.d" / "00-stdin.sh",
        """
        #!/usr/bin/env bash
        if read -r module_input; then
          printf 'module-read=%s\n' "$module_input"
        else
          printf 'module-eof\n'
        fi
        """,
    )

    result = run_cmd(
        [
            "bash",
            "-c",
            """
            printf 'after-line\n' | bash -i -c '. "$1/shell/rc.sh"; read -r after; printf "after=%s\n" "$after"' _ "$1"
            """,
            "_",
            remote,
        ],
        env=isolated_env.env,
    )

    assert_ok(result)
    assert "module-eof" in result.stdout
    assert "module-read=" not in result.stdout
    assert "after=after-line" in result.stdout


def test_welcome_runner_debug_reports_module_errors(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    tmp_path: Path,
) -> None:
    remote = prepare_minimal_remote_tree(repo_dir, tmp_path)
    _copy_welcome_runner(repo_dir, remote)
    write_executable(
        remote / "shell" / "welcome.d" / "00-fail.sh",
        """
        #!/usr/bin/env bash
        printf 'visible\n'
        printf 'debug-stderr\n' >&2
        exit 7
        """,
    )

    quiet = run_cmd(
        ["bash", "-i", "-c", '. "$1/shell/rc.sh"', "_", remote],
        env=isolated_env.env,
    )
    assert_ok(quiet)
    assert "visible" in quiet.stdout
    assert "debug-stderr" not in quiet.stderr
    assert "module failed" not in quiet.stderr

    debug = run_cmd(
        ["bash", "-i", "-c", '. "$1/shell/rc.sh"', "_", remote],
        env=isolated_env.env | {"REMOTE_SSH_WELCOME_DEBUG": "1"},
    )
    assert_ok(debug)
    assert "debug-stderr" in debug.stderr
    assert "remote-ssh welcome: module failed:" in debug.stderr


def test_remote_ssh_welcome_update_disabled_and_missing_cache_do_not_raise_issue(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    issues_file = isolated_env.home / "issues"
    state_dir = isolated_env.home / "state"

    disabled = run_cmd(
        [
            "bash",
            "-c",
            '. "$1/shell/welcome.lib.sh"; remote_ssh_welcome_print_update',
            "_",
            repo_dir,
        ],
        env=isolated_env.env
        | {
            "REMOTE_SSH_UPDATE_CHECK": "0",
            "REMOTE_SSH_UPDATE_CHECK_STATE_DIR": str(state_dir),
            "REMOTE_SSH_WELCOME_ISSUES_FILE": str(issues_file),
        },
    )
    assert_ok(disabled)
    assert disabled.stdout.rstrip("\n") == "update:  disabled"
    assert not issues_file.exists()

    missing_cache = run_cmd(
        [
            "bash",
            "-c",
            '. "$1/shell/welcome.lib.sh"; remote_ssh_welcome_print_update',
            "_",
            repo_dir,
        ],
        env=isolated_env.env
        | {
            "REMOTE_SSH_UPDATE_CHECK_STATE_DIR": str(state_dir),
            "REMOTE_SSH_WELCOME_ISSUES_FILE": str(issues_file),
        },
    )
    assert_ok(missing_cache)
    assert missing_cache.stdout.rstrip("\n") == "update:  unknown (checked: never)"
    assert not issues_file.exists()


def test_remote_ssh_welcome_update_error_reports_doctor_issue(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    issues_file = isolated_env.home / "issues"
    state_dir = isolated_env.home / "state"
    state_dir.mkdir()
    (state_dir / "update-check").write_text(
        "checked_at=1\nchecked_at_text=2026-05-27 12:02:00 UTC\nstatus=error\n",
        encoding="utf-8",
    )

    result = run_cmd(
        [
            "bash",
            "-c",
            '. "$1/shell/welcome.lib.sh"; remote_ssh_welcome_print_update',
            "_",
            repo_dir,
        ],
        env=isolated_env.env
        | {
            "REMOTE_SSH_UPDATE_CHECK_STATE_DIR": str(state_dir),
            "REMOTE_SSH_WELCOME_ISSUES_FILE": str(issues_file),
        },
    )

    assert_ok(result)
    assert result.stdout.rstrip("\n") == "update:  unavailable (checked: 2026-05-27 12:02:00 UTC)"
    assert issues_file.read_text(encoding="utf-8").splitlines() == ["doctor"]


def test_remote_ssh_welcome_update_malformed_cache_reports_doctor_issue(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    issues_file = isolated_env.home / "issues"
    state_dir = isolated_env.home / "state"
    state_dir.mkdir()
    (state_dir / "update-check").write_text(
        "checked_at=1\nchecked_at_text=2026-05-27 12:03:00 UTC\n",
        encoding="utf-8",
    )

    result = run_cmd(
        [
            "bash",
            "-c",
            '. "$1/shell/welcome.lib.sh"; remote_ssh_welcome_print_update',
            "_",
            repo_dir,
        ],
        env=isolated_env.env
        | {
            "REMOTE_SSH_UPDATE_CHECK_STATE_DIR": str(state_dir),
            "REMOTE_SSH_WELCOME_ISSUES_FILE": str(issues_file),
        },
    )

    assert_ok(result)
    assert result.stdout.rstrip("\n") == "update:  unavailable (checked: 2026-05-27 12:03:00 UTC)"
    assert issues_file.read_text(encoding="utf-8").splitlines() == ["doctor"]


def test_remote_ssh_welcome_module_reports_statuses(
    repo_dir: Path,
    tool_env: ToolStateEnv,
) -> None:
    state_dir = tool_env.home / "state"
    state_dir.mkdir()
    (state_dir / "update-check").write_text(
        "checked_at=1\nchecked_at_text=2026-05-27 12:00:00 UTC\nstatus=current\n",
        encoding="utf-8",
    )
    write_expected_tools(tool_env, ["rg", "fd"])
    make_managed_tool(tool_env, "rg", "15.1.0")
    make_managed_tool(tool_env, "fd", "10.3.0")
    for command in ("gh", "helm", "python3", "fzf"):
        write_executable(tool_env.bin_dir / command, "#!/usr/bin/env bash\nexit 0\n")

    result = run_cmd(
        [repo_dir / "shell" / "welcome.d" / "00-remote-ssh.sh"],
        env=tool_env.env
        | {
            "REMOTE_ENV_DIR": str(repo_dir),
            "REMOTE_SSH_UPDATE_CHECK_STATE_DIR": str(state_dir),
            "REMOTE_SSH_WELCOME_BANNER": "0",
        },
    )

    assert_ok(result)
    output = result.stdout
    assert "update:  current (checked: 2026-05-27 12:00:00 UTC)" in output
    assert "tools:   2 checked / 2 ok" in output
    assert "scripts: 3 checked / 3 ok" in output


def test_remote_ssh_welcome_module_uses_status_lib_without_commands_dispatcher(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    tmp_path: Path,
) -> None:
    remote = prepare_minimal_remote_tree(repo_dir, tmp_path)
    _copy_welcome_lib(repo_dir, remote)
    (remote / "shell" / "welcome.d").mkdir()
    shutil.copy2(
        repo_dir / "shell" / "welcome.d" / "00-remote-ssh.sh",
        remote / "shell" / "welcome.d" / "00-remote-ssh.sh",
    )
    shutil.copytree(repo_dir / "tools", remote / "tools")
    (remote / "tools" / "lib" / "commands.lib.sh").unlink()

    result = run_cmd(
        [remote / "shell" / "welcome.d" / "00-remote-ssh.sh"],
        env=isolated_env.env
        | {
            "REMOTE_ENV_DIR": str(remote),
            "REMOTE_SSH_UPDATE_CHECK": "0",
            "REMOTE_SSH_WELCOME_BANNER": "0",
        },
    )

    assert_ok(result)
    assert "tools:" in result.stdout
    assert "scripts:" in result.stdout


def test_remote_ssh_welcome_module_reports_update_and_tool_problems(
    repo_dir: Path,
    tool_env: ToolStateEnv,
) -> None:
    state_dir = tool_env.home / "state"
    state_dir.mkdir()
    (state_dir / "update-check").write_text(
        "checked_at=1\nchecked_at_text=2026-05-27 12:01:00 UTC\nstatus=update-available\n",
        encoding="utf-8",
    )
    write_expected_tools(tool_env, ["rg"])
    issues_file = tool_env.home / "issues"

    result = run_cmd(
        [repo_dir / "shell" / "welcome.d" / "00-remote-ssh.sh"],
        env=tool_env.env
        | {
            "REMOTE_ENV_DIR": str(repo_dir),
            "REMOTE_SSH_UPDATE_CHECK_STATE_DIR": str(state_dir),
            "REMOTE_SSH_WELCOME_BANNER": "0",
            "REMOTE_SSH_WELCOME_ISSUES_FILE": str(issues_file),
        },
    )

    assert_ok(result)
    output = result.stdout
    assert "update:  available (checked: 2026-05-27 12:01:00 UTC)" in output
    assert "tools:   1 checked / 0 ok" in output
    assert "update" in issues_file.read_text(encoding="utf-8").splitlines()
    assert "tools" in issues_file.read_text(encoding="utf-8").splitlines()


def test_welcome_banner_is_responsive_and_can_be_hidden(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    def render(columns: str, *, banner: str = "1") -> str:
        result = run_cmd(
            [
                "bash",
                "-c",
                '. "$1/shell/welcome.lib.sh"; remote_ssh_welcome_print_banner',
                "_",
                repo_dir,
            ],
            env=isolated_env.env
            | {
                "COLUMNS": columns,
                "REMOTE_SSH_WELCOME_COLOR": "0",
                "REMOTE_SSH_WELCOME_BANNER": banner,
            },
        )
        assert_ok(result)
        return result.stdout

    full = render("100")
    assert "____  _____" in full
    assert "Remote-SSH" in full

    compact = render("60")
    assert compact.splitlines()[:2] == ["R-SSH", "Remote-SSH"]

    tiny = render("30")
    assert tiny.splitlines()[:2] == ["R-S", "Remote-SSH"]

    hidden = render("100", banner="0")
    assert hidden == ""


def test_welcome_ip_falls_back_to_unknown(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    result = run_cmd(
        [
            "/bin/bash",
            "-c",
            '. "$1/shell/welcome.lib.sh"; remote_ssh_welcome_host_ip',
            "_",
            repo_dir,
        ],
        env=isolated_env.env | {"PATH": "/nonexistent"},
    )

    assert_ok(result)
    assert result.stdout.rstrip("\n") == "unknown"


def test_welcome_ip_skips_ip_route_on_darwin(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    called = isolated_env.home / "ip-called"
    write_executable(
        isolated_env.bin_dir / "hostname",
        """
        #!/usr/bin/env bash
        exit 1
        """,
    )
    write_executable(
        isolated_env.bin_dir / "uname",
        """
        #!/usr/bin/env bash
        printf 'Darwin\n'
        """,
    )
    write_executable(
        isolated_env.bin_dir / "ip",
        f"""
        #!/usr/bin/env bash
        touch {called}
        printf 'unexpected ip route\n'
        exit 0
        """,
    )
    write_executable(
        isolated_env.bin_dir / "ifconfig",
        """
        #!/usr/bin/env bash
        printf 'en0: flags=8863<UP>\\n'
        printf '    inet 10.0.0.9 netmask 0xffffff00 broadcast 10.0.0.255\\n'
        """,
    )

    result = run_cmd(
        [
            "/bin/bash",
            "-c",
            '. "$1/shell/welcome.lib.sh"; remote_ssh_welcome_host_ip',
            "_",
            repo_dir,
        ],
        env=isolated_env.env
        | {"PATH": f"{isolated_env.bin_dir}:/usr/bin:/bin"},
    )

    assert_ok(result)
    assert result.stdout.rstrip("\n") == "10.0.0.9"
    assert not called.exists()


def test_welcome_ip_uses_ip_route_on_linux(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    ifconfig_called = isolated_env.home / "ifconfig-called"
    write_executable(
        isolated_env.bin_dir / "hostname",
        """
        #!/usr/bin/env bash
        exit 1
        """,
    )
    write_executable(
        isolated_env.bin_dir / "uname",
        """
        #!/usr/bin/env bash
        printf 'Linux\n'
        """,
    )
    write_executable(
        isolated_env.bin_dir / "ip",
        """
        #!/usr/bin/env bash
        printf '1.1.1.1 via 10.0.0.1 dev eth0 src 10.0.0.8 uid 1000\n'
        """,
    )
    write_executable(
        isolated_env.bin_dir / "ifconfig",
        f"""
        #!/usr/bin/env bash
        touch {ifconfig_called}
        exit 1
        """,
    )

    result = run_cmd(
        [
            "/bin/bash",
            "-c",
            '. "$1/shell/welcome.lib.sh"; remote_ssh_welcome_host_ip',
            "_",
            repo_dir,
        ],
        env=isolated_env.env
        | {"PATH": f"{isolated_env.bin_dir}:/usr/bin:/bin"},
    )

    assert_ok(result)
    assert result.stdout.rstrip("\n") == "10.0.0.8"
    assert not ifconfig_called.exists()


def test_sw_welcome_module_reports_agent_and_git_config(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    write_executable(
        isolated_env.bin_dir / "ssh-add",
        """
        #!/usr/bin/env bash
        printf '256 SHA256:test key (ED25519)\n'
        """,
    )
    write_executable(isolated_env.bin_dir / "git", "#!/usr/bin/env bash\nexit 0\n")

    result = run_cmd(
        [repo_dir / "shell" / "welcome.d" / "20-sw.sh"],
        env=isolated_env.env
        | {
            "REMOTE_ENV_DIR": str(repo_dir),
            "SSH_AUTH_SOCK": str(isolated_env.home / "agent.sock"),
            "REMOTE_SSH_GIT_SESSION_IDENTITY": "1",
        },
    )

    assert_ok(result)
    assert result.stdout.rstrip("\n") == "sw:      ssh-agent ok / git config ok"


def test_sw_uses_exported_git_session_identity_status_without_git(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    for status in ("ok", "disabled", "missing", "invalid", "unavailable"):
        result = run_cmd(
            [
                "/bin/bash",
                "-c",
                '. "$1/shell/welcome.lib.sh"; remote_ssh_welcome_git_user_config_status',
                "_",
                repo_dir,
            ],
            env=isolated_env.env
            | {
                "PATH": "/nonexistent",
                "REMOTE_SSH_GIT_SESSION_IDENTITY_STATUS": status,
            },
        )

        assert_ok(result)
        assert result.stdout.rstrip("\n") == status


def test_git_session_identity_hook_exports_status_for_welcome(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    tmp_path: Path,
) -> None:
    remote = prepare_minimal_remote_tree(repo_dir, tmp_path)
    (remote / "shell" / "rc.d" / "07-git-session-identity.sh").write_text(
        (repo_dir / "shell" / "rc.d" / "07-git-session-identity.sh").read_text(
            encoding="utf-8"
        ),
        encoding="utf-8",
    )
    write_git_user_local(remote / "dots")
    write_executable(
        isolated_env.bin_dir / "git",
        """
        #!/usr/bin/env bash
        if [[ "${1:-}" == "config" && "${2:-}" == "--file" ]]; then
          case "${5:-}" in
            user.name) printf 'Session User\n'; exit 0 ;;
            user.email) printf 'session@example.com\n'; exit 0 ;;
          esac
        fi
        exit 1
        """,
    )

    result = run_cmd(
        [
            "/bin/bash",
            "-c",
            """
            . "$1/shell/rc.sh"
            printf '%s:%s\n' \
              "$REMOTE_SSH_GIT_SESSION_IDENTITY" \
              "$REMOTE_SSH_GIT_SESSION_IDENTITY_STATUS"
            """,
            "_",
            remote,
        ],
        env=isolated_env.env,
    )

    assert_ok(result)
    assert result.stdout.rstrip("\n") == "1:ok"


def test_sw_welcome_module_treats_agent_empty_as_information(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    write_executable(
        isolated_env.bin_dir / "ssh-add",
        """
        #!/usr/bin/env bash
        printf 'The agent has no identities.\n' >&2
        exit 1
        """,
    )
    write_executable(isolated_env.bin_dir / "git", "#!/usr/bin/env bash\nexit 0\n")
    issues_file = isolated_env.home / "issues"

    result = run_cmd(
        [repo_dir / "shell" / "welcome.d" / "20-sw.sh"],
        env=isolated_env.env
        | {
            "REMOTE_ENV_DIR": str(repo_dir),
            "SSH_AUTH_SOCK": str(isolated_env.home / "agent.sock"),
            "REMOTE_SSH_GIT_SESSION_IDENTITY": "1",
            "REMOTE_SSH_WELCOME_ISSUES_FILE": str(issues_file),
        },
    )

    assert_ok(result)
    assert result.stdout.rstrip("\n") == "sw:      ssh-agent empty / git config ok"
    assert not issues_file.exists()


def test_sw_welcome_module_reports_inactive_valid_git_config(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    tmp_path: Path,
) -> None:
    remote = tmp_path / "remote"
    (remote / "shell" / "welcome.d").mkdir(parents=True)
    _copy_welcome_lib(repo_dir, remote)
    shutil.copy2(
        repo_dir / "shell" / "welcome.d" / "20-sw.sh",
        remote / "shell" / "welcome.d" / "20-sw.sh",
    )
    write_git_user_local(remote / "dots")
    write_executable(
        isolated_env.bin_dir / "ssh-add",
        """
        #!/usr/bin/env bash
        printf '256 SHA256:test key (ED25519)\n'
        """,
    )
    write_executable(
        isolated_env.bin_dir / "git",
        """
        #!/usr/bin/env bash
        if [[ "${1:-}" == "config" && "${2:-}" == "--file" ]]; then
          case "${5:-}" in
            user.name) printf 'Session User\n'; exit 0 ;;
            user.email) printf 'session@example.com\n'; exit 0 ;;
          esac
        fi
        exit 1
        """,
    )
    issues_file = isolated_env.home / "issues"

    result = run_cmd(
        [remote / "shell" / "welcome.d" / "20-sw.sh"],
        env=isolated_env.env
        | {
            "REMOTE_ENV_DIR": str(remote),
            "SSH_AUTH_SOCK": str(isolated_env.home / "agent.sock"),
            "REMOTE_SSH_WELCOME_ISSUES_FILE": str(issues_file),
        },
    )

    assert_ok(result)
    assert "sw:      ssh-agent ok / git config inactive" in result.stdout
    assert issues_file.read_text(encoding="utf-8").splitlines() == ["sw"]


def test_sw_welcome_module_reports_invalid_and_disabled_git_config(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    tmp_path: Path,
) -> None:
    remote = tmp_path / "remote"
    (remote / "shell" / "welcome.d").mkdir(parents=True)
    (remote / "dots" / "git").mkdir(parents=True)
    _copy_welcome_lib(repo_dir, remote)
    shutil.copy2(
        repo_dir / "shell" / "welcome.d" / "20-sw.sh",
        remote / "shell" / "welcome.d" / "20-sw.sh",
    )
    write_executable(isolated_env.bin_dir / "ssh-add", "#!/usr/bin/env bash\nexit 1\n")
    write_executable(
        isolated_env.bin_dir / "git",
        """
        #!/usr/bin/env bash
        exit 1
        """,
    )
    (remote / "dots" / "git" / "user.local").write_text(
        "[user]\n    name = Your Name\n    email = your.email@example.com\n",
        encoding="utf-8",
    )

    invalid = run_cmd(
        [remote / "shell" / "welcome.d" / "20-sw.sh"],
        env=isolated_env.env
        | {
            "REMOTE_ENV_DIR": str(remote),
            "SSH_AUTH_SOCK": str(isolated_env.home / "agent.sock"),
        },
    )
    assert_ok(invalid)
    assert "git config invalid" in invalid.stdout

    disabled = run_cmd(
        [remote / "shell" / "welcome.d" / "20-sw.sh"],
        env=isolated_env.env
        | {
            "REMOTE_ENV_DIR": str(remote),
            "SSH_AUTH_SOCK": str(isolated_env.home / "agent.sock"),
            "REMOTE_SSH_ENABLE_GIT_SESSION_IDENTITY": "0",
        },
    )
    assert_ok(disabled)
    assert "git config disabled" in disabled.stdout


def test_sw_welcome_module_reports_unavailable_git(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    issues_file = isolated_env.home / "issues"
    result = run_cmd(
        [
            "bash",
            "-c",
            """
            command() {
              if [[ "${1:-}" == "-v" && "${2:-}" == "git" ]]; then
                return 1
              fi
              builtin command "$@"
            }
            . "$1/shell/welcome.lib.sh"
            remote_ssh_welcome_print_sw
            """,
            "_",
            repo_dir,
        ],
        env=isolated_env.env | {"REMOTE_SSH_WELCOME_ISSUES_FILE": str(issues_file)},
    )

    assert_ok(result)
    assert "git config unavailable" in result.stdout
    assert issues_file.read_text(encoding="utf-8").splitlines() == ["doctor"]


def test_sw_welcome_module_flags_empty_agent_and_missing_git_config(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    tmp_path: Path,
) -> None:
    remote = tmp_path / "remote"
    (remote / "shell" / "welcome.d").mkdir(parents=True)
    _copy_welcome_lib(repo_dir, remote)
    shutil.copy2(
        repo_dir / "shell" / "welcome.d" / "20-sw.sh",
        remote / "shell" / "welcome.d" / "20-sw.sh",
    )
    write_executable(
        isolated_env.bin_dir / "ssh-add",
        """
        #!/usr/bin/env bash
        printf 'The agent has no identities.\n' >&2
        exit 1
        """,
    )
    write_executable(isolated_env.bin_dir / "git", "#!/usr/bin/env bash\nexit 0\n")
    issues_file = isolated_env.home / "issues"

    result = run_cmd(
        [remote / "shell" / "welcome.d" / "20-sw.sh"],
        env=isolated_env.env
        | {
            "REMOTE_ENV_DIR": str(remote),
            "SSH_AUTH_SOCK": str(isolated_env.home / "agent.sock"),
            "REMOTE_SSH_WELCOME_ISSUES_FILE": str(issues_file),
        },
    )

    assert_ok(result)
    assert "sw:      ssh-agent empty / git config missing" in result.stdout
    assert issues_file.read_text(encoding="utf-8").splitlines() == ["sw"]
