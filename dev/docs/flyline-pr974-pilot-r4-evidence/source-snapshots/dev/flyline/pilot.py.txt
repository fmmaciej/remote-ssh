"""Offline native Flyline acceptance probes; explicit local library and Bash only.

Run in disposable PTYs. This does not load the library into the invoking shell.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

# Reuse the terminal emulator that answers Flyline's CPR/DA2 probes.
sys.path.insert(
    0, str(Path(__file__).resolve().parents[1] / "docs/interactive-tools-performance-evidence")
)
from benchmark import PROMPT, Session, config, environment  # noqa: E402

CASES = {
    "replace": ("ac", [b"\x1b", b"hrbA"], "bc"),
    "delete": ("abcd", [b"\x1b", b"xA"], "abc"),
    "delete-word": ("one two three", [b"\x1b", b"0wdwA"], "two three"),
    "change-word": ("one two", [b"\x1b", b"0wcwONE", b"\x1b", b"A"], "ONE two"),
    "yank-paste": ("ab", [b"\x1b", b"0wyw$pA"], "abab"),
    "undo-redo": ("ac", [b"\x1b", b"hrb", b"u", b"\x12", b"A"], "bc"),
    "undo": ("ac", [b"\x1b", b"hrb", b"u", b"A"], "ac"),
    "dot-delete": ("abcd", [b"\x1b", b"0wlx.A"], "ad"),
    "dot-replace": ("abcd", [b"\x1b", b"0wrXl.A"], "XXcd"),
    "dot-change": ("one two", [b"\x1b", b"0wcwNEW", b"\x1b", b"w.A"], "NEW NEW"),
    "unicode-paste": ("żółw", [], "żółw"),
    "normal-mode-no-text": ("abc", [b"\x1b", b"qA"], "abc"),
    "count-motion": ("abcd", [b"\x1b", b"2hrXA"], "aXcd"),
    "history-k": ("", [b"\x1b", b"kA"], "seeded"),
    "history-up": ("", [b"\x1b[A"], "seeded"),
    "history-slash": ("", [b"\x1b", b"/seeded", b"\r", b"A"], "seeded"),
    "unicode-yank-paste": ("żółw", [b"\x1b", b"0wyw$pA"], "żółwżółw"),
    "undo-change": ("one two", [b"\x1b", b"0wcwNEW", b"\x1b", b"uA"], "one two"),
    "undo-consecutive": ("abcd", [b"\x1b", b"0wrXlrYuuA"], "abcd"),
    "undo-after-motion": ("ac", [b"\x1b", b"hrbhluA"], "ac"),
    "dot-undo": ("abcd", [b"\x1b", b"0wlx.uA"], "acd"),
    "count-motion-right": ("abcd", [b"\x1b", b"0w2lrXA"], "abXd"),
    "count-ten": ("abcdefghijkl", [b"\x1b", b"10hrXA"], "aXcdefghijkl"),
    "count-delete-words": ("one two three", [b"\x1b", b"0w2dwA"], "three"),
    "history-k-draft": ("draft", [b"\x1b", b"kA"], "seeded"),
    "history-kj-draft": ("draft", [b"\x1b", b"kjA"], "draft"),
    "history-count": ("", [b"\x1b", b"2kA"], "older"),
    "history-search-cancel": ("draft", [b"\x1b", b"/seeded", b"\x07", b"A"], "draft"),
    "history-search-miss": ("draft", [b"\x1b", b"/not-in-fixture", b"\r", b"A"], "draft"),
    "history-search-edit-query": ("", [b"\x1b", b"/seedX", b"\x7fed", b"\r", b"A"], "seeded"),
    "history-search-anchor": ("", [b"\x1b", b"/^capture seed", b"\r", b"A"], "seeded"),
    "history-search-preserves-undo": ("ac", [b"\x1b", b"hrb/seeded", b"\x07", b"uA"], "ac"),
}

# These history cases start with an actual draft command, rather than a blank prompt.
DRAFT_HISTORY_CASES = {
    "history-k-draft",
    "history-kj-draft",
    "history-search-cancel",
    "history-search-miss",
    "history-search-preserves-undo",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bash", type=Path, required=True)
    editor = parser.add_mutually_exclusive_group(required=True)
    editor.add_argument("--library", type=Path)
    editor.add_argument("--readline", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--case", choices=CASES, action="append")
    parser.add_argument(
        "--managed-repo", type=Path, help="Install and activate via a temporary checkout"
    )
    args = parser.parse_args()
    if args.managed_repo and not args.library:
        parser.error("--managed-repo requires --library")
    args.output.mkdir(parents=True, exist_ok=True)
    library_bytes = args.library.read_bytes() if args.library else None
    results = []
    for name in args.case or CASES:
        text, keys, expected = CASES[name]
        # Clean Readline's Ctrl-R is a history-search binding, not Vim redo.
        # The PR adds redo; keep both observations explicit in the report.
        if args.readline and name == "undo-redo":
            expected = "ac"
        with tempfile.TemporaryDirectory(prefix="flyline-pr974-") as directory:
            home = Path(directory)
            for subdir in ("config", "data", "state", "cache", "bin"):
                (home / subdir).mkdir()
            rc = home / "rc.sh"
            snapshot = home / (args.library.name if args.library else "unused-library")
            if library_bytes is not None:
                snapshot.write_bytes(library_bytes)
            setup = config("bash", Path("/usr/bin"), snapshot, home)
            if library_bytes is not None:
                setup = (
                    config("flyline-minimal", Path("/usr/bin"), snapshot, home)
                    + "flyline key --vim-mode true || exit 51\n"
                    + "flyline suggestions --use-flycomp false || exit 52\n"
                )
            env = environment(home, Path("/usr/bin"))
            if args.managed_repo:
                import managed

                (home / "bin/bash").symlink_to(args.bash.resolve())
                env = environment(home, home / "bin")
                checkout = managed.install(args.managed_repo, args.bash, args.library, home, env)
                setup = (
                    f"source {shlex.quote(str(checkout / 'shell/rc.sh'))}\n"
                    "[[ $REMOTE_SSH_FLYLINE_STATE == active ]] || exit 54\n"
                    "PS1='BMARK> '\n"
                )
            rc.write_text(
                "capture() { printf '\\036ARG:%s\\037\\n' \"$*\"; }\n"
                + "history -s 'capture older'\n"
                + "history -s 'capture seeded'\n"
                + setup
                + "printf '\\036LOADED\\037\\n'\n"
            )
            session = Session(
                [str(args.bash.resolve()), "--noprofile", "--rcfile", str(rc), "-i"],
                env,
                home,
            )
            result = {"case": name, "expected": expected, "keys": [repr(k) for k in keys]}
            try:
                session.expect(b"\x1eLOADED\x1f", raw=True)
                session.expect(PROMPT)
                session.quiet(0.05)
                if not name.startswith("history-") or name in DRAFT_HISTORY_CASES:
                    session.send(("capture " + text).encode())
                session.quiet(0.1)
                for key in keys:
                    session.send(key)
                    # Escape must be decoded as a standalone key, not an Alt prefix.
                    session.quiet(0.12)
                result["line_before_submit"] = "".join(
                    session.screen.rows[session.screen.row]
                ).rstrip()
                result["executed_before_submit"] = bool(
                    re.search(rb"\x1eARG:([^\x1f]*)\x1f", session.transcript)
                )
                session.send(b"\r")
                session.expect(b"\x1f", raw=True, timeout=3)
                found = re.findall(rb"\x1eARG:([^\x1f]*)\x1f", session.transcript)
                actual = found[-1].decode() if found else "[no argument]"
                result.update(
                    actual=actual,
                    passed=actual == expected and not result["executed_before_submit"],
                )
            except (RuntimeError, OSError) as exc:
                result.update(passed=False, error=str(exc)[:600])
            finally:
                result["resources"] = session.close()
                (args.output / f"{name}.txt").write_text(
                    json.dumps(session.transcript.decode(errors="replace")) + "\n"
                )
            results.append(result)
            print(json.dumps(result), flush=True)
    report = {
        "platform": platform.platform(),
        "bash": str(args.bash.resolve()),
        "bash_version": subprocess.check_output([args.bash, "--version"], text=True).splitlines()[
            0
        ],
        "library": str(args.library.resolve()) if args.library else None,
        "library_sha256": hashlib.sha256(library_bytes).hexdigest() if library_bytes else None,
        "pilot_sha256": digest(Path(__file__)),
        "managed": bool(args.managed_repo),
        "results": results,
    }
    (args.output / "results.json").write_text(json.dumps(report, indent=2) + "\n")
    return 0 if all(row["passed"] for row in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
