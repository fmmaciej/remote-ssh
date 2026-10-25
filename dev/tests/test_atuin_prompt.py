from __future__ import annotations

import os
import shlex
from pathlib import Path

import pytest
from conftest import run_cmd, write_executable
from pty_shell import PtyShell
from test_atuin_lifecycle import upstream_env as upstream_env
from test_atuin_ownership import (
    SAVE_PROMPT,
    assert_pending_cleared,
    ends,
    history_id,
    pending_id_file,
)
from test_atuin_ownership import event_env as event_env

# Keep the audited serialized format independently of the runtime generator:
# already-open shells may restore this text after loading repaired functions.
LEGACY_PROMPT = r'''printf -v audit_cached_pc '"${__rs_ap[%s]:-__rs_astale}" "$?" %s 1 "${__rs_as:=%s}" "$_"\n__bp_interactive_mode' "$REMOTE_SSH_ATUIN_PENDING_TOKEN" "$REMOTE_SSH_ATUIN_PENDING_TOKEN" "$REMOTE_SSH_ATUIN_PENDING_TOKEN"'''
CACHE_PROMPT = r'''audit_cached_pc="$(IFS=$'\n'; printf '%s' "${PROMPT_COMMAND[*]}")"'''


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


def startup_shell(bash: str, env: dict[str, str]) -> str:
    home = Path(env["HOME"])
    startup = home / "startup.rc"
    startup.write_text('. "$REPO/shell/rc.sh"\nPS1="REMOTE_SSH_TEST> "\n')
    launcher = home / "start-bash"
    write_executable(
        launcher,
        f"#!/bin/sh\nexec {shlex.quote(bash)} --noprofile --rcfile {shlex.quote(str(startup))} -i\n",
    )
    return str(launcher)


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
            assert_pending_cleared(shell)
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


@pytest.mark.parametrize(
    ("shape", "expected_edit", "pending_edit", "dispatch"),
    [
        ("scalar", "", "", True),
        ("exported", "", "", True),
        ("scalar", "export PROMPT_COMMAND", "export PROMPT_COMMAND", True),
        ("exported", "export -n PROMPT_COMMAND", "export -n PROMPT_COMMAND", True),
        ("array", "", "", True),
        ("sparse", "", "", True),
        ("sparse", "PROMPT_COMMAND[11]=':'", "PROMPT_COMMAND[11]=':'", True),
        (
            "array",
            "PROMPT_COMMAND[0]=audit_layout_changed",
            "PROMPT_COMMAND[1]=audit_layout_changed",
            True,
        ),
        (
            "scalar",
            "PROMPT_COMMAND=(audit_layout_wrapper); PROMPT_COMMAND[9]=':'",
            "PROMPT_COMMAND[9]=':'",
            True,
        ),
        ("scalar", "PROMPT_COMMAND=''", "unset 'PROMPT_COMMAND[1]'", False),
        ("array", "unset 'PROMPT_COMMAND[0]'", "unset 'PROMPT_COMMAND[1]'", False),
    ],
)
def test_separate_boundary_restores_prompt_layout_and_user_edits(
    runtime_bash: str,
    event_env: dict[str, str],
    shape: str,
    expected_edit: str,
    pending_edit: str,
    dispatch: bool,
) -> None:
    if not prompt_arrays_supported(runtime_bash, event_env):
        pytest.skip("Separate prompt boundaries require Bash 5.1")
    home = Path(event_env["HOME"])
    with PtyShell(runtime_bash, event_env) as shell:
        shell.command('. "$REPO/shell/rc.sh"')
        shell.command(
            SAVE_PROMPT
            + r"""; audit_layout_wrapper() { declare -p PROMPT_COMMAND > "$HOME/actual-layout"; eval "$audit_saved_pc"; }; audit_layout_changed() { audit_layout_wrapper; }"""
        )
        setup = (
            "unset PROMPT_COMMAND; "
            + {
                "scalar": "PROMPT_COMMAND=audit_layout_wrapper",
                "exported": "export PROMPT_COMMAND=audit_layout_wrapper",
                "array": "PROMPT_COMMAND=(audit_layout_wrapper ':')",
                "sparse": "PROMPT_COMMAND[2]=audit_layout_wrapper; PROMPT_COMMAND[9]=':'",
            }[shape]
        )
        body = setup + "; "
        if expected_edit:
            body += expected_edit + "; "
        body += 'declare -p PROMPT_COMMAND > "$HOME/expected-layout"; '
        body += setup + '; printf "%s" "$ATUIN_HISTORY_ID" > "$HOME/stopped-id"; '
        body += "REMOTE_SSH_ENABLE_ATUIN=0; rcrc; "
        if pending_edit:
            body += pending_edit + "; "
        shell.command(body + "(exit 7)", status=7)
        stopped = pending_id_file(event_env).read_text()
        shell.until(lambda: bool(ends(event_env, stopped)))
        if not dispatch:
            shell.command('declare -p PROMPT_COMMAND > "$HOME/actual-layout"')
        assert (home / "actual-layout").read_text() == (home / "expected-layout").read_text()
        assert_pending_cleared(shell)
        assert ends(event_env, stopped) == [("end", stopped, "7")]


@pytest.mark.parametrize("failure", ["dispatcher", "backend", "helper", "end"])
def test_separate_boundary_cleans_up_without_successful_user_dispatch(
    runtime_bash: str, event_env: dict[str, str], failure: str
) -> None:
    if not prompt_arrays_supported(runtime_bash, event_env):
        pytest.skip("Separate prompt boundaries require Bash 5.1")
    with PtyShell(runtime_bash, event_env) as shell:
        shell.command('. "$REPO/shell/rc.sh"')
        shell.command(SAVE_PROMPT + '; audit_failure_wrapper() { eval "$audit_saved_pc"; }')
        edit = {
            "dispatcher": "unset -f __bp_precmd_invoke_cmd",
            "backend": 'mv "$ATUIN_BIN" "$ATUIN_BIN.saved"',
            "helper": "unset -f __atuin_precmd",
            "end": "export FAIL_HISTORY_END=1",
        }[failure]
        shell.command(
            'PROMPT_COMMAND=audit_failure_wrapper; printf "%s" "$ATUIN_HISTORY_ID" > "$HOME/stopped-id"; '
            f"REMOTE_SSH_ENABLE_ATUIN=0; rcrc; {edit}; (exit 7)",
            status=7,
        )
        stopped = pending_id_file(event_env).read_text()
        if failure in {"dispatcher", "end"}:
            shell.until(lambda: bool(ends(event_env, stopped)))
            expected = [("end", stopped, "7")]
        else:
            expected = []
        assert ends(event_env, stopped) == expected
        assert_pending_cleared(shell)
        shell.command(": later-input")
        assert ends(event_env, stopped) == expected


@pytest.mark.parametrize("missed", [False, True])
def test_cached_separate_boundary_keeps_pipeline_after_completion_or_expiry(
    runtime_bash: str, event_env: dict[str, str], missed: bool
) -> None:
    if not prompt_arrays_supported(runtime_bash, event_env):
        pytest.skip("Separate prompt boundaries require Bash 5.1")
    records = Path(event_env["HOME"]) / "separate-callbacks"
    with PtyShell(runtime_bash, event_env) as shell:
        shell.command('. "$REPO/shell/rc.sh"')
        shell.command(
            SAVE_PROMPT
            + r"""; audit_separate_wrapper() { eval "$audit_saved_pc"; }; audit_separate_callback() { printf '%s|%s|%s\n' "$?" "${BP_PIPESTATUS[*]}" "$__bp_last_argument_prev_command" >> "$HOME/separate-callbacks"; }; precmd_functions+=(audit_separate_callback)"""
        )
        loss = "; unset PROMPT_COMMAND" if missed else ""
        shell.command(
            'PROMPT_COMMAND=audit_separate_wrapper; printf "%s" "$ATUIN_HISTORY_ID" > "$HOME/stopped-id"; '
            "REMOTE_SSH_ENABLE_ATUIN=0; rcrc; "
            f'audit_separate_pc="$(declare -p PROMPT_COMMAND)"{loss}; (exit 7)',
            status=7,
        )
        stopped = pending_id_file(event_env).read_text()
        if not missed:
            shell.until(lambda: bool(ends(event_env, stopped)))
        shell.command(": fallback-before-reload")
        shell.command("REMOTE_SSH_ENABLE_ATUIN=1; rcrc")
        results = []
        for setup in ("PROMPT_COMMAND=audit_separate_wrapper", 'eval "$audit_separate_pc"'):
            records.write_text("")
            os.write(shell.fd, (setup + "; : EXPECTED; (exit 4) | (exit 7)\n").encode())
            shell.prompt()
            results.append(records.read_text().splitlines())
        assert results == [["7|4 7|EXPECTED"]] * 2
        assert len(ends(event_env, stopped)) == (0 if missed else 1)
        assert_pending_cleared(shell)


@pytest.mark.parametrize("startup", [False, True])
@pytest.mark.parametrize("shape", ["scalar", "sparse"])
@pytest.mark.parametrize("status", [0, 7])
def test_prompt_prologue_preserves_status_order_and_pipeline(
    runtime_bash: str, event_env: dict[str, str], startup: bool, shape: str, status: int
) -> None:
    if shape == "sparse" and not prompt_arrays_supported(runtime_bash, event_env):
        pytest.skip("PROMPT_COMMAND arrays require Bash 5.1")
    launch = startup_shell(runtime_bash, event_env) if startup else runtime_bash
    home = Path(event_env["HOME"])
    callbacks = home / "callbacks"
    with PtyShell(launch, event_env) as shell:
        if not startup:
            shell.command('. "$REPO/shell/rc.sh"')
        shell.command(
            SAVE_PROMPT
            + r"""; audit_one() { printf 'one:%s:%s:%s\n' "$?" "${BP_PIPESTATUS[*]}" "$__bp_last_argument_prev_command" >> "$HOME/callbacks"; printf 'one:%s\n' "$audit_prepared" >> "$HOME/prompt-order"; }; audit_two() { printf 'two:%s:%s:%s\n' "$?" "${BP_PIPESTATUS[*]}" "$__bp_last_argument_prev_command" >> "$HOME/callbacks"; printf 'two:%s\n' "$audit_prepared" >> "$HOME/prompt-order"; }; precmd_functions+=(audit_one audit_two); audit_wrapper() { local audit_ret=$? audit_last=$_; printf 'wrapper:%s\n' "$audit_ret" >> "$HOME/prompt-order"; if __bp_set_ret_value "$audit_ret" "$audit_last"; then eval "$audit_saved_pc"; else eval "$audit_saved_pc"; fi; }; audit_tail() { printf 'tail\n' >> "$HOME/prompt-order"; }"""
        )
        # Use a file to preserve literal newlines and shell quoting without
        # adding another interactive prompt while configuring PROMPT_COMMAND.
        text = """audit_prompt_status=$? audit_prompt_last=$_ audit_prompt_pipeline=("${PIPESTATUS[@]}")
printf '%s\\n' "${audit_prompt_pipeline[*]}" > "$HOME/prefix-pipeline"
audit_prepared=new
printf 'prefix:%s\\n' "$audit_prompt_status" >> "$HOME/prompt-order"
__bp_set_ret_value "$audit_prompt_status" "$audit_prompt_last"
audit_wrapper"""
        (home / "prefix.txt").write_text(text)
        if shape == "scalar":
            setup = 'PROMPT_COMMAND="$(cat "$HOME/prefix.txt")"; PROMPT_COMMAND+=$\'\\n\'audit_tail'
        else:
            setup = 'unset PROMPT_COMMAND; PROMPT_COMMAND[2]="$(cat "$HOME/prefix.txt")"; PROMPT_COMMAND[9]=audit_tail'
        order = home / "prompt-order"
        callbacks.write_text("")
        order.write_text("")
        # The control uses the same prefix/wrapper, rather than a default
        # dispatcher that runs callbacks at a different point in the prompt.
        os.write(
            shell.fd,
            (setup + f"; audit_prepared=old; : EXPECTED; (exit 4) | (exit {status})\n").encode(),
        )
        shell.prompt()
        baseline = callbacks.read_text().splitlines()
        baseline_order = order.read_text().splitlines()
        baseline_pipeline = (home / "prefix-pipeline").read_text()
        if prompt_arrays_supported(runtime_bash, event_env):
            assert baseline_pipeline == f"4 {status}\n"
        assert len(baseline) == 2
        assert all(line.split(":")[1] == str(status) for line in baseline)
        assert baseline_order == [
            f"prefix:{status}",
            f"wrapper:{status}",
            "one:new",
            "two:new",
            "tail",
        ]
        # Legacy bash-preexec rearms at the next top-level epilogue after a
        # wrapper first caused it to normalize PROMPT_COMMAND.
        shell.command(": baseline-rearm")
        callbacks.write_text("")
        order.write_text("")
        command = (
            setup + '; printf "%s" "$ATUIN_HISTORY_ID" > "$HOME/stopped-id"; '
            f"REMOTE_SSH_ENABLE_ATUIN=0; rcrc; audit_prepared=old; : EXPECTED; (exit 4) | (exit {status})"
        )
        os.write(shell.fd, (command + "\n").encode())
        shell.prompt()
        old = pending_id_file(event_env).read_text()
        shell.until(lambda: bool(ends(event_env, old)))
        assert ends(event_env, old) == [("end", old, str(status))]
        assert order.read_text().splitlines() == baseline_order
        assert callbacks.read_text().splitlines() == baseline
        if prompt_arrays_supported(runtime_bash, event_env):
            assert (home / "prefix-pipeline").read_text() == baseline_pipeline
        if shape == "sparse":
            shell.command(
                '[[ "${PROMPT_COMMAND[2]}" == "$(cat "$HOME/prefix.txt")" && "${PROMPT_COMMAND[9]}" == audit_tail ]]'
            )
        assert_pending_cleared(shell)


@pytest.mark.parametrize("missed", [False, True])
@pytest.mark.parametrize("saved_format", ["current", "legacy"])
def test_cached_pending_prompt_keeps_normal_dispatch(
    runtime_bash: str, event_env: dict[str, str], missed: bool, saved_format: str
) -> None:
    callbacks = Path(event_env["HOME"]) / "restored-callbacks"
    with PtyShell(runtime_bash, event_env) as shell:
        shell.command('. "$REPO/shell/rc.sh"')
        shell.command(
            SAVE_PROMPT
            + r"""; audit_restored_callback() { printf 'callback\n' >> "$HOME/restored-callbacks"; }; precmd_functions+=(audit_restored_callback); audit_restored_wrapper() { eval "$audit_target_pc"; }"""
        )
        capture = CACHE_PROMPT if saved_format == "current" else LEGACY_PROMPT
        loss = "; unset PROMPT_COMMAND" if missed else ""
        shell.command(
            'printf "%s" "$ATUIN_HISTORY_ID" > "$HOME/stopped-id"; '
            f"REMOTE_SSH_ENABLE_ATUIN=0; rcrc; {capture}{loss}; (exit 7)",
            status=7,
        )
        old = pending_id_file(event_env).read_text()
        if not missed:
            shell.until(lambda: bool(ends(event_env, old)))
        else:
            shell.command(": fallback-before-restoring")
        shell.command("REMOTE_SSH_ENABLE_ATUIN=1; rcrc")
        for label, target in [("control", "audit_saved_pc"), ("cached", "audit_cached_pc")]:
            callbacks.write_text("")
            shell.command(f'audit_target_pc="${target}"; PROMPT_COMMAND=audit_restored_wrapper')
            assert callbacks.read_text().splitlines() == ["callback"]
            # The control permits the vendor's first wrapper rearm sequence;
            # both following independent inputs must then record and finish.
            shell.command(": wrapper-rearm")
            for number in (1, 2):
                marker = f": audit-{label}-{number}"
                shell.command(marker)
                current = history_id(event_env, marker)
                shell.until(lambda current=current: bool(ends(event_env, current)))
                assert ends(event_env, current) == [("end", current, "0")]
            assert len(callbacks.read_text().splitlines()) == 4
        assert len(ends(event_env, old)) == (0 if missed else 1)
        assert_pending_cleared(shell)


@pytest.mark.parametrize("shape", ["scalar", "sparse"])
@pytest.mark.parametrize("forward", ["direct", "wrapper"])
@pytest.mark.parametrize("saved_format", ["current", "legacy"])
def test_expired_prompt_keeps_pipeline_metadata(
    runtime_bash: str, event_env: dict[str, str], shape: str, forward: str, saved_format: str
) -> None:
    if shape == "sparse" and not prompt_arrays_supported(runtime_bash, event_env):
        pytest.skip("PROMPT_COMMAND arrays require Bash 5.1")
    records = Path(event_env["HOME"]) / "pipeline-callbacks"
    with PtyShell(runtime_bash, event_env) as shell:
        shell.command('. "$REPO/shell/rc.sh"')
        shell.command(
            SAVE_PROMPT
            + r"""; audit_pipeline_callback() { printf '%s|%s|%s\n' "$?" "${BP_PIPESTATUS[*]}" "$__bp_last_argument_prev_command" >> "$HOME/pipeline-callbacks"; }; precmd_functions+=(audit_pipeline_callback); audit_pipeline_wrapper() { eval "$audit_target_pc"; }"""
        )
        capture = CACHE_PROMPT if saved_format == "current" else LEGACY_PROMPT
        shell.command(f"REMOTE_SSH_ENABLE_ATUIN=0; rcrc; {capture}")
        shell.command("REMOTE_SSH_ENABLE_ATUIN=1; rcrc")
        results = []
        for target in ("audit_saved_pc", "audit_cached_pc"):
            records.write_text("")
            value = '"$audit_target_pc"' if forward == "direct" else "audit_pipeline_wrapper"
            setup = f' audit_target_pc="${target}"; '
            if shape == "scalar":
                setup += f"PROMPT_COMMAND={value}"
            else:
                setup += f"unset PROMPT_COMMAND; PROMPT_COMMAND[2]={value}; PROMPT_COMMAND[9]=':'"
            os.write(shell.fd, (setup + "; : EXPECTED; (exit 4) | (exit 7)\n").encode())
            shell.prompt()
            lines = records.read_text().splitlines()
            assert len(lines) == 1
            assert lines[0].startswith("7|")
            results.append(lines)
        assert results[1] == results[0]
        if forward == "direct" and prompt_arrays_supported(runtime_bash, event_env):
            assert results[0] == ["7|4 7|EXPECTED"]
        assert_pending_cleared(shell)


def test_pending_legacy_dispatch_map_is_upgraded_on_reload(
    runtime_bash: str, event_env: dict[str, str]
) -> None:
    with PtyShell(runtime_bash, event_env) as shell:
        shell.command('. "$REPO/shell/rc.sh"')
        shell.command(
            'printf "%s" "$ATUIN_HISTORY_ID" > "$HOME/stopped-id"; '
            "REMOTE_SSH_ENABLE_ATUIN=0; rcrc; "
            "__rs_ap[REMOTE_SSH_ATUIN_PENDING_TOKEN]=__bp_precmd_invoke_cmd; rcrc; (exit 7)",
            status=7,
        )
        old = pending_id_file(event_env).read_text()
        shell.until(lambda: bool(ends(event_env, old)))
        assert ends(event_env, old) == [("end", old, "7")]
        assert_pending_cleared(shell)


def test_cached_old_prompt_releases_an_expired_new_pending_record(
    runtime_bash: str, event_env: dict[str, str]
) -> None:
    records = Path(event_env["HOME"]) / "pending-callbacks"
    with PtyShell(runtime_bash, event_env) as shell:
        shell.command('. "$REPO/shell/rc.sh"')
        shell.command(
            r"""audit_pending_callback() { printf '%s\n' "${audit_step:-setup}" >> "$HOME/pending-callbacks"; }; precmd_functions+=(audit_pending_callback); REMOTE_SSH_ENABLE_ATUIN=0; rcrc; """
            + CACHE_PROMPT
        )
        shell.command("REMOTE_SSH_ENABLE_ATUIN=1; rcrc")
        records.write_text("")
        shell.command(
            'printf "%s" "$ATUIN_HISTORY_ID" > "$HOME/stopped-id"; '
            "REMOTE_SSH_ENABLE_ATUIN=0; rcrc; audit_step=stop; "
            'audit_pending_wrapper() { eval "$audit_cached_pc"; }; '
            "PROMPT_COMMAND=audit_pending_wrapper; (exit 7)",
            status=7,
        )
        missed = pending_id_file(event_env).read_text()
        assert missed
        shell.command("audit_step=one; : fallback-one")
        shell.command("audit_step=two; : fallback-two")
        assert records.read_text().splitlines()[-2:] == ["one", "two"]
        assert_pending_cleared(shell)
        assert not ends(event_env, missed)
        shell.command("REMOTE_SSH_ENABLE_ATUIN=1; rcrc")
        shell.command(": after-expired-new-pending")
        current = history_id(event_env, ": after-expired-new-pending")
        shell.until(lambda: bool(ends(event_env, current)))
        assert ends(event_env, current) == [("end", current, "0")]
        assert not ends(event_env, missed)


@pytest.mark.parametrize("forward", ["direct", "wrapper"])
def test_user_callback_state_and_changes_survive_prompt_delegation(
    runtime_bash: str, event_env: dict[str, str], forward: str
) -> None:
    records = Path(event_env["HOME"]) / "changed-callbacks"
    with PtyShell(runtime_bash, event_env) as shell:
        shell.command('. "$REPO/shell/rc.sh"')
        shell.command(
            SAVE_PROMPT
            + r"""; audit_user_wrapper() { eval "$audit_saved_pc"; }; audit_late_callback() { printf 'late\n' >> "$HOME/changed-callbacks"; }; audit_changing_callback() { [[ "${audit_change_hooks:-0}" == 1 ]] || return 0; printf 'state|%s|%s|%s|%s|%s|%s\n' "$status" "$force" "$last_arg" "$statement" "$replacement" "$had_vendor" >> "$HOME/changed-callbacks"; status=updated; local hook; local -a kept=(); for hook in "${precmd_functions[@]}"; do [[ "$hook" == audit_changing_callback ]] || kept+=("$hook"); done; precmd_functions=("${kept[@]}" audit_late_callback); printf 'changed\n' >> "$HOME/changed-callbacks"; }; precmd_functions+=(audit_changing_callback)"""
        )
        shell.command(
            ("PROMPT_COMMAND=audit_user_wrapper; " if forward == "wrapper" else "")
            + "status=USER_STATUS; force=USER_FORCE; last_arg=USER_LAST; statement=USER_STATEMENT; "
            "replacement=USER_REPLACEMENT; had_vendor=USER_VENDOR; "
            "audit_change_hooks=1; REMOTE_SSH_ENABLE_ATUIN=0; rcrc"
        )
        expected = [
            "state|USER_STATUS|USER_FORCE|USER_LAST|USER_STATEMENT|USER_REPLACEMENT|USER_VENDOR",
            "changed",
        ]
        assert records.read_text().splitlines() == expected
        shell.command(
            '[[ "$status" == updated && " ${precmd_functions[*]} " != *" audit_changing_callback "* && '
            '" ${precmd_functions[*]} " == *" audit_late_callback "* ]]'
        )
        assert records.read_text().splitlines() == expected + ["late"]
        assert_pending_cleared(shell)


@pytest.mark.parametrize("snapshot", ["before", "after"])
@pytest.mark.parametrize("restore", ["callback", "restore-first", "reload-first"])
def test_saved_prompt_cannot_resurrect_pending_history(
    runtime_bash: str, event_env: dict[str, str], snapshot: str, restore: str
) -> None:
    with PtyShell(runtime_bash, event_env) as shell:
        shell.command('. "$REPO/shell/rc.sh"')
        shell.command(SAVE_PROMPT)
        shell.command(
            'printf "%s" "$ATUIN_HISTORY_ID" > "$HOME/stopped-id"; '
            'REMOTE_SSH_ENABLE_ATUIN=0; rcrc; audit_after="$(declare -p PROMPT_COMMAND)"; '
            "unset PROMPT_COMMAND; (exit 7)",
            status=7,
        )
        old = pending_id_file(event_env).read_text()
        shell.command(": fallback-one")
        shell.command(": fallback-two")
        saved = "audit_saved_prompt" if snapshot == "before" else "audit_after"
        restore_command = f'eval "${saved}"'
        if restore == "callback":
            command = restore_command
        elif restore == "restore-first":
            command = restore_command + "; REMOTE_SSH_ENABLE_ATUIN=1; rcrc"
        else:
            command = "REMOTE_SSH_ENABLE_ATUIN=1; rcrc; " + restore_command
        shell.command(command + "; (exit 3)", status=3)
        assert_pending_cleared(shell)
        assert not ends(event_env, old)
        shell.command("REMOTE_SSH_ENABLE_ATUIN=1; rcrc")
        shell.command(": audit-restored-prompt")
        newer = history_id(event_env, ": audit-restored-prompt")
        shell.until(lambda: bool(ends(event_env, newer)))
        assert len(ends(event_env, newer)) == 1
        assert not ends(event_env, old)


def test_stale_prologue_does_not_touch_a_new_pending_record(
    runtime_bash: str, event_env: dict[str, str]
) -> None:
    with PtyShell(runtime_bash, event_env) as shell:
        shell.command('. "$REPO/shell/rc.sh"')
        shell.command(
            'REMOTE_SSH_ENABLE_ATUIN=0; rcrc; audit_old_prologue="$REMOTE_SSH_ATUIN_PENDING_PROLOGUE"'
        )
        shell.command("REMOTE_SSH_ENABLE_ATUIN=1; rcrc")
        shell.command(
            'printf "%s" "$ATUIN_HISTORY_ID" > "$HOME/stopped-id"; '
            'REMOTE_SSH_ENABLE_ATUIN=0; rcrc; audit_new_id="$REMOTE_SSH_ATUIN_PENDING_ID"; '
            'audit_new_token="$REMOTE_SSH_ATUIN_PENDING_TOKEN"; eval "$audit_old_prologue"; '
            '[[ "$REMOTE_SSH_ATUIN_PENDING_ID" == "$audit_new_id" && '
            '"$REMOTE_SSH_ATUIN_PENDING_TOKEN" == "$audit_new_token" ]] || exit 31; (exit 7)',
            status=7,
        )
        current = pending_id_file(event_env).read_text()
        shell.until(lambda: bool(ends(event_env, current)))
        assert ends(event_env, current) == [("end", current, "7")]
        assert_pending_cleared(shell)


@pytest.mark.parametrize("status", [0, 7])
def test_first_startup_input_completes_before_a_multiline_prompt(
    runtime_bash: str, event_env: dict[str, str], status: int
) -> None:
    with PtyShell(startup_shell(runtime_bash, event_env), event_env) as shell:
        shell.command(
            SAVE_PROMPT
            + r"""; audit_wrapper() { eval "$audit_saved_pc"; }; PROMPT_COMMAND=$'audit_status=$?\n:\n__bp_set_ret_value "$audit_status"\naudit_wrapper'; printf '%s' "$ATUIN_HISTORY_ID" > "$HOME/stopped-id"; REMOTE_SSH_ENABLE_ATUIN=0; rcrc"""
            + f"; (exit {status})",
            status=status,
        )
        old = pending_id_file(event_env).read_text()
        shell.until(lambda: bool(ends(event_env, old)))
        assert ends(event_env, old) == [("end", old, str(status))]
        assert_pending_cleared(shell)
