"""Opt-in native history/prompt pilot with pinned local Atuin, skim and Starship."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shlex
import sqlite3
import sys
import tempfile
import termios
import time
from pathlib import Path
from typing import Any

import managed

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1] / "docs/interactive-tools-performance-evidence")
)
from benchmark import Session, config, environment  # noqa: E402

READY = b"\x1ePILOT_READY\x1f"


def input_ready(session: Session) -> None:
    # PROMPT_COMMAND prints READY before Flyline enters raw mode. Sending Ctrl-R
    # immediately can let the tty's cooked reprint binding consume it. Wait for
    # actual input readiness rather than mistaking that harness race for a widget.
    deadline = time.monotonic() + 3
    while termios.tcgetattr(session.fd)[3] & termios.ICANON:
        if time.monotonic() >= deadline:
            raise RuntimeError("Editor did not enter raw input mode")
        session.quiet(0.01)
    session.quiet(0.03)


def command(session: Session, text: str) -> bytes:
    start = len(session.transcript)
    session.send(text.encode() + b"\r")
    session.expect(READY, raw=True)
    input_ready(session)
    return bytes(session.transcript[start:])


def argument(session: Session, text: bytes, expected: str) -> dict[str, Any]:
    start = len(session.transcript)
    session.send(text)
    session.quiet(0.08)
    early = bool(re.search(rb"\x1eARG:([^\x1f]*)\x1f", session.transcript[start:]))
    session.send(b"\r")
    session.expect(READY, raw=True)
    input_ready(session)
    found = re.findall(rb"\x1eARG:([^\x1f]*)\x1f", session.transcript[start:])
    actual = found[-1].decode() if found else "[no argument]"
    return {
        "actual": actual,
        "expected": expected,
        "early_execution": early,
        "passed": actual == expected and not early,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("bash", "library", "atuin", "skim", "starship", "repo", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument(
        "--backends",
        nargs="+",
        choices=("native", "skim", "atuin"),
        default=("native", "skim", "atuin"),
    )
    parser.add_argument(
        "--managed", action="store_true", help="Test actual managed installation/activation"
    )
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    results = []
    for backend in args.backends:
        with tempfile.TemporaryDirectory(prefix=f"flyline-{backend}-history-") as directory:
            home = Path(directory)
            for sub in ("config", "data", "state", "cache", "bin"):
                (home / sub).mkdir()
            for name, path in (("bash", args.bash), ("starship", args.starship)):
                (home / "bin" / name).symlink_to(path.resolve())
            if backend == "atuin":
                (home / "bin/atuin").symlink_to(args.atuin.resolve())
            if backend == "skim":
                (home / "bin/sk").symlink_to(args.skim.resolve())
            env = environment(home, home / "bin")
            env.update(
                HISTFILE=str(home / "bash-history"),
                REMOTE_SSH_ENABLE_ATUIN="1" if backend == "atuin" else "0",
            )
            repo = (
                managed.install(args.repo, args.bash, args.library, home, env)
                if args.managed
                else args.repo
            )
            library = home / args.library.name
            library.write_bytes(args.library.read_bytes())
            rc = home / "rc.sh"
            setup = (
                f"source {shlex.quote(str(repo / 'shell/rc.sh'))}\n"
                + "capture() { printf '\\036ARG:%s\\037\\n' \"$*\"; }\n"
                + config("flyline-minimal", home / "bin", library, args.repo)
                + "flyline key --vim-mode true\nflyline suggestions --use-flycomp false\n"
                + "flyline history --backend bash\n"
            )
            if args.managed:
                setup = (
                    f"source {shlex.quote(str(repo / 'shell/rc.sh'))}\n"
                    + "[[ $REMOTE_SSH_FLYLINE_STATE == active ]] || exit 54\n"
                    + "capture() { printf '\\036ARG:%s\\037\\n' \"$*\"; }\n"
                )
            # Keep the actual Starship PS1 after loading the minimal Flyline settings.
            setup += "PS1=$__PILOT_STARSHIP_PS1\n"
            setup = setup.replace("capture() {", "__PILOT_STARSHIP_PS1=$PS1\ncapture() {", 1)
            if backend == "atuin" and not args.managed:
                setup += """
_pilot_history() { __atuin_history --keymap-mode=vim-insert; }
flyline key bind Ctrl+r 'vimInsertMode=runBashCommand(_pilot_history)' || exit 51
"""
            elif backend == "skim" and not args.managed:
                setup += (
                    "declare -F __skim_history >/dev/null || exit 52\n"
                    "flyline key bind Ctrl+r 'vimInsertMode=runBashCommand(__skim_history)' || exit 53\n"
                )
            setup += """
__pilot_ready() { printf '\036PILOT_READY\037\n'; }
if [[ $(declare -p PROMPT_COMMAND 2>/dev/null) == 'declare -a'* ]]; then
    PROMPT_COMMAND+=(__pilot_ready)
else
    PROMPT_COMMAND=("${PROMPT_COMMAND:-:}" __pilot_ready)
fi
"""
            rc.write_text(setup)
            session = Session([str(args.bash), "--noprofile", "--rcfile", str(rc), "-i"], env, home)
            result: dict[str, Any] = {"backend": backend}
            try:
                session.expect(READY, raw=True)
                session.quiet(0.08)
                state = command(
                    session,
                    'printf \'\\036STATE:%s:%s\\037\\n\' "$REMOTE_SSH_HISTORY_BACKEND" "$HISTFILE"',
                )
                result["initial_state"] = re.findall(rb"\x1eSTATE:([^\x1f]*)\x1f", state)[
                    -1
                ].decode()
                command(session, "false")
                command(session, "sleep 0.05")
                command(session, "capture selected")
                start = len(session.transcript)
                session.send(b"capture \x12")
                session.quiet(0.5)
                session.send(b"\r")
                session.quiet(0.25)
                early = bool(re.search(rb"\x1eARG:([^\x1f]*)\x1f", session.transcript[start:]))
                result["selection_did_not_execute"] = not early
                result["editable_selection"] = argument(session, b"_edited", "selected_edited")
                session.send(b"capture draft\x12")
                session.quiet(0.4)
                session.send(b"\x1b")
                session.quiet(0.2)
                result["cancel"] = argument(session, b"", "draft")
                session.send(b"capture draft\x12")
                session.quiet(0.4)
                session.send(b"search_query")
                session.quiet(0.1)
                session.send(b"\x1b")
                session.quiet(0.2)
                result["cancel_edited_query"] = argument(session, b"", "draft")
                command(session, "capture navigation")
                result["up"] = argument(session, b"\x1b[A", "navigation")
                command(session, "capture navigation")
                session.send(b"\x1b")
                session.quiet(0.12)
                result["k"] = argument(session, b"kA", "navigation")
                reload_output = command(
                    session,
                    f"source {shlex.quote(str(repo / 'shell/rc.sh'))}; printf '\\036RELOADED:%s\\037\\n' \"$REMOTE_SSH_HISTORY_BACKEND\"",
                )
                result["reload_keeps_backend"] = (
                    f"\x1eRELOADED:{'atuin' if backend == 'atuin' else 'bash'}\x1f".encode()
                    in reload_output
                )
                session.send(b"exit\r")
                session.quiet(0.25)
                if backend == "atuin":
                    database = home / ".local/share/atuin/history.db"
                    with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as db:
                        rows = db.execute(
                            "SELECT command, exit, duration FROM history ORDER BY timestamp"
                        ).fetchall()
                    result["history_records"] = rows
                    result["false_status"] = any(
                        c == "false" and status == 1 for c, status, _ in rows
                    )
                    result["duration"] = any(
                        c == "sleep 0.05" and status == 0 and duration >= 40_000_000
                        for c, status, duration in rows
                    )
                    result["no_duplicate_selected"] = (
                        sum(c == "capture selected" for c, _, _ in rows) == 1
                    )
                else:
                    persisted = (home / "bash-history").read_text()
                    result["bash_history_persisted"] = "capture selected_edited" in persisted
                result["passed"] = (
                    result["selection_did_not_execute"]
                    and all(
                        result[key]["passed"]
                        for key in (
                            "editable_selection",
                            "cancel",
                            "cancel_edited_query",
                            "up",
                            "k",
                        )
                    )
                    and result["reload_keeps_backend"]
                    and (
                        all(
                            result[key]
                            for key in ("false_status", "duration", "no_duplicate_selected")
                        )
                        if backend == "atuin"
                        else result["bash_history_persisted"]
                    )
                )
            except (RuntimeError, OSError, sqlite3.Error, IndexError) as exc:
                result.update(passed=False, error=str(exc)[:1000])
            finally:
                result["resources"] = session.close()
                (args.output / f"{backend}.txt").write_text(
                    json.dumps(session.transcript.decode(errors="replace")) + "\n"
                )
            results.append(result)
            print(json.dumps(result), flush=True)
    report = {
        "library_sha256": hashlib.sha256(args.library.read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "results": results,
    }
    (args.output / "results.json").write_text(json.dumps(report, indent=2) + "\n")
    return 0 if all(r["passed"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
