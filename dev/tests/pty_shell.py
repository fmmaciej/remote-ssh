from __future__ import annotations

import os
import pty
import select
import signal
import time
from collections.abc import Callable, Mapping


class PtyShell:
    """An isolated interactive Bash with execution markers and bounded cleanup."""

    prompt_text = b"REMOTE_SSH_TEST> "

    def __init__(self, bash: str, env: Mapping[str, str]) -> None:
        self.output = bytearray()
        self.counter = 0
        self.pid, self.fd = pty.fork()
        if self.pid == 0:
            try:
                os.execve(
                    bash,
                    [bash, "--noprofile", "--norc", "-i"],
                    dict(env) | {"PS1": self.prompt_text.decode()},
                )
            finally:
                os._exit(127)

    def __enter__(self) -> PtyShell:
        try:
            self.prompt()
        except BaseException:
            self.close()
            raise
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def until(self, predicate: Callable[[], bool]) -> None:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if predicate():
                return
            readable, _, _ = select.select([self.fd], [], [], 0.03)
            if readable:
                try:
                    data = os.read(self.fd, 65536)
                except OSError:
                    break
                if not data:
                    break
                self.output.extend(data)
        raise AssertionError(self.output.decode(errors="replace"))

    def prompt(self) -> None:
        self.until(lambda: self.prompt_text in self.output)
        self.output.clear()

    def command(self, value: str, *, status: int = 0) -> None:
        self.counter += 1
        prefix = f"\x1e{self.counter}:".encode()
        # Preserve the command's status for real PROMPT_COMMAND callbacks.
        # The input echo contains escapes; only execution emits control bytes.
        suffix = rf"""; audit_status=$?; printf '\036{self.counter}:%s\037' "$audit_status"; (exit "$audit_status")"""
        os.write(self.fd, (value + suffix + "\n").encode())
        self.until(
            lambda: prefix in self.output and b"\x1f" in self.output[self.output.index(prefix) :]
        )
        start = self.output.index(prefix) + len(prefix)
        end = self.output.index(b"\x1f", start)
        actual = int(self.output[start:end])
        captured = self.output.decode(errors="replace")
        del self.output[: end + 1]
        self.prompt()
        assert actual == status, f"status={actual}, expected={status}\n{captured}"

    def keypress(self, keys: bytes, completed: Callable[[], bool]) -> None:
        os.write(self.fd, keys)
        self.until(completed)
        self.output.clear()
        os.write(self.fd, b"\x03")
        self.prompt()

    def close(self) -> None:
        try:
            os.kill(self.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        # A terminal can keep the child in teardown until its master is closed.
        os.close(self.fd)
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            if os.waitpid(self.pid, os.WNOHANG)[0] == self.pid:
                return
            time.sleep(0.01)
        raise AssertionError(f"PTY shell {self.pid} did not exit after terminal close")
