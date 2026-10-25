from __future__ import annotations

import shlex
import shutil
import subprocess
from pathlib import Path

import pytest
from conftest import IsolatedEnv, assert_ok, run_cmd, write_executable

ATUIN_WRAPPER_SETUP = r"""
audit_atuin_wrapper() {
  printf 'wrapper invoked\n' >> "$WRAPPER_LOG"
  return 91
}
define_atuin_wrapper() {
  case "$WRAPPER" in
    alias) alias atuin='audit_atuin_wrapper' ;;
    function) atuin() { audit_atuin_wrapper "$@"; } ;;
    none) return 0 ;;
  esac
  WRAPPER_DEFINITION="$(alias atuin 2>/dev/null || declare -f atuin)"
}
"""


def prepare_history_tools(isolated_env: IsolatedEnv, runtime_bash: str) -> None:
    (isolated_env.bin_dir / "bash").symlink_to(runtime_bash)
    write_executable(isolated_env.bin_dir / "fzf", "#!/bin/sh\nexit 0\n")
    write_executable(
        isolated_env.bin_dir / "atuin",
        r"""
        #!/bin/sh
        [ "$1" = init ] || exit 0
        echo init >> "$INIT_LOG"
        [ "${FAIL_INIT:-0}" = 0 ] || exit 1
        cat <<'INIT'
        audit_atuin_preexec() { :; }
        audit_atuin_precmd() { :; }
        preexec_functions+=(audit_atuin_preexec)
        precmd_functions+=(audit_atuin_precmd)
        INIT
        case " $* " in
          *' --disable-up-arrow '*) ;;
          *) cat <<'BIND'
        bind -m vi-insert '"\e[A":"atuin-owned"'
        BIND
          ;;
        esac
    """,
    )


@pytest.mark.parametrize("wrapper", ["alias", "function"])
@pytest.mark.parametrize("when", ["startup", "reload"])
@pytest.mark.parametrize("backend", ["working", "absent"])
def test_atuin_lookup_ignores_wrappers(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    runtime_bash: str,
    wrapper: str,
    when: str,
    backend: str,
) -> None:
    prepare_history_tools(isolated_env, runtime_bash)
    if backend == "absent":
        (isolated_env.bin_dir / "atuin").unlink()
    log = isolated_env.home / "init.log"
    wrapper_log = isolated_env.home / "wrapper.log"
    history = isolated_env.home / "custom history"
    result = run_cmd(
        [
            runtime_bash,
            "--noprofile",
            "--norc",
            "-ic",
            ATUIN_WRAPPER_SETUP
            + r"""
        . "$1/lib/guards.sh"
        . "$1/lib/helpers.sh"
        REMOTE_DOTS_DIR="$1/dots"
        bash_preexec_imported=1
        audit_user_exec() { :; }
        audit_user_cmd() { :; }
        preexec_functions=(audit_user_exec)
        precmd_functions=(audit_user_cmd)
        [[ "$WRAPPER_WHEN" != startup ]] || define_atuin_wrapper
        for iteration in 1 2 3; do
          if [[ "$WRAPPER_WHEN" == reload && "$iteration" == 2 ]]; then
            define_atuin_wrapper
          fi
          . "$1/shell/rc.d/06-bash-history.sh"
          . "$1/shell/rc.d/20-fzf.sh"
          . "$1/shell/rc.d/23-atuin.sh"
        done
        [[ "$(alias atuin 2>/dev/null || declare -f atuin)" == "$WRAPPER_DEFINITION" ]] || exit 30
        printf 'active=%s\nfile=%s\nfzf=%s\n' "$REMOTE_SSH_ATUIN_ACTIVE" "$HISTFILE" "${REMOTE_SSH_FZF_HISTORY_BOUND:-0}"
        printf 'exec=%s\ncmd=%s\nwrapper=%s\n' "${preexec_functions[*]}" "${precmd_functions[*]}" "$(type -t atuin)"
        """,
            "_",
            repo_dir,
        ],
        env=isolated_env.env
        | {
            "INIT_LOG": str(log),
            "WRAPPER_LOG": str(wrapper_log),
            "WRAPPER": wrapper,
            "WRAPPER_WHEN": when,
            "HISTFILE": str(history),
            "FAIL_INIT": "0",
            "REMOTE_SSH_ENABLE_ATUIN": "1",
            "REMOTE_SSH_ENABLE_ATUIN_AUTO_IMPORT": "0",
        },
    )
    assert_ok(result)
    assert not wrapper_log.exists()
    assert f"wrapper={wrapper}\n" in result.stdout
    if backend == "working":
        assert "active=1\nfile=\nfzf=0\n" in result.stdout
        assert "exec=audit_user_exec audit_atuin_preexec\n" in result.stdout
        assert "cmd=audit_user_cmd audit_atuin_precmd\n" in result.stdout
        assert log.read_text().splitlines() == ["init"]
    else:
        assert f"active=0\nfile={history}\nfzf=1\n" in result.stdout
        assert "exec=audit_user_exec\ncmd=audit_user_cmd\n" in result.stdout
        assert not log.exists()


@pytest.mark.parametrize("backend", ["absent", "disabled", "failing", "working"])
def test_history_backend_and_repeated_initialization(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str, backend: str
) -> None:
    prepare_history_tools(isolated_env, runtime_bash)
    if backend == "absent":
        (isolated_env.bin_dir / "atuin").unlink()
    log = isolated_env.home / "init.log"
    history = isolated_env.home / "history with spaces"
    script = """
        . "$1/lib/guards.sh"
        . "$1/lib/helpers.sh"
        REMOTE_DOTS_DIR="$1/dots"
        bash_preexec_imported=1
        for iteration in 1 2; do
          . "$1/shell/rc.d/06-bash-history.sh"
          . "$1/shell/rc.d/20-fzf.sh"
          . "$1/shell/rc.d/23-atuin.sh"
        done
        printf 'file=%s\nactive=%s\nfzf=%s\n' "$HISTFILE" "${REMOTE_SSH_ATUIN_ACTIVE:-0}" "${REMOTE_SSH_FZF_HISTORY_BOUND:-0}"
        printf 'hooks=%s\n' "${#preexec_functions[@]}"
        REMOTE_SSH_ENABLE_ATUIN=0
        . "$1/shell/rc.d/06-bash-history.sh"
        . "$1/shell/rc.d/23-atuin.sh"
        printf 'restored=%s\nhooks-after=%s\n' "$HISTFILE" "${#preexec_functions[@]}"
        bind -m vi-insert -s
    """
    result = run_cmd(
        [runtime_bash, "--noprofile", "--norc", "-ic", script, "_", repo_dir],
        env=isolated_env.env
        | {
            "INIT_LOG": str(log),
            "HISTFILE": str(history),
            "REMOTE_SSH_ENABLE_ATUIN": "0" if backend == "disabled" else "1",
            "FAIL_INIT": "1" if backend == "failing" else "0",
            "REMOTE_SSH_ENABLE_ATUIN_AUTO_IMPORT": "0",
        },
    )
    assert_ok(result)
    if backend == "working":
        assert "file=\nactive=1\nfzf=0" in result.stdout
        assert "hooks=1\n" in result.stdout
        assert log.read_text().splitlines() == ["init"]
    else:
        assert f"file={history}\nactive=0\nfzf=1" in result.stdout
    assert f"restored={history}\nhooks-after=0" in result.stdout
    assert "atuin-owned" not in result.stdout


@pytest.mark.parametrize("choice", ["default", "custom", "empty", "null"])
def test_bash_fallback_persistence_respects_user_history_settings(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str, choice: str
) -> None:
    env = isolated_env.env.copy()
    env.pop("HISTFILE", None)
    history = isolated_env.home / ("custom-history" if choice == "custom" else ".bash_history")
    if choice != "default":
        env["HISTFILE"] = {"custom": str(history), "empty": "", "null": "/dev/null"}[choice]
    script = f'. "{repo_dir}/lib/guards.sh"\n. "{repo_dir}/shell/rc.d/06-bash-history.sh"\nhistory -s audit-persisted-marker\nexit\n'
    result = subprocess.run(
        [runtime_bash, "--noprofile", "--norc", "-i"],
        input=script,
        text=True,
        capture_output=True,
        env=env,
    )
    assert_ok(result)
    if choice in {"empty", "null"}:
        assert not history.exists()
    else:
        second = run_cmd(
            [runtime_bash, "--noprofile", "--norc", "-ic", "history -r; history"], env=env
        )
        assert_ok(second)
        assert "audit-persisted-marker" in second.stdout


@pytest.mark.parametrize(
    "failure,wrapper",
    [
        ("removed", "none"),
        ("broken-link", "none"),
        ("not-executable", "none"),
        ("removed", "alias"),
        ("removed", "function"),
    ],
)
@pytest.mark.parametrize("choice", ["default", "custom", "empty", "null"])
def test_removed_hashed_atuin_restores_history(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    runtime_bash: str,
    failure: str,
    wrapper: str,
    choice: str,
) -> None:
    prepare_history_tools(isolated_env, runtime_bash)
    history = isolated_env.home / ("custom history" if choice == "custom" else ".bash_history")
    log = isolated_env.home / "init.log"
    wrapper_log = isolated_env.home / "wrapper.log"
    env = isolated_env.env | {
        "INIT_LOG": str(log),
        "FAIL_INIT": "0",
        "REMOTE_SSH_ENABLE_ATUIN": "1",
        "REMOTE_SSH_ENABLE_ATUIN_AUTO_IMPORT": "0",
        "FAILURE": failure,
        "WRAPPER": wrapper,
        "WRAPPER_LOG": str(wrapper_log),
        "ATUIN_BIN": str(isolated_env.bin_dir / "atuin"),
    }
    env.pop("HISTFILE", None)
    if choice != "default":
        env["HISTFILE"] = {"custom": str(history), "empty": "", "null": "/dev/null"}[choice]
    result = run_cmd(
        [
            runtime_bash,
            "--noprofile",
            "--norc",
            "-ic",
            ATUIN_WRAPPER_SETUP
            + r"""
        . "$1/lib/guards.sh"
        . "$1/lib/helpers.sh"
        REMOTE_DOTS_DIR="$1/dots"
        bash_preexec_imported=1
        audit_user_exec() { :; }
        audit_user_cmd() { :; }
        preexec_functions=(audit_user_exec)
        precmd_functions=(audit_user_cmd)
        bind -m vi-insert '"\e[A":"user-before"'
        . "$1/shell/rc.d/06-bash-history.sh"
        . "$1/shell/rc.d/20-fzf.sh"
        . "$1/shell/rc.d/23-atuin.sh"
        [[ "$REMOTE_SSH_ATUIN_ACTIVE" == 1 ]] || exit 20
        bind -m vi-command '"k":forward-char'
        # Bash skips function names in `hash`, so cache the external tool first.
        hash atuin mkdir
        define_atuin_wrapper
        other_hash="$(hash -t mkdir)"
        case "$FAILURE" in
          removed) rm "$ATUIN_BIN" ;;
          broken-link) mv "$ATUIN_BIN" "$ATUIN_BIN.saved"; ln -s absent "$ATUIN_BIN" ;;
          not-executable) chmod -x "$ATUIN_BIN" ;;
        esac
        [[ "$(hash -t atuin)" == "$ATUIN_BIN" ]] || exit 21
        for iteration in 1 2; do
          . "$1/shell/rc.d/06-bash-history.sh"
          . "$1/shell/rc.d/20-fzf.sh"
          . "$1/shell/rc.d/23-atuin.sh"
        done
        [[ "$(hash -t mkdir)" == "$other_hash" ]] || exit 22
        [[ "$WRAPPER" == none || "$(type -t atuin)" == "$WRAPPER" ]] || exit 23
        printf 'active=%s\nfile=%s\nfzf=%s\n' "$REMOTE_SSH_ATUIN_ACTIVE" "$HISTFILE" "$REMOTE_SSH_FZF_HISTORY_BOUND"
        printf 'exec=%s\ncmd=%s\n' "${preexec_functions[*]}" "${precmd_functions[*]}"
        bind -m vi-insert -s
        bind -m vi-command -p
        history -s audit-restored-marker
        history -a
        """,
            "_",
            repo_dir,
        ],
        env=env,
    )
    assert_ok(result)
    assert not wrapper_log.exists()
    expected = {"default": str(history), "custom": str(history), "empty": "", "null": "/dev/null"}
    assert f"active=0\nfile={expected[choice]}\nfzf=1" in result.stdout
    assert "exec=audit_user_exec\ncmd=audit_user_cmd\n" in result.stdout
    assert '"\\e[A": "user-before"' in result.stdout
    assert '"k": forward-char' in result.stdout
    assert "atuin-owned" not in result.stdout
    assert log.read_text().splitlines() == ["init"]
    if choice in {"empty", "null"}:
        assert not history.exists()
    else:
        second = run_cmd(
            [runtime_bash, "--noprofile", "--norc", "-ic", "history -r; history"], env=env
        )
        assert_ok(second)
        assert "audit-restored-marker" in second.stdout


@pytest.mark.parametrize("wrapper", ["none", "alias", "function"])
def test_atuin_removal_and_reactivation_in_full_rc(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str, wrapper: str
) -> None:
    prepare_history_tools(isolated_env, runtime_bash)
    atuin = isolated_env.bin_dir / "atuin"
    saved = isolated_env.home / "saved-atuin"
    shutil.copy2(atuin, saved)
    log = isolated_env.home / "init.log"
    history = isolated_env.home / "history"
    wrapper_log = isolated_env.home / "wrapper.log"
    env = isolated_env.env | {
        "INIT_LOG": str(log),
        "FAIL_INIT": "0",
        "HISTFILE": str(history),
        "REMOTE_SSH_CONFIG": "0",
        "REMOTE_SSH_UPDATE_CHECK": "0",
        "REMOTE_SSH_WELCOME": "0",
        "REMOTE_SSH_ENABLE_GIT_SESSION_IDENTITY": "0",
        "REMOTE_SSH_ENABLE_ATUIN": "1",
        "REMOTE_SSH_ENABLE_ATUIN_AUTO_IMPORT": "0",
        "ATUIN_BIN": str(atuin),
        "ATUIN_SAVED": str(saved),
        "WRAPPER": wrapper,
        "WRAPPER_LOG": str(wrapper_log),
    }
    # Interactive stdin exercises the real alias and bash-preexec between lines.
    script = "\n".join(
        [
            ATUIN_WRAPPER_SETUP,
            f". {shlex.quote(str(repo_dir / 'shell/rc.sh'))}",
            'printf "initial=%s\\n" "$REMOTE_SSH_ATUIN_ACTIVE"',
            "hash atuin",
            "define_atuin_wrapper",
            'rm "$ATUIN_BIN"',
            'printf "cached=%s\\n" "$(hash -t atuin)"',
            "rcrc",
            'printf "removed=%s:%s:%s\\n" "$REMOTE_SSH_ATUIN_ACTIVE" "$HISTFILE" "$REMOTE_SSH_FZF_HISTORY_BOUND"',
            'cp "$ATUIN_SAVED" "$ATUIN_BIN"',
            "rcrc",
            "rcrc",
            'printf "restored=%s:%s:%s\\n" "$REMOTE_SSH_ATUIN_ACTIVE" "${#preexec_functions[@]}" "${#precmd_functions[@]}"',
            'printf "wrapper=%s\\n" "$(type -t atuin)"',
            "exit",
            "",
        ]
    )
    result = subprocess.run(
        [runtime_bash, "--noprofile", "--norc", "-i"],
        input=script,
        text=True,
        capture_output=True,
        env=env,
    )
    assert_ok(result)
    assert "initial=1" in result.stdout
    assert f"cached={atuin}" in result.stdout
    assert f"removed=0:{history}:1" in result.stdout
    # bash-preexec retains its own preexec/precmd placeholder alongside Atuin.
    assert "restored=1:2:2" in result.stdout
    assert log.read_text().splitlines() == ["init"]
    assert f"wrapper={'file' if wrapper == 'none' else wrapper}\n" in result.stdout
    assert not wrapper_log.exists()


@pytest.mark.parametrize("wrapper", ["none", "alias", "function"])
def test_atuin_uses_alternative_after_hashed_binary_is_removed(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str, wrapper: str
) -> None:
    prepare_history_tools(isolated_env, runtime_bash)
    alternative = isolated_env.home / "alternative-bin"
    alternative.mkdir()
    shutil.copy2(isolated_env.bin_dir / "atuin", alternative / "atuin")
    log = isolated_env.home / "init.log"
    wrapper_log = isolated_env.home / "wrapper.log"
    result = run_cmd(
        [
            runtime_bash,
            "--noprofile",
            "--norc",
            "-ic",
            ATUIN_WRAPPER_SETUP
            + """
        . "$1/lib/guards.sh"
        . "$1/lib/helpers.sh"
        REMOTE_DOTS_DIR="$1/dots"
        bash_preexec_imported=1
        . "$1/shell/rc.d/06-bash-history.sh"
        . "$1/shell/rc.d/23-atuin.sh"
        hash atuin
        define_atuin_wrapper
        [[ "$(hash -t atuin)" == "$ATUIN_BIN" ]] || exit 11
        rm "$ATUIN_BIN"
        . "$1/shell/rc.d/06-bash-history.sh"
        . "$1/shell/rc.d/23-atuin.sh"
        command atuin noop || exit 10
        printf 'active=%s\nfile=%s\ncommand=%s\nhooks=%s\n' "$REMOTE_SSH_ATUIN_ACTIVE" "$HISTFILE" "$(hash -t atuin)" "${#preexec_functions[@]}"
        """,
            "_",
            repo_dir,
        ],
        env=isolated_env.env
        | {
            "PATH": f"{isolated_env.bin_dir}:{alternative}:/usr/bin:/bin",
            "INIT_LOG": str(log),
            "FAIL_INIT": "0",
            "REMOTE_SSH_ENABLE_ATUIN": "1",
            "REMOTE_SSH_ENABLE_ATUIN_AUTO_IMPORT": "0",
            "ATUIN_BIN": str(isolated_env.bin_dir / "atuin"),
            "WRAPPER": wrapper,
            "WRAPPER_LOG": str(wrapper_log),
        },
    )
    assert_ok(result)
    assert f"active=1\nfile=\ncommand={alternative / 'atuin'}\nhooks=1" in result.stdout
    assert log.read_text().splitlines() == ["init"]
    assert not wrapper_log.exists()
