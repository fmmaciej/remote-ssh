"""Run an opt-in native Flyline/Readline editing comparison in isolated PTYs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pty
import select
import signal
import subprocess
import tempfile
import termios
import time
from pathlib import Path


def run_case(
    bash: Path, library: Path, output_dir: Path, *, flyline: bool, vi: bool
) -> dict[str, str | bool]:
    editor = "flyline" if flyline else "readline"
    scenario = "vi-replace" if vi else "plain-input"
    name = f"{editor}-{scenario}"
    with tempfile.TemporaryDirectory(prefix=f"{name}-") as directory:
        root = Path(directory)
        result_file = root / "result"
        ready_file = root / "ready"
        version_file = root / "version"
        rc = root / "rc.sh"
        rc.write_text(
            """PS1='PILOT> '
set -o vi
pilot_capture() { printf '%s\\n' "$1" > "$PILOT_RESULT"; }
if [[ "$PILOT_EDITOR" == flyline ]]; then
    builtin enable -f "$PILOT_LIBRARY" flyline || exit 31
    flyline version > "$PILOT_VERSION" || exit 32
    flyline run-tutorial false || exit 33
    flyline --show-animations false --enable-easter-eggs false \\
        --enable-extended-key-codes false --send-shell-integration-codes none \\
        --set-mouse-mode disabled || exit 34
    flyline set-cursor --backend terminal || exit 35
    flyline suggestions --auto-suggest false --auto-suggest-inline false || exit 36
fi
printf ready > "$PILOT_READY"
"""
        )
        env = {
            "HOME": directory,
            "XDG_CONFIG_HOME": str(root / "config"),
            "XDG_DATA_HOME": str(root / "data"),
            "XDG_STATE_HOME": str(root / "state"),
            "XDG_CACHE_HOME": str(root / "cache"),
            "PATH": f"{bash.parent}:/usr/bin:/bin",
            "TERM": "xterm-256color",
            "LANG": "en_US.UTF-8",
            "HISTFILE": str(root / "history"),
            "PILOT_EDITOR": editor,
            "PILOT_LIBRARY": str(library),
            "PILOT_RESULT": str(result_file),
            "PILOT_READY": str(ready_file),
            "PILOT_VERSION": str(version_file),
        }
        captured = bytearray()
        pid, fd = pty.fork()
        if pid == 0:
            try:
                termios.tcsetwinsize(0, (30, 120))
                os.execve(str(bash), [str(bash), "--noprofile", "--rcfile", str(rc), "-i"], env)
            finally:
                os._exit(127)

        def drain(duration: float) -> None:
            deadline = time.monotonic() + duration
            pending = bytearray()
            while time.monotonic() < deadline:
                readable, _, _ = select.select([fd], [], [], min(0.02, duration))
                if not readable:
                    continue
                try:
                    chunk = os.read(fd, 65536)
                except OSError:
                    return
                if not chunk:
                    return
                captured.extend(chunk)
                pending.extend(chunk)
                while b"\x1b[6n" in pending:
                    end = pending.index(b"\x1b[6n") + 4
                    del pending[:end]
                    os.write(fd, b"\x1b[1;1R")
                if len(pending) > 8:
                    del pending[:-8]

        try:
            deadline = time.monotonic() + 5
            while not ready_file.exists() and time.monotonic() < deadline:
                drain(0.05)
            drain(0.5)
            if ready_file.exists():
                os.write(fd, b"pilot_capture ac")
                drain(0.2)
                if vi:
                    os.write(fd, b"\x1b")
                    drain(0.2)
                    os.write(fd, b"hrbA")
                    drain(0.2)
                os.write(fd, b"\r")
                deadline = time.monotonic() + 4
                while not result_file.exists() and time.monotonic() < deadline:
                    drain(0.05)
                drain(0.1)
            actual = result_file.read_text().strip() if result_file.exists() else "[no result]"
            expected = "bc" if vi else "ac"
            return {
                "editor": editor,
                "scenario": scenario,
                "startup_ready": ready_file.exists(),
                "flyline_version": version_file.read_text().strip()
                if version_file.exists()
                else "",
                "expected_argument": expected,
                "actual_argument": actual,
                "passed": actual == expected,
                "transcript": f"{name}.pty",
            }
        finally:
            (output_dir / f"{name}.pty").write_bytes(captured)
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            os.close(fd)
            os.waitpid(pid, 0)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bash", type=Path, required=True)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    bash = args.bash.resolve(strict=True)
    library = args.library.resolve(strict=True)
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    version = subprocess.run(
        [str(bash), "--version"], check=True, capture_output=True, text=True, timeout=5
    ).stdout.splitlines()[0]
    results = [
        run_case(bash, library, output_dir, flyline=flyline, vi=vi)
        for flyline in (False, True)
        for vi in (False, True)
    ]
    report = {
        "bash_version": version,
        "library_sha256": hashlib.sha256(library.read_bytes()).hexdigest(),
        "scenarios": results,
    }
    (output_dir / "results.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
