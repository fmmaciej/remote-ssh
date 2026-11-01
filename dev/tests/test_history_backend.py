from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from conftest import IsolatedEnv, assert_ok, run_cmd, write_executable
from test_atuin_lifecycle import upstream_env as upstream_env


@pytest.mark.parametrize(
    "backend", ["working", "disabled", "absent", "failing", "empty", "partial"]
)
@pytest.mark.parametrize("choice", ["default", "custom", "empty", "null"])
def test_initial_choice_is_frozen_through_full_reload(
    repo_dir: Path, runtime_bash: str, upstream_env: dict[str, str], backend: str, choice: str
) -> None:
    bin_dir = Path(upstream_env["PATH"].split(":")[0])
    atuin = bin_dir / "atuin"
    if backend == "absent":
        atuin.rename(bin_dir / "atuin.saved")
    if backend == "empty":
        write_executable(atuin, '#!/bin/sh\nprintf "init %s\\n" "$*" >> "$ATUIN_CALLS"\nexit 0\n')
    env = upstream_env | {
        "REPO": str(repo_dir),
        "REMOTE_SSH_ENABLE_ATUIN": "0" if backend == "disabled" else "1",
        "FAIL_INIT": "1" if backend == "failing" else "0",
        "FAIL_AFTER_SOURCE": "1" if backend == "partial" else "0",
    }
    env.pop("HISTFILE", None)
    history = str(Path(env["HOME"]) / (".bash_history" if choice == "default" else "custom"))
    if choice != "default":
        env["HISTFILE"] = {"custom": history, "empty": "", "null": "/dev/null"}[choice]
    expected = "" if backend == "working" else env.get("HISTFILE", history)
    result = run_cmd(
        [
            runtime_bash,
            "--noprofile",
            "--norc",
            "-ic",
            r"""
      . "$REPO/shell/rc.sh"
      before="$REMOTE_SSH_HISTORY_BACKEND:$HISTFILE:${preexec_functions[*]}:${precmd_functions[*]}"
      bind -m emacs '"\C-r":"later-user-edit"'
      REMOTE_SSH_ENABLE_ATUIN=1
      [[ "$REMOTE_SSH_HISTORY_BACKEND" != atuin ]] || REMOTE_SSH_ENABLE_ATUIN=0
      [[ ! -f "$HOME/../bin/atuin.saved" ]] || mv "$HOME/../bin/atuin.saved" "$HOME/../bin/atuin"
      rcrc; rcrc
      [[ "$REMOTE_SSH_HISTORY_BACKEND:$HISTFILE:${preexec_functions[*]}:${precmd_functions[*]}" == "$before" ]] || exit 11
      [[ "$(bind -m emacs -s)" == *'"\C-r": "later-user-edit"'* ]] || exit 12
      printf 'backend=%s\nfile=%s\npreexec=%s\n' "$REMOTE_SSH_HISTORY_BACKEND" "$HISTFILE" "${bash_preexec_imported:-missing}"
    """,
        ],
        env=env,
    )
    assert_ok(result)
    assert (
        f"backend={'atuin' if backend == 'working' else 'bash'}\nfile={expected}\n" in result.stdout
    )
    if backend in {"disabled", "absent"}:
        assert "preexec=missing" in result.stdout
    calls = Path(env["ATUIN_CALLS"])
    assert (
        sum(x.startswith("init ") for x in calls.read_text().splitlines()) == 1
        if calls.exists()
        else backend in {"disabled", "absent"}
    )
    if backend in {"disabled", "absent"}:
        fresh = run_cmd(
            [
                runtime_bash,
                "--noprofile",
                "--norc",
                "-ic",
                '. "$REPO/shell/rc.sh"; echo "$REMOTE_SSH_HISTORY_BACKEND"',
            ],
            env=env | {"REMOTE_SSH_ENABLE_ATUIN": "1"},
        )
        assert_ok(fresh)
        assert fresh.stdout.strip() == "atuin"


@pytest.mark.parametrize("wrapper", ["alias", "function"])
@pytest.mark.parametrize("binary", [True, False])
def test_executable_lookup_ignores_aliases_and_functions(
    repo_dir: Path, runtime_bash: str, upstream_env: dict[str, str], wrapper: str, binary: bool
) -> None:
    if not binary:
        (Path(upstream_env["PATH"].split(":")[0]) / "atuin").unlink()
    result = run_cmd(
        [
            runtime_bash,
            "--noprofile",
            "--norc",
            "-ic",
            r"""
      case "$WRAPPER" in
        alias) alias atuin='false' ;;
        function) atuin() { return 91; } ;;
      esac
      . "$REPO/shell/rc.sh"
      echo "$REMOTE_SSH_HISTORY_BACKEND:$(type -t atuin)"
    """,
        ],
        env=upstream_env | {"REPO": str(repo_dir), "WRAPPER": wrapper},
    )
    assert_ok(result)
    assert result.stdout.strip() == f"{'atuin' if binary else 'bash'}:{wrapper}"


@pytest.mark.parametrize("choice", ["default", "custom", "empty", "null"])
def test_fallback_history_persists_without_overriding_explicit_policy(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str, choice: str
) -> None:
    env = isolated_env.env | {
        "REMOTE_SSH_ENABLE_ATUIN": "0",
        "REMOTE_SSH_CONFIG": "0",
        "REMOTE_SSH_WELCOME": "0",
        "REMOTE_SSH_UPDATE_CHECK": "0",
    }
    env.pop("HISTFILE", None)
    history = isolated_env.home / ("custom-history" if choice == "custom" else ".bash_history")
    if choice != "default":
        env["HISTFILE"] = {"custom": str(history), "empty": "", "null": "/dev/null"}[choice]
    result = subprocess.run(
        [runtime_bash, "--noprofile", "--norc", "-i"],
        input=f'. "{repo_dir}/shell/rc.sh"\nhistory -s audit-persisted-marker\nrcrc\nexit\n',
        text=True,
        capture_output=True,
        env=env,
    )
    assert_ok(result)
    assert (
        ("audit-persisted-marker" in history.read_text())
        if choice in {"default", "custom"}
        else not history.exists()
    )


@pytest.mark.parametrize("existing", [False, True])
@pytest.mark.parametrize("vendor", ["missing", "unreadable"])
def test_missing_preexec_vendor_selects_fallback_or_reuses_user_library(
    repo_dir: Path, runtime_bash: str, upstream_env: dict[str, str], existing: bool, vendor: str
) -> None:
    if vendor == "unreadable":
        path = Path(upstream_env["HOME"]) / "vendor-root/tools/vendors/bash-preexec.sh"
        path.parent.mkdir(parents=True)
        path.write_text("echo unexpected-vendor-load\n")
        path.chmod(0)
    result = run_cmd(
        [
            runtime_bash,
            "--noprofile",
            "--norc",
            "-ic",
            r"""
      . "$REPO/lib/guards.sh"; . "$REPO/lib/helpers.sh"
      REMOTE_ENV_DIR="$HOME/vendor-root"; REMOTE_DOTS_DIR="$REPO/dots"
      [[ "$EXISTING" != 1 ]] || bash_preexec_imported=user-library
      . "$REPO/shell/rc.d/05-bash-preexec.sh"
      . "$REPO/shell/rc.d/06-bash-history.sh"
      . "$REPO/shell/rc.d/20-skim.sh"
      . "$REPO/shell/rc.d/23-atuin.sh"
      echo "$REMOTE_SSH_HISTORY_BACKEND:${bash_preexec_imported:-missing}"
    """,
        ],
        env=upstream_env | {"REPO": str(repo_dir), "EXISTING": str(int(existing))},
    )
    assert_ok(result)
    assert result.stdout.strip() == ("atuin:user-library" if existing else "bash:missing")


def test_noninteractive_modules_install_no_history_hooks(
    repo_dir: Path, runtime_bash: str, upstream_env: dict[str, str]
) -> None:
    result = run_cmd(
        [
            runtime_bash,
            "-c",
            r"""
      . "$REPO/lib/guards.sh"; . "$REPO/lib/helpers.sh"
      for module in 05-bash-preexec 06-bash-history 20-skim 23-atuin; do . "$REPO/shell/rc.d/$module.sh"; done
      [[ -z "${REMOTE_SSH_HISTORY_BACKEND+x}" && -z "${bash_preexec_imported+x}" && -z "${preexec_functions+x}" ]]
    """,
        ],
        env=upstream_env | {"REPO": str(repo_dir)},
    )
    assert_ok(result)


def test_new_interactive_child_makes_its_own_selection(
    repo_dir: Path, runtime_bash: str, upstream_env: dict[str, str]
) -> None:
    result = run_cmd(
        [
            runtime_bash,
            "--noprofile",
            "--norc",
            "-ic",
            r"""
      export REMOTE_SSH_ENABLE_ATUIN=0
      . "$REPO/shell/rc.sh"
      [[ "$REMOTE_SSH_HISTORY_BACKEND" == bash ]] || exit 10
      REMOTE_SSH_ENABLE_ATUIN=1 "$BASH" --noprofile --norc -ic '. "$REPO/shell/rc.sh"; [[ "$REMOTE_SSH_HISTORY_BACKEND" == atuin ]]' || exit 11
      [[ "$REMOTE_SSH_HISTORY_BACKEND" == bash ]] || exit 12
    """,
        ],
        env=upstream_env | {"REPO": str(repo_dir)},
    )
    assert_ok(result)


def test_removing_or_changing_path_does_not_probe_or_switch_on_reload(
    repo_dir: Path, runtime_bash: str, upstream_env: dict[str, str]
) -> None:
    result = run_cmd(
        [
            runtime_bash,
            "--noprofile",
            "--norc",
            "-ic",
            r"""
      . "$REPO/shell/rc.sh"
      mv "$ATUIN_BIN" "$ATUIN_BIN.saved"
      PATH=/usr/bin:/bin
      remote_atuin_available() { echo unexpected-probe; return 1; }
      REMOTE_SSH_ENABLE_ATUIN=0
      rcrc; rcrc
      [[ "$REMOTE_SSH_HISTORY_BACKEND" == atuin && "$HISTFILE" == '' && "${REMOTE_SSH_SKIM_HISTORY_BOUND:-0}" == 0 ]] || exit 10
    """,
        ],
        env=upstream_env
        | {
            "REPO": str(repo_dir),
            "ATUIN_BIN": str(Path(upstream_env["PATH"].split(":")[0]) / "atuin"),
        },
    )
    assert_ok(result)
    assert "unexpected-probe" not in result.stdout


def test_native_readline_fallback_when_skim_is_absent(
    repo_dir: Path, runtime_bash: str, upstream_env: dict[str, str]
) -> None:
    (Path(upstream_env["PATH"].split(":")[0]) / "sk").unlink()
    result = run_cmd(
        [
            runtime_bash,
            "--noprofile",
            "--norc",
            "-ic",
            r"""
      bind -m emacs '"\C-r":reverse-search-history'
      bind -m vi-insert '"\C-r":reverse-search-history'
      . "$REPO/shell/rc.sh"
      [[ "$REMOTE_SSH_HISTORY_BACKEND" == bash && "${REMOTE_SSH_SKIM_HISTORY_BOUND:-0}" == 0 ]] || exit 10
      [[ "$(bind -m emacs -p)" == *'"\C-r": reverse-search-history'* ]] || exit 11
      [[ "$(bind -m vi-insert -p)" == *'"\C-r": reverse-search-history'* ]] || exit 12
    """,
        ],
        env=upstream_env | {"REPO": str(repo_dir), "REMOTE_SSH_ENABLE_ATUIN": "0"},
    )
    assert_ok(result)
