from __future__ import annotations

import shutil
from pathlib import Path

from conftest import (
    IsolatedEnv,
    assert_failed,
    assert_ok,
    require_zsh,
    run_cmd,
    write_executable,
)


def test_line_editing_uses_vi_mode_for_bash(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    env = isolated_env.env | {"REPO_DIR": str(repo_dir)}

    result = run_cmd(
        [
            "bash",
            "--noprofile",
            "--norc",
            "-ic",
            """
            . "$REPO_DIR/lib/guards.sh"
            . "$REPO_DIR/shell/rc.d/11-line-editing.sh"
            set -o | awk '$1 == "vi" { print $2 }'
            """,
        ],
        env=env,
    )

    assert_ok(result)
    assert result.stdout.rstrip("\n") == "on"


def test_line_editing_uses_vi_mode_for_zsh(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    require_zsh()
    log_file = isolated_env.home / "bindkey.log"
    env = isolated_env.env | {
        "REPO_DIR": str(repo_dir),
        "BINDKEY_LOG": str(log_file),
    }

    result = run_cmd(
        [
            "zsh",
            "-i",
            "-c",
            """
            bindkey() {
              print -r -- "$*" >> "$BINDKEY_LOG"
              builtin bindkey "$@"
            }
            source "$REPO_DIR/lib/guards.sh"
            source "$REPO_DIR/shell/rc.d/11-line-editing.sh"
            if [[ -s "$BINDKEY_LOG" ]]; then
              cat "$BINDKEY_LOG"
            fi
            """,
        ],
        env=env,
    )

    assert_ok(result)
    assert "-v" in result.stdout.splitlines()


def test_editor_prefers_nvim_and_sets_visual(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    write_executable(
        isolated_env.bin_dir / "nvim",
        """
        #!/usr/bin/env bash
        exit 0
        """,
    )
    env = isolated_env.env | {
        "PATH": f"{isolated_env.bin_dir}:/usr/bin:/bin:/usr/sbin:/sbin",
        "REPO_DIR": str(repo_dir),
    }

    result = run_cmd(
        [
            "bash",
            "--noprofile",
            "--norc",
            "-ic",
            """
            . "$REPO_DIR/lib/guards.sh"
            . "$REPO_DIR/lib/helpers.sh"
            . "$REPO_DIR/shell/rc.d/10-editor-pager.sh"
            printf "editor=%s\n" "${EDITOR:-missing}"
            printf "visual=%s\n" "${VISUAL:-missing}"
            """,
        ],
        env=env,
    )

    assert_ok(result)
    lines = result.stdout.splitlines()
    assert "editor=nvim" in lines
    assert "visual=nvim" in lines


def test_shell_aliases_include_parent_directory_shortcuts(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    result = run_cmd(
        [
            "bash",
            "--noprofile",
            "--norc",
            "-ic",
            """
            . "$1/lib/guards.sh"
            . "$1/lib/helpers.sh"
            . "$1/shell/aliases.sh"
            alias ..
            alias ...
            alias ....
            """,
            "_",
            repo_dir,
        ],
        env=isolated_env.env,
    )

    assert_ok(result)
    assert "alias ..='cd ..'" in result.stdout
    assert "alias ...='cd ../..'" in result.stdout
    assert "alias ....='cd ../../..'" in result.stdout


def test_bundled_vimrc_uses_system_clipboard_when_available(repo_dir: Path) -> None:
    conf = (repo_dir / "dots" / "vimrc").read_text(encoding="utf-8")

    assert "set clipboard=unnamed,unnamedplus" in conf
    assert 'nnoremap <leader>p "+p' in conf


def test_bundled_vimrc_disables_classic_vim_bracketed_paste(repo_dir: Path) -> None:
    conf = (repo_dir / "dots" / "vimrc").read_text(encoding="utf-8")

    assert "if !has('nvim')" in conf
    assert "set t_BE=" in conf


def test_vim_alias_uses_bundled_vimrc_when_nvim_is_available(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    write_executable(
        isolated_env.bin_dir / "nvim",
        """
        #!/usr/bin/env bash
        printf '%s\n' "$@" >"$NVIM_ARGS_LOG"
        """,
    )
    args_log = isolated_env.home / "nvim.args"
    env = isolated_env.env | {
        "PATH": f"{isolated_env.bin_dir}:/usr/bin:/bin",
        "REMOTE_DOTS_DIR": str(repo_dir / "dots"),
        "NVIM_ARGS_LOG": str(args_log),
    }

    result = run_cmd(
        [
            "bash",
            "--noprofile",
            "--norc",
            "-ic",
            """
            . "$1/lib/guards.sh"
            . "$1/lib/helpers.sh"
            . "$1/shell/aliases.sh"
            eval 'vim sample.txt'
            """,
            "_",
            repo_dir,
        ],
        env=env,
    )

    assert_ok(result)
    assert args_log.read_text(encoding="utf-8").splitlines() == [
        "-u",
        str(repo_dir / "dots" / "vimrc"),
        "sample.txt",
    ]


def test_editor_warns_when_missing(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    env = isolated_env.env | {
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
        "REPO_DIR": str(repo_dir),
    }

    result = run_cmd(
        [
            "bash",
            "--noprofile",
            "--norc",
            "-ic",
            """
            have() { return 1; }
            . "$REPO_DIR/shell/rc.d/10-editor-pager.sh"
            printf "editor=%s\n" "${EDITOR:-missing}"
            printf "visual=%s\n" "${VISUAL:-missing}"
            """,
        ],
        env=env,
    )

    assert_ok(result)
    output = result.stdout + result.stderr
    assert "editor=missing" in output.splitlines()
    assert "visual=missing" in output.splitlines()
    assert "[WARN] No vim/nvim found in PATH. Install one manually if you want an editor." in output


def test_tmux_conf_uses_modern_copy_mode_api(repo_dir: Path) -> None:
    conf = (repo_dir / "dots" / "tmux.conf").read_text(encoding="utf-8")

    assert "bind -T copy-mode-vi v send -X begin-selection" in conf
    assert "bind -T copy-mode-vi y send -X copy-selection-and-cancel" in conf
    assert "bind -T copy-mode-vi Escape send -X cancel" in conf
    assert "vi-copy" not in conf


def test_tmux_conf_reloads_project_config(repo_dir: Path) -> None:
    conf = (repo_dir / "dots" / "tmux.conf").read_text(encoding="utf-8")

    assert "source-file ~/.local/share/remote-ssh/dots/tmux.conf" in conf


def test_navi_init_sets_cheats_path(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    tmp_path: Path,
) -> None:
    remote = tmp_path / "repo"
    cheats = remote / "dots" / "navi" / "cheats"
    rc_dir = remote / "shell" / "rc.d"
    cheats.mkdir(parents=True)
    rc_dir.mkdir(parents=True)
    shutil.copy2(repo_dir / "shell" / "rc.d" / "24-navi.sh", rc_dir / "24-navi.sh")
    write_executable(isolated_env.bin_dir / "navi", "#!/usr/bin/env bash\n")
    env = isolated_env.env | {
        "PATH": f"{isolated_env.bin_dir}:/usr/bin:/bin",
        "REMOTE_DOTS_DIR": str(remote / "dots"),
    }

    result = run_cmd(
        [
            "bash",
            "-c",
            """
            have() { command -v "$1" >/dev/null 2>&1; }
            ensure_this_file_sourced() { :; }
            source "$1"
            alias cheats
            printf "NAVI_PATH=%s\n" "$NAVI_PATH"
            """,
            "_",
            rc_dir / "24-navi.sh",
        ],
        env=env,
    )

    assert_ok(result)
    lines = result.stdout.splitlines()
    assert f"NAVI_PATH={cheats}" in lines
    assert "alias cheats='navi'" in lines


def test_navi_init_preserves_existing_cheats_path(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    tmp_path: Path,
) -> None:
    remote = tmp_path / "repo"
    cheats = remote / "dots" / "navi" / "cheats"
    rc_dir = remote / "shell" / "rc.d"
    cheats.mkdir(parents=True)
    rc_dir.mkdir(parents=True)
    shutil.copy2(repo_dir / "shell" / "rc.d" / "24-navi.sh", rc_dir / "24-navi.sh")
    personal = tmp_path / "personal"
    env = isolated_env.env | {
        "REMOTE_DOTS_DIR": str(remote / "dots"),
        "NAVI_PATH": str(personal),
    }

    result = run_cmd(
        [
            "bash",
            "-c",
            """
            have() { return 1; }
            ensure_this_file_sourced() { :; }
            source "$1"
            printf "NAVI_PATH=%s\n" "$NAVI_PATH"
            """,
            "_",
            rc_dir / "24-navi.sh",
        ],
        env=env,
    )

    assert_ok(result)
    assert f"NAVI_PATH={cheats}:{personal}" in result.stdout.splitlines()


def test_log_filter_writes_explicit_file(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    write_executable(
        isolated_env.bin_dir / "tspin",
        """
        #!/usr/bin/env bash
        cat
        """,
    )
    out = isolated_env.home / "out.log"
    env = isolated_env.env | {
        "PATH": f"{isolated_env.bin_dir}:{isolated_env.env['PATH']}",
        "REPO_DIR": str(repo_dir),
    }

    result = run_cmd(
        [
            "bash",
            "-c",
            """
            . "$REPO_DIR/lib/guards.sh"
            . "$REPO_DIR/lib/helpers.sh"
            . "$REPO_DIR/shell/rc.d/25-log.sh"
            printf "one\ntwo\n" | log "$1"
            """,
            "_",
            out,
        ],
        env=env,
    )

    assert_ok(result)
    assert result.stdout.rstrip("\n") == "one\ntwo"
    assert out.read_text(encoding="utf-8").rstrip("\n") == "one\ntwo"


def test_logrun_writes_default_file_and_preserves_status(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    work = isolated_env.home / "work"
    work.mkdir()
    write_executable(
        isolated_env.bin_dir / "tspin",
        """
        #!/usr/bin/env bash
        cat
        """,
    )
    write_executable(
        isolated_env.bin_dir / "failcmd",
        """
        #!/usr/bin/env bash
        printf 'out\n'
        printf 'err\n' >&2
        exit 7
        """,
    )
    env = isolated_env.env | {
        "PATH": f"{isolated_env.bin_dir}:{isolated_env.env['PATH']}",
        "REPO_DIR": str(repo_dir),
    }

    result = run_cmd(
        [
            "bash",
            "-c",
            """
            cd "$1" || exit
            . "$REPO_DIR/lib/guards.sh"
            . "$REPO_DIR/lib/helpers.sh"
            . "$REPO_DIR/shell/rc.d/25-log.sh"
            logrun failcmd
            """,
            "_",
            work,
        ],
        env=env,
    )

    assert_failed(result)
    assert result.returncode == 7
    assert result.stdout.rstrip("\n") == "out\nerr"
    assert (work / "failcmd.log").read_text(encoding="utf-8").rstrip("\n") == "out\nerr"
