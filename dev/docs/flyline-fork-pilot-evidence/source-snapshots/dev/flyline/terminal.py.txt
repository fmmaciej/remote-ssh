"""Offline terminal lifecycle probes with private tmux/Zellij sessions."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import signal
import subprocess
import sys
import tempfile
import termios
import time
from pathlib import Path
from typing import Any

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1] / "docs/interactive-tools-performance-evidence")
)
from benchmark import PROMPT, Screen, Session, config, environment  # noqa: E402


class TerminalScreen(Screen):
    """Answer multiplexer geometry/palette probes as a basic xterm terminal."""

    def __init__(self) -> None:
        super().__init__()
        self.osc_pending = b""

    def csi(self, final: str) -> None:
        if final == "t" and self.sequence == "14":
            self.responses.extend(b"\x1b[4;600;1200t")
        elif final == "t" and self.sequence == "16":
            self.responses.extend(b"\x1b[6;20;10t")
        elif final == "p" and self.sequence.startswith("?") and self.sequence.endswith("$"):
            self.responses.extend(f"\x1b[{self.sequence[:-1]};2$y".encode())
        elif final == "n" and self.sequence == "?996":
            self.responses.extend(b"\x1b[?997;1n")
        elif final == "q" and self.sequence == ">":
            self.responses.extend(b"\x1bP>|XTerm(370)\x1b\\")
        else:
            super().csi(final)

    def feed(self, data: bytes) -> None:
        super().feed(data)
        self.osc_pending += data
        last = 0
        for match in re.finditer(rb"\x1b\]([^\x07\x1b]*)(?:\x07|\x1b\\)", self.osc_pending):
            payload = match[1]
            if payload in (b"10;?", b"11;?"):
                code = payload[:2]
                color = b"dddd/dddd/dddd" if code == b"10" else b"1111/1111/1111"
                self.responses.extend(b"\x1b]" + code + b";rgb:" + color + b"\x1b\\")
            elif re.fullmatch(rb"4;\d+;\?", payload):
                self.responses.extend(b"\x1b]" + payload[:-1] + b"rgb:7777/7777/7777\x1b\\")
            last = match.end()
        self.osc_pending = self.osc_pending[last:][-8192:]


class TerminalSession(Session):
    def read(self, timeout: float) -> bool:
        # Large palette replies can exceed one nonblocking PTY write.
        if self.responses:
            try:
                sent = os.write(self.fd, self.responses)
                del self.responses[:sent]
            except BlockingIOError:
                pass
        return super().read(timeout)


def capture(session: Session, path: Path, keys: list[bytes], expected: str) -> dict[str, Any]:
    start = path.stat().st_size if path.exists() else 0
    for key in keys:
        session.send(key)
        session.quiet(0.15)
    early = path.exists() and path.stat().st_size != start
    session.send(b"\r")
    deadline = time.monotonic() + 15
    actual = "[no argument]"
    while time.monotonic() < deadline:
        data = path.read_bytes()[start:] if path.exists() else b""
        if b"\x00" in data:
            actual = data.split(b"\x00", 1)[0].decode()
            break
        if not session.read(0.01):
            break
    session.quiet(0.08)
    return {
        "actual": actual,
        "expected": expected,
        "early_execution": early,
        "passed": actual == expected and not early,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("bash", "library", "tmux", "zellij", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument(
        "--contexts",
        nargs="+",
        choices=("direct", "tmux", "zellij"),
        default=("direct", "tmux", "zellij"),
    )
    parser.add_argument("--trace", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    results = []
    for context in args.contexts:
        # Short paths also fit macOS Unix socket path limits.
        with tempfile.TemporaryDirectory(prefix="fl-term-", dir="/private/tmp") as directory:
            home = Path(directory)
            for sub in ("config", "data", "state", "cache"):
                (home / sub).mkdir()
            library = home / args.library.name
            library.write_bytes(args.library.read_bytes())
            rc = home / "rc.sh"
            captured = home / "arguments"
            loaded = home / "loaded"
            rc.write_text(
                "capture() { printf '%s\\0' \"$*\" >> "
                + shlex.quote(str(captured))
                + "; }\n"
                + config("flyline-minimal", Path("/usr/bin"), library, home)
                + "flyline key --vim-mode true\nflyline suggestions --use-flycomp false\n"
                + "printf ready > "
                + shlex.quote(str(loaded))
                + "\n"
            )
            if args.trace:
                with rc.open("a") as stream:
                    stream.write(
                        "flyline log set-level trace\nflyline log stream "
                        + shlex.quote(str(home / "native.log"))
                        + "\n"
                    )
            shell = [str(args.bash), "--noprofile", "--rcfile", str(rc), "-i"]
            env = environment(home, Path("/usr/bin"))
            cleanup: list[str] | None = None
            if context == "tmux":
                tmux_config = home / "tmux.conf"
                # Match the project's Vim-friendly ESC policy, in a private server.
                tmux_config.write_text("set -s escape-time 0\n")
                prefix = [str(args.tmux), "-S", str(home / "socket"), "-f", str(tmux_config)]
                command = [*prefix, "new-session", "-s", "pilot", "-x", "120", "-y", "30", *shell]
                cleanup = [*prefix, "kill-server"]
            elif context == "zellij":
                wrapper = home / "pilot-shell"
                wrapper.write_text("#!/bin/sh\nexec " + shlex.join(shell) + "\n")
                wrapper.chmod(0o755)
                settings = home / "config.kdl"
                settings.write_text(
                    'default_mode "locked"\nshow_startup_tips false\nshow_release_notes false\nsession_serialization false\npane_frames false\n'
                    + "default_shell "
                    + json.dumps(str(wrapper))
                    + "\n"
                )
                layout = home / "layout.kdl"
                layout.write_text("layout {\n pane\n}\n")
                name = home.name
                command = [
                    str(args.zellij),
                    "--config",
                    str(settings),
                    "--data-dir",
                    str(home / "data"),
                    "--session",
                    name,
                    "--new-session-with-layout",
                    str(layout),
                ]
                cleanup = [
                    str(args.zellij),
                    "--config-dir",
                    str(home / "config"),
                    "delete-session",
                    "--force",
                    name,
                ]
            else:
                command = shell
            session = TerminalSession(command, env, home)
            session.screen = TerminalScreen()
            initial_flags = termios.tcgetattr(session.fd)[3]
            result: dict[str, Any] = {
                "context": context,
                "command": [shlex.quote(a) for a in command],
            }
            try:
                deadline = time.monotonic() + 15
                while not loaded.exists() and time.monotonic() < deadline:
                    if not session.read(0.01):
                        break
                if not loaded.exists():
                    raise RuntimeError("Shell rc did not finish loading")
                session.expect(PROMPT)
                if context == "tmux":
                    result["escape_time"] = subprocess.check_output(
                        [*prefix, "show-options", "-sv", "escape-time"], env=env, text=True
                    ).strip()
                result["vi"] = capture(session, captured, [b"capture ac", b"\x1b", b"hrbA"], "bc")
                result["paste"] = capture(
                    session, captured, ["\x1b[200~capture żółw\x1b[201~".encode()], "żółw"
                )
                result["multiline"] = capture(
                    session, captured, [b"\x1b[200~capture 'line1\nline2'\x1b[201~"], "line1\nline2"
                )
                session.send(b"capture MUST_NOT_RUN")
                session.quiet(0.1)
                session.send(b"\x03")
                session.quiet(0.2)
                result["ctrl_c"] = capture(session, captured, [b"capture recovered"], "recovered")
                termios.tcsetwinsize(session.fd, (25, 100))
                os.kill(session.pid, signal.SIGWINCH)
                session.quiet(0.2)
                result["resize"] = capture(session, captured, [b"capture resized"], "resized")
                session.send(b"\x04")
                session.quiet(0.5)
                final_flags = termios.tcgetattr(session.fd)[3]
                mask = termios.ICANON | termios.ECHO
                result["terminal_flags_restored"] = initial_flags & mask == final_flags & mask
                result["passed"] = (
                    all(
                        result[name]["passed"]
                        for name in ("vi", "paste", "multiline", "ctrl_c", "resize")
                    )
                    and result["terminal_flags_restored"]
                )
            except (RuntimeError, OSError) as exc:
                result.update(passed=False, error=str(exc)[:800])
            finally:
                if cleanup:
                    subprocess.run(
                        cleanup,
                        env=env,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=8,
                        check=False,
                    )
                result["resources"] = session.close()
                (args.output / f"{context}.txt").write_text(
                    json.dumps(session.transcript.decode(errors="replace")) + "\n"
                )
                if args.trace and (home / "native.log").exists():
                    (args.output / f"{context}-trace.log").write_bytes(
                        (home / "native.log").read_bytes()
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
