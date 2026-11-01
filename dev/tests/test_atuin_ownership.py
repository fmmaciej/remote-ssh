from __future__ import annotations

from pathlib import Path

import pytest
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
        "SKIM_CALLS": str(home / "sk.calls"),
        "ATUIN_BIN": str(Path(upstream_env["PATH"].split(":")[0]) / "atuin"),
    }


@pytest.mark.parametrize("mode", ["emacs", "vi"])
@pytest.mark.parametrize("scenario", ["normal", "disabled", "missing", "prior-sk"])
def test_external_atuin_keeps_default_bindings(
    runtime_bash: str, event_env: dict[str, str], mode: str, scenario: str
) -> None:
    with PtyShell(runtime_bash, event_env) as shell:
        shell.command(
            '. "$REPO/lib/guards.sh"; . "$REPO/lib/helpers.sh"; REMOTE_DOTS_DIR="$REPO/dots"'
        )
        if scenario == "prior-sk":
            shell.command(
                'REMOTE_SSH_ENABLE_ATUIN=0; . "$REPO/shell/rc.d/20-skim.sh"; REMOTE_SSH_ENABLE_ATUIN=1'
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
            'ATUIN_CONFIG_DIR=external-config; audit_history="$HISTFILE"; ATUIN_HISTORY_ID=foreign-pending; . "$REPO/shell/rc.sh"; '
            '[[ "$ATUIN_HISTORY_ID" == foreign-pending && "$(audit_bindings)" == "$audit_before" && "$ATUIN_CONFIG_DIR" == external-config && "$HISTFILE" == "$audit_history" && -z "${bash_preexec_imported+x}" ]]'
        )
        for _ in range(2):
            shell.command(
                'rcrc; [[ "$(audit_bindings)" == "$audit_before" && "$__atuin_initialized" == true && "$REMOTE_SSH_HISTORY_BACKEND" == external ]]'
            )
        if scenario == "missing":
            shell.command('mv "$ATUIN_BIN.saved" "$ATUIN_BIN"')
        shell.command(f"set -o {mode}")
        calls = Path(event_env["ATUIN_CALLS"])
        shell.keypress(
            b"\x12",
            lambda: any(line.startswith("search ") for line in calls.read_text().splitlines()),
        )
        assert not Path(event_env["SKIM_CALLS"]).exists()
        assert not any(line.startswith("init ") for line in calls.read_text().splitlines())


@pytest.mark.parametrize("failure", ["cli", "partial"])
def test_failed_owned_initialization_keeps_working_sk(
    runtime_bash: str, event_env: dict[str, str], failure: str
) -> None:
    env = event_env | {
        "FAIL_INIT": "1" if failure == "cli" else "0",
        "FAIL_AFTER_SOURCE": "1" if failure == "partial" else "0",
    }
    with PtyShell(runtime_bash, env) as shell:
        shell.command(
            '. "$REPO/shell/rc.sh"; [[ "$REMOTE_SSH_HISTORY_BACKEND" == bash && "$REMOTE_SSH_SKIM_HISTORY_BOUND" == 1 ]]'
        )
        shell.command(
            'rcrc; [[ "$REMOTE_SSH_HISTORY_BACKEND" == bash && "$REMOTE_SSH_SKIM_HISTORY_BOUND" == 1 ]]'
        )
        shell.keypress(b"\x12", lambda: Path(env["SKIM_CALLS"]).exists())
        calls = Path(env["ATUIN_CALLS"]).read_text().splitlines()
        assert sum(line.startswith("init ") for line in calls) == 1


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


@pytest.mark.parametrize("status", [0, 7])
@pytest.mark.parametrize("context", ["direct", "function", "source", "multiline"])
def test_recording_continues_across_toggle_reload(
    runtime_bash: str, event_env: dict[str, str], status: int, context: str
) -> None:
    body = f": audit-recording; REMOTE_SSH_ENABLE_ATUIN=0; rcrc; rcrc; (exit {status})"
    with PtyShell(runtime_bash, event_env) as shell:
        shell.command('. "$REPO/shell/rc.sh"')
        if context == "function":
            shell.command(f"audit_record() {{ {body}; }}")
            command = "audit_record"
        elif context == "source":
            Path(event_env["HOME"], "record.sh").write_text(body + "\n")
            command = '. "$HOME/record.sh"'
        elif context == "multiline":
            command = "{\n" + body + "\n}"
        else:
            command = body
        shell.command(command, status=status)
        marker = {"function": "audit_record;", "source": '. "$HOME/record.sh"'}.get(
            context, "audit-recording"
        )
        entry_id = history_id(event_env, marker)
        shell.until(lambda: bool(ends(event_env, entry_id)))
        assert ends(event_env, entry_id) == [("end", entry_id, str(status))]
        shell.command(": audit-after-reload")
        next_id = history_id(event_env, "audit-after-reload")
        shell.until(lambda: bool(ends(event_env, next_id)))
        assert ends(event_env, next_id) == [("end", next_id, "0")]
        assert next_id != entry_id
        shell.command('[[ "$REMOTE_SSH_HISTORY_BACKEND" == atuin && "$HISTFILE" == "" ]]')
