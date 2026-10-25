from __future__ import annotations

from pathlib import Path

import pytest
from conftest import run_cmd
from pty_shell import PtyShell
from test_atuin_lifecycle import upstream_env as upstream_env


def events(env: dict[str, str]) -> list[tuple[str, str, str]]:
    file = Path(env["ATUIN_EVENTS"])
    return (
        [tuple(line.split("\t", 2)) for line in file.read_text().splitlines()]
        if file.exists()
        else []
    )


def history_id(env: dict[str, str], marker: str) -> str:
    found = [entry for entry in events(env) if entry[0] == "start" and marker in entry[2]]
    assert len(found) == 1, found
    return found[0][1]


def ends(env: dict[str, str], entry_id: str) -> list[tuple[str, str, str]]:
    return [entry for entry in events(env) if entry[:2] == ("end", entry_id)]


@pytest.fixture
def event_env(upstream_env: dict[str, str], repo_dir: Path) -> dict[str, str]:
    home = Path(upstream_env["HOME"])
    return upstream_env | {
        "REPO": str(repo_dir),
        "ATUIN_EVENTS": str(home / "history.events"),
        "ATUIN_UNIQUE_IDS": "1",
        "FZF_CALLS": str(home / "fzf.calls"),
        "ATUIN_BIN": str(Path(upstream_env["PATH"].split(":")[0]) / "atuin"),
    }


@pytest.mark.parametrize("mode", ["emacs", "vi"])
@pytest.mark.parametrize("scenario", ["normal", "disabled", "missing", "prior-fzf"])
def test_external_atuin_keeps_default_bindings(
    runtime_bash: str, event_env: dict[str, str], mode: str, scenario: str
) -> None:
    with PtyShell(runtime_bash, event_env) as shell:
        shell.command(
            '. "$REPO/lib/guards.sh"; . "$REPO/lib/helpers.sh"; REMOTE_DOTS_DIR="$REPO/dots"'
        )
        if scenario == "prior-fzf":
            shell.command(
                'REMOTE_SSH_ENABLE_ATUIN=0; . "$REPO/shell/rc.d/20-fzf.sh"; REMOTE_SSH_ENABLE_ATUIN=1'
            )
        shell.command('__atuin_bind_ctrl_r=true; __atuin_bind_up_arrow=true; . "$ATUIN_SOURCE"')
        shell.command(
            r'''audit_bindings() { local map line; for map in emacs vi-insert vi-command; do while IFS= read -r line; do case "$line" in '"\C-r":'*|'"/":'*) printf '%s|%s\n' "$map" "$line";; esac; done < <(bind -m "$map" -s); done; }; audit_before="$(audit_bindings)"'''
        )
        if scenario == "missing":
            shell.command('mv "$ATUIN_BIN" "$ATUIN_BIN.saved"')
        if scenario == "disabled":
            shell.command("REMOTE_SSH_ENABLE_ATUIN=0")
        # Inspect the pending ID before a legitimate external prompt hook can
        # finish it. Our cleanup must not clear another integration's state.
        shell.command(
            'ATUIN_HISTORY_ID=foreign-pending; . "$REPO/shell/rc.sh"; '
            '[[ "$ATUIN_HISTORY_ID" == foreign-pending && "$(audit_bindings)" == "$audit_before" ]]'
        )
        for _ in range(2):
            shell.command(
                'rcrc; [[ "$(audit_bindings)" == "$audit_before" && "$__atuin_initialized" == true && "$REMOTE_SSH_ATUIN_ACTIVE" == 0 ]]'
            )
        if scenario == "missing":
            shell.command('mv "$ATUIN_BIN.saved" "$ATUIN_BIN"')
        shell.command(f"set -o {mode}")
        calls = Path(event_env["ATUIN_CALLS"])
        shell.keypress(
            b"\x12",
            lambda: any(line.startswith("search ") for line in calls.read_text().splitlines()),
        )
        assert not Path(event_env["FZF_CALLS"]).exists()
        assert not any(line.startswith("init ") for line in calls.read_text().splitlines())


@pytest.mark.parametrize(
    "scenario",
    [
        "disable",
        "zero",
        "repeat",
        "compound",
        "compound-active",
        "new-live",
        "remove",
        "late-remove",
        "helper-missing",
        "late-helper-missing",
        "end-failing",
        "sentinel",
        "no-prompt",
    ],
)
def test_owned_history_detach_completes_at_first_prompt(
    runtime_bash: str, event_env: dict[str, str], scenario: str
) -> None:
    with PtyShell(runtime_bash, event_env) as shell:
        shell.command('. "$REPO/shell/rc.sh"')
        shell.command(
            'audit_saved_precmd="$(declare -f __atuin_precmd)"; audit_saved_prompt="$(declare -p PROMPT_COMMAND)"; audit_user_hook() { :; }; precmd_functions+=(audit_user_hook); preexec_functions+=(audit_user_hook)'
        )
        body = ": audit-stop; REMOTE_SSH_ENABLE_ATUIN=0; rcrc"
        discarded = scenario in {
            "remove",
            "late-remove",
            "helper-missing",
            "late-helper-missing",
            "sentinel",
            "no-prompt",
        }
        if scenario == "compound":
            body += "; REMOTE_SSH_ENABLE_ATUIN=1; rcrc; REMOTE_SSH_ENABLE_ATUIN=0; rcrc"
        elif scenario == "compound-active":
            body += "; REMOTE_SSH_ENABLE_ATUIN=1; rcrc"
        elif scenario == "new-live":
            body += "; __atuin_preexec audit-new-live; REMOTE_SSH_ENABLE_ATUIN=1; rcrc"
        elif scenario == "remove":
            body = ': audit-stop; mv "$ATUIN_BIN" "$ATUIN_BIN.saved"; rcrc'
        elif scenario == "helper-missing":
            body = ": audit-stop; unset -f __atuin_precmd; REMOTE_SSH_ENABLE_ATUIN=0; rcrc"
        elif scenario == "late-helper-missing":
            body += "; unset -f __atuin_precmd"
        elif scenario == "late-remove":
            body += '; mv "$ATUIN_BIN" "$ATUIN_BIN.saved"'
        elif scenario == "end-failing":
            body = "export FAIL_HISTORY_END=1; " + body
        elif scenario == "sentinel":
            body = ": audit-stop; ATUIN_HISTORY_ID=__bash_preexec_failure__; REMOTE_SSH_ENABLE_ATUIN=0; rcrc"
        elif scenario == "no-prompt":
            body = ": audit-stop; PROMPT_COMMAND=; REMOTE_SSH_ENABLE_ATUIN=0; rcrc"
        stop_status = 0 if scenario == "zero" else 7
        shell.command(body + f"; (exit {stop_status})", status=stop_status)
        stopped = history_id(event_env, "audit-stop")
        if not discarded:
            shell.until(lambda: len(ends(event_env, stopped)) == 1)
            assert ends(event_env, stopped) == [("end", stopped, str(stop_status))]
        else:
            assert not ends(event_env, stopped)
        if scenario == "new-live":
            newer_ids = [
                entry[1]
                for entry in events(event_env)
                if entry[0] == "start" and entry[2] == "history start -- audit-new-live"
            ]
            assert len(newer_ids) == 1
            newer = newer_ids[0]
            shell.until(lambda: len(ends(event_env, newer)) == 1)
            assert newer != stopped
            assert ends(event_env, newer) == [("end", newer, "7")]
        if scenario in {"compound-active", "new-live"}:
            # Active checks are themselves recorded after the first prompt;
            # neither the regular hook nor a new detach may reuse the old ID.
            shell.command(
                '[[ "$REMOTE_SSH_ATUIN_ACTIVE" == 1 && "${REMOTE_SSH_ATUIN_PENDING_ID:-}" == "" && " ${precmd_functions[*]} " != *" remote_atuin_finish_detached_history "* ]]'
            )
            assert len(ends(event_env, stopped)) == 1
            return
        shell.command(
            '[[ "$ATUIN_HISTORY_ID" == "" && "${REMOTE_SSH_ATUIN_PENDING_ID:-}" == "" && "$REMOTE_SSH_ATUIN_ACTIVE" == 0 ]] && '
            '[[ " ${precmd_functions[*]} " == *" audit_user_hook "* && " ${precmd_functions[*]} " != *" remote_atuin_finish_detached_history "* ]]'
        )
        shell.command(": audit-fallback")
        assert not any(
            "audit-fallback" in entry[2] for entry in events(event_env) if entry[0] == "start"
        )
        if scenario == "repeat":
            shell.command("rcrc; rcrc")
        if scenario in {"remove", "late-remove"}:
            shell.command('mv "$ATUIN_BIN.saved" "$ATUIN_BIN"')
        elif scenario in {"helper-missing", "late-helper-missing"}:
            shell.command('eval "$audit_saved_precmd"')
        elif scenario == "no-prompt":
            shell.command('eval "$audit_saved_prompt"')
        shell.command(
            'export FAIL_HISTORY_END=0; REMOTE_SSH_ENABLE_ATUIN=1; rcrc; [[ "$REMOTE_SSH_ATUIN_ACTIVE" == 1 ]]'
        )
        shell.command(": audit-next")
        next_id = history_id(event_env, "audit-next")
        shell.until(lambda: len(ends(event_env, next_id)) == 1)
        assert next_id != stopped
        assert len(ends(event_env, stopped)) == (0 if discarded else 1)
        assert not any(entry[1] == "__bash_preexec_failure__" for entry in events(event_env))


@pytest.mark.parametrize("failure", ["cli", "partial"])
def test_failed_owned_initialization_keeps_working_fzf(
    runtime_bash: str, event_env: dict[str, str], failure: str
) -> None:
    env = event_env | {
        "FAIL_INIT": "1" if failure == "cli" else "0",
        "FAIL_AFTER_SOURCE": "1" if failure == "partial" else "0",
    }
    with PtyShell(runtime_bash, env) as shell:
        shell.command(
            '. "$REPO/shell/rc.sh"; [[ "$REMOTE_SSH_ATUIN_ACTIVE" == 0 && "$REMOTE_SSH_FZF_HISTORY_BOUND" == 1 ]]'
        )
        shell.command(
            'rcrc; [[ "$REMOTE_SSH_ATUIN_ACTIVE" == 0 && "$REMOTE_SSH_FZF_HISTORY_BOUND" == 1 ]]'
        )
        shell.keypress(b"\x12", lambda: Path(env["FZF_CALLS"]).exists())
        calls = Path(env["ATUIN_CALLS"]).read_text().splitlines()
        assert sum(line.startswith("init ") for line in calls) == (2 if failure == "cli" else 1)


def test_active_reload_keeps_entry_until_its_command_finishes(
    runtime_bash: str, event_env: dict[str, str]
) -> None:
    with PtyShell(runtime_bash, event_env) as shell:
        shell.command('. "$REPO/shell/rc.sh"')
        shell.command(
            ': audit-active; audit_entry="$ATUIN_HISTORY_ID"; rcrc; rcrc; [[ "$ATUIN_HISTORY_ID" == "$audit_entry" && "${REMOTE_SSH_ATUIN_PENDING_ID:-}" == "" ]] || exit 20; (exit 9)',
            status=9,
        )
        entry_id = history_id(event_env, "audit-active")
        shell.until(lambda: len(ends(event_env, entry_id)) == 1)
        assert ends(event_env, entry_id) == [("end", entry_id, "9")]


SAVE_PROMPT = r'''audit_saved_prompt="$(declare -p PROMPT_COMMAND)"; audit_saved_pc="$(IFS=$'\n'; printf '%s' "${PROMPT_COMMAND[*]}")"'''


def pending_id_file(env: dict[str, str]) -> Path:
    return Path(env["HOME"]) / "stopped-id"


def assert_pending_cleared(shell: PtyShell) -> None:
    shell.command(
        '[[ -z "${REMOTE_SSH_ATUIN_PENDING_ID:-}" && '
        '-z "${REMOTE_SSH_ATUIN_PENDING_TIME:-}" && '
        '-z "${REMOTE_SSH_ATUIN_PENDING_CONTEXT:-}" && '
        '-z "${REMOTE_SSH_ATUIN_PENDING_TOKEN:-}" && '
        '-z "${REMOTE_SSH_ATUIN_PENDING_PROLOGUE:-}" && '
        '-z "${REMOTE_SSH_ATUIN_PENDING_REPLACED:-}" && '
        '-z "${REMOTE_SSH_ATUIN_PENDING_LAYOUT+x}" && '
        '-z "${__rs_as:-}" && ${#__rs_ap[@]} == 0 && '
        '-z "${__rs_prompt_captured+x}" && -z "${__rs_prompt_pipeline+x}" && '
        "\"${PROMPT_COMMAND[*]:-}\" != *'${__rs_ap['* && "
        '" ${precmd_functions[*]} " != *" remote_atuin_finish_detached_history "* && '
        '" ${precmd_functions[*]} " != *" remote_atuin_restore_prompt_pipeline "* ]]'
    )


@pytest.mark.parametrize("context", ["direct", "function", "source"])
@pytest.mark.parametrize("status", [0, 7])
@pytest.mark.parametrize("prompt", ["bare", "prefix", "suffix", "sourced", "array", "sparse"])
def test_prompt_wrapper_finishes_owned_history(
    runtime_bash: str, event_env: dict[str, str], context: str, status: int, prompt: str
) -> None:
    if (
        prompt in {"array", "sparse"}
        and run_cmd(
            [
                runtime_bash,
                "-c",
                "(( BASH_VERSINFO[0] > 5 || (BASH_VERSINFO[0] == 5 && BASH_VERSINFO[1] >= 1) ))",
            ],
            env=event_env,
        ).returncode
    ):
        pytest.skip("PROMPT_COMMAND arrays require Bash 5.1")
    prompts = {
        "bare": "PROMPT_COMMAND=audit_prompt_wrapper",
        "prefix": r"""PROMPT_COMMAND=$'audit_prompt_status=$?\n:\n__bp_set_ret_value "$audit_prompt_status"\naudit_prompt_wrapper' """,
        "suffix": r"PROMPT_COMMAND=$'audit_prompt_wrapper\n:'",
        "sourced": """PROMPT_COMMAND='. "$HOME/prompt.sh"' """,
        "array": "PROMPT_COMMAND=(audit_prompt_wrapper ':')",
        "sparse": "unset PROMPT_COMMAND; PROMPT_COMMAND[2]=audit_prompt_wrapper; PROMPT_COMMAND[9]=':'",
    }
    body = (
        'printf "%s" "$ATUIN_HISTORY_ID" > "$HOME/stopped-id"; '
        'audit_prompt_wrapper() { eval "$audit_saved_pc"; }; '
        f"{prompts[prompt]}; REMOTE_SSH_ENABLE_ATUIN=0; rcrc; "
        f"(exit {status})"
    )
    (Path(event_env["HOME"]) / "prompt.sh").write_text("audit_prompt_wrapper\n")
    with PtyShell(runtime_bash, event_env) as shell:
        shell.command('. "$REPO/shell/rc.sh"')
        # bash-preexec replaces its deferred installer at the first prompt.
        shell.command(SAVE_PROMPT)
        shell.command(
            'audit_user_callback() { printf "user\\n" >> "$HOME/user-prompts"; }; '
            "precmd_functions+=(audit_user_callback)"
        )
        if context == "function":
            shell.command(f"audit_disable() {{\n{body}\n}}")
            command = "audit_disable"
        elif context == "source":
            (Path(event_env["HOME"]) / "disable.sh").write_text(body.replace("; ", ";\n"))
            command = '. "$HOME/disable.sh"'
        else:
            command = body
        user_prompts = Path(event_env["HOME"]) / "user-prompts"
        user_prompts.write_text("")
        shell.command(command, status=status)
        entry = pending_id_file(event_env).read_text()
        shell.until(lambda: bool(ends(event_env, entry)))
        assert ends(event_env, entry) == [("end", entry, str(status))]
        assert user_prompts.read_text().splitlines() == ["user"]
        assert_pending_cleared(shell)
        shell.command('[[ " ${precmd_functions[*]} " == *" audit_user_callback "* ]]')
        assert len(ends(event_env, entry)) == 1


@pytest.mark.parametrize("history", ["normal", "off", "filtered", "cleared"])
@pytest.mark.parametrize("prompt_loss", ["unset", "empty"])
@pytest.mark.parametrize(
    "restore", ["before-reload", "after-reload", "callback", "inactive-reload"]
)
def test_lost_prompt_expires_pending_history(
    runtime_bash: str,
    event_env: dict[str, str],
    history: str,
    prompt_loss: str,
    restore: str,
) -> None:
    with PtyShell(runtime_bash, event_env) as shell:
        shell.command('. "$REPO/shell/rc.sh"')
        shell.command(SAVE_PROMPT)
        if history == "off":
            shell.command("set +o history")
        elif history == "filtered":
            shell.command("HISTIGNORE='*'")
        loss = "unset PROMPT_COMMAND" if prompt_loss == "unset" else "PROMPT_COMMAND="
        shell.command(
            'printf "%s" "$ATUIN_HISTORY_ID" > "$HOME/stopped-id"; '
            f"REMOTE_SSH_ENABLE_ATUIN=0; rcrc; {loss}; (exit 7)",
            status=7,
        )
        entry = pending_id_file(event_env).read_text()
        assert entry
        if history == "cleared":
            shell.command("history -c")
        shell.command(": audit-fallback-one")
        shell.command(": audit-fallback-two")
        if restore == "inactive-reload":
            shell.command("rcrc; rcrc")
            assert_pending_cleared(shell)
        if restore == "callback":
            shell.command('eval "$audit_saved_prompt"; (exit 3)', status=3)
        else:
            activate = "REMOTE_SSH_ENABLE_ATUIN=1; rcrc"
            restore_prompt = 'eval "$audit_saved_prompt"'
            parts = (
                [restore_prompt, activate]
                if restore == "before-reload"
                else [activate, restore_prompt]
            )
            shell.command("; ".join(parts) + "; (exit 3)", status=3)
        assert_pending_cleared(shell)
        assert not ends(event_env, entry)
        shell.command("REMOTE_SSH_ENABLE_ATUIN=1; rcrc; set -o history; unset HISTIGNORE")
        shell.command(": audit-after-loss")
        newer = history_id(event_env, ": audit-after-loss")
        shell.until(lambda: bool(ends(event_env, newer)))
        assert len(ends(event_env, newer)) == 1
        assert not ends(event_env, entry)


@pytest.mark.parametrize("context", ["function", "source"])
def test_multiline_reload_keeps_its_outer_command_context(
    runtime_bash: str, event_env: dict[str, str], context: str
) -> None:
    body = """printf "%s" "$ATUIN_HISTORY_ID" > "$HOME/stopped-id"
REMOTE_SSH_ENABLE_ATUIN=0
rcrc
REMOTE_SSH_ENABLE_ATUIN=1
rcrc
REMOTE_SSH_ENABLE_ATUIN=0
rcrc
(exit 7)"""
    with PtyShell(runtime_bash, event_env) as shell:
        shell.command('. "$REPO/shell/rc.sh"')
        if context == "function":
            shell.command(f"audit_toggle() {{\n{body}\n}}")
            command = "audit_toggle"
        else:
            (Path(event_env["HOME"]) / "toggle.sh").write_text(body)
            command = '. "$HOME/toggle.sh"'
        shell.command(command, status=7)
        entry = pending_id_file(event_env).read_text()
        shell.until(lambda: bool(ends(event_env, entry)))
        assert ends(event_env, entry) == [("end", entry, "7")]
        assert_pending_cleared(shell)


def test_ambiguous_multiline_input_discards_pending_history(
    runtime_bash: str, event_env: dict[str, str]
) -> None:
    with PtyShell(runtime_bash, event_env) as shell:
        shell.command('. "$REPO/shell/rc.sh"')
        shell.command(
            '{\n printf "%s" "$ATUIN_HISTORY_ID" > "$HOME/stopped-id"\n '
            "REMOTE_SSH_ENABLE_ATUIN=0; rcrc\n (exit 7)\n}",
            status=7,
        )
        entry = pending_id_file(event_env).read_text()
        assert_pending_cleared(shell)
        shell.command("REMOTE_SSH_ENABLE_ATUIN=1; rcrc")
        shell.command(": audit-after-ambiguous")
        newer = history_id(event_env, ": audit-after-ambiguous")
        shell.until(lambda: bool(ends(event_env, newer)))
        assert not ends(event_env, entry)
