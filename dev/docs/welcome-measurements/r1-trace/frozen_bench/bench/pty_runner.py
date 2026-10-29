from __future__ import annotations

import os
import pty
import select
import signal
import time
from collections.abc import Mapping, Sequence
from pathlib import Path

from bench.model import Sample


def wait_status_to_returncode(status: int) -> int:
    if hasattr(os, "waitstatus_to_exitcode"):
        return os.waitstatus_to_exitcode(status)
    if os.WIFEXITED(status):
        return os.WEXITSTATUS(status)
    if os.WIFSIGNALED(status):
        return -os.WTERMSIG(status)
    return 1


def terminate_child(pid: int) -> None:
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    time.sleep(0.05)
    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        return


def run_pty_sample(
    args: Sequence[str],
    env: Mapping[str, str],
    cwd: Path,
    marker: str,
    timeout_seconds: float,
) -> Sample:
    marker_bytes = marker.encode()
    search_buffer = b""
    output_limit = 128 * 1024
    output_tail = bytearray()

    start_ns = time.perf_counter_ns()
    pid, fd = pty.fork()
    if pid == 0:
        os.chdir(cwd)
        os.execvpe(args[0], list(args), dict(env))

    ready_ns: int | None = None
    returncode: int | None = None
    timed_out = False
    deadline = time.monotonic() + timeout_seconds

    try:
        while True:
            waited_pid, status = os.waitpid(pid, os.WNOHANG)
            if waited_pid == pid:
                returncode = wait_status_to_returncode(status)

            remaining = max(0.0, deadline - time.monotonic())
            if returncode is None and remaining <= 0:
                timed_out = True
                terminate_child(pid)
                waited_pid, status = os.waitpid(pid, 0)
                if waited_pid == pid:
                    returncode = wait_status_to_returncode(status)
                break

            read_timeout = 0.0 if returncode is not None else min(0.05, remaining)
            readable, _, _ = select.select([fd], [], [], read_timeout)
            if readable:
                try:
                    chunk = os.read(fd, 4096)
                except OSError:
                    chunk = b""
                if not chunk:
                    if returncode is not None:
                        break
                    continue

                output_tail.extend(chunk)
                if len(output_tail) > output_limit:
                    del output_tail[: len(output_tail) - output_limit]

                search_buffer = (search_buffer + chunk)[-4096:]
                if ready_ns is None and marker_bytes in search_buffer:
                    ready_ns = time.perf_counter_ns()
                continue

            if returncode is not None:
                break
    finally:
        try:
            os.close(fd)
        except OSError:
            pass

    total_ns = time.perf_counter_ns()
    ready_ms = None if ready_ns is None else (ready_ns - start_ns) / 1_000_000
    total_ms = (total_ns - start_ns) / 1_000_000
    return Sample(
        ready_ms=ready_ms,
        total_ms=total_ms,
        returncode=returncode,
        timed_out=timed_out,
        output_tail=output_tail.decode(errors="replace"),
    )
