from __future__ import annotations

import os
from pathlib import Path

import pytest
from conftest import run_cmd
from pty_shell import PtyShell
from test_atuin_lifecycle import upstream_env as upstream_env
from test_atuin_ownership import ends
from test_atuin_ownership import event_env as event_env

SAVE_PROMPT = r'''audit_saved_pc="$(IFS=$'\n'; printf '%s' "${PROMPT_COMMAND[*]}")"'''


def prompt_arrays_supported(bash: str, env: dict[str, str]) -> bool:
    return (
        run_cmd(
            [
                bash,
                "-c",
                "(( BASH_VERSINFO[0] > 5 || (BASH_VERSINFO[0] == 5 && BASH_VERSINFO[1] >= 1) ))",
            ],
            env=env,
        ).returncode
        == 0
    )


def pending_id_file(env: dict[str, str]) -> Path:
    return Path(env["HOME"]) / "stopped-id"


@pytest.mark.parametrize("shape", ["scalar", "array", "sparse"])
@pytest.mark.parametrize("status", [0, 7])
def test_live_bare_wrapper_preserves_pipeline(
    runtime_bash: str, event_env: dict[str, str], shape: str, status: int
) -> None:
    modern = prompt_arrays_supported(runtime_bash, event_env)
    if shape != "scalar" and not modern:
        pytest.skip("PROMPT_COMMAND arrays require Bash 5.1")
    records = Path(event_env["HOME"]) / "bare-callbacks"
    with PtyShell(runtime_bash, event_env) as shell:
        shell.command('. "$REPO/shell/rc.sh"')
        shell.command(
            SAVE_PROMPT
            + r"""; audit_bare_one() { printf 'one|%s|%s|%s\n' "$?" "${BP_PIPESTATUS[*]}" "$__bp_last_argument_prev_command" >> "$HOME/bare-callbacks"; }; audit_bare_two() { printf 'two|%s|%s|%s\n' "$?" "${BP_PIPESTATUS[*]}" "$__bp_last_argument_prev_command" >> "$HOME/bare-callbacks"; }; precmd_functions+=(audit_bare_one audit_bare_two); audit_bare_wrapper() { eval "$audit_saved_pc"; }"""
        )
        setup = {
            "scalar": "PROMPT_COMMAND=audit_bare_wrapper",
            "array": "unset PROMPT_COMMAND; PROMPT_COMMAND=(audit_bare_wrapper ':')",
            "sparse": "unset PROMPT_COMMAND; PROMPT_COMMAND[2]=audit_bare_wrapper; PROMPT_COMMAND[9]=':'",
        }[shape]
        records.write_text("")
        os.write(shell.fd, (setup + f"; : EXPECTED; (exit 4) | (exit {status})\n").encode())
        shell.prompt()
        baseline = records.read_text().splitlines()
        assert len(baseline) == 2
        assert [line.split("|")[1] for line in baseline] == [str(status)] * 2
        if modern:
            assert baseline == [f"{name}|{status}|4 {status}|EXPECTED" for name in ("one", "two")]
        shell.command(": baseline-rearm")
        for _ in range(2):
            records.write_text("")
            os.write(
                shell.fd,
                (
                    setup
                    + '; printf "%s" "$ATUIN_HISTORY_ID" > "$HOME/stopped-id"; '
                    + "REMOTE_SSH_ENABLE_ATUIN=0; rcrc; : EXPECTED; "
                    + f"(exit 4) | (exit {status})\n"
                ).encode(),
            )
            shell.prompt()
            stopped = pending_id_file(event_env).read_text()
            shell.until(lambda stopped=stopped: bool(ends(event_env, stopped)))
            assert ends(event_env, stopped) == [("end", stopped, str(status))]
            assert records.read_text().splitlines() == baseline
            records.write_text("")
            os.write(shell.fd, b": NEXT; (exit 2) | (exit 3)\n")
            shell.prompt()
            assert len(records.read_text().splitlines()) == 2
            if modern:
                assert records.read_text().splitlines() == [
                    f"{name}|3|2 3|NEXT" for name in ("one", "two")
                ]
            assert ends(event_env, stopped) == [("end", stopped, str(status))]
            shell.command("REMOTE_SSH_ENABLE_ATUIN=1; rcrc")


def test_full_reload_cooperates_with_surrounding_prompt_hooks(
    runtime_bash: str, event_env: dict[str, str]
) -> None:
    from conftest import write_executable

    bindir = Path(event_env["PATH"].split(":")[0])
    write_executable(
        bindir / "starship",
        r"""#!/bin/sh
    cat <<'INIT'
    [[ -n "${bash_preexec_imported:-}" ]] || return 81
    if ! declare -F starship_precmd >/dev/null; then
      starship_precmd() { printf 'starship|%s|%s\n' "$?" "${BP_PIPESTATUS[*]}" >> "$HOME/surrounding"; }
      precmd_functions+=(starship_precmd)
    fi
    INIT
    """,
    )
    write_executable(
        bindir / "zoxide",
        r"""#!/bin/sh
    cat <<'INIT'
    if ! declare -F __zoxide_hook >/dev/null; then
      __zoxide_hook() { printf 'zoxide|%s|%s\n' "$?" "${BP_PIPESTATUS[*]}" >> "$HOME/surrounding"; }
      precmd_functions+=(__zoxide_hook)
    fi
    INIT
    """,
    )
    records = Path(event_env["HOME"]) / "surrounding"
    with PtyShell(runtime_bash, event_env) as shell:
        shell.command('. "$REPO/shell/rc.sh"')
        records.write_text("")
        shell.command(": baseline; (exit 7)", status=7)
        baseline = records.read_text().splitlines()
        assert [row.split("|")[:2] for row in baseline] == [["zoxide", "7"], ["starship", "7"]]
        for _ in range(2):
            records.write_text("")
            shell.command("REMOTE_SSH_ENABLE_ATUIN=0; rcrc; rcrc; (exit 7)", status=7)
            assert records.read_text().splitlines() == baseline
            shell.command('[[ "${precmd_functions[*]}" == *"__atuin_precmd"* ]]')
