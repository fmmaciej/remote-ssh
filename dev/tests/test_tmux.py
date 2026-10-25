from __future__ import annotations

import os
import pty
import shutil
import subprocess
import tempfile
import time
from collections.abc import Callable
from pathlib import Path

import pytest
from conftest import IsolatedEnv, assert_ok, run_cmd


def test_tmux_checkout_paths_reload_and_confirmed_restart(
    repo_dir: Path, isolated_env: IsolatedEnv
) -> None:
    tmux = shutil.which("tmux")
    if tmux is None:
        pytest.skip("tmux is optional")
    # A short socket path also works on systems with a small Unix socket limit.
    with tempfile.TemporaryDirectory(prefix="remote-ssh-tmux-", dir="/tmp") as temporary:
        root = Path(temporary)
        checkout = root / "checkout with spaces and 'quote"
        (checkout / "dots").mkdir(parents=True)
        (checkout / "shell").mkdir()
        config = checkout / "dots/tmux.conf"
        shutil.copy2(repo_dir / "dots/tmux.conf", config)
        marker = root / "started"
        (checkout / "shell/rc.sh").write_text('printf started >"$AUDIT_ROOT_MARKER"\nPS1=""\n')
        env = isolated_env.env | {"TERM": "xterm-256color", "AUDIT_ROOT_MARKER": str(marker)}
        command = [tmux, "-S", str(root / "socket")]

        def call(*args: str) -> str:
            result = run_cmd([*command, *args], env=env)
            assert_ok(result)
            return result.stdout.strip()

        def wait_until(predicate: Callable[[], bool]) -> None:
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                if predicate():
                    return
                time.sleep(0.02)
            raise AssertionError("tmux did not reach the expected state")

        master, slave = pty.openpty()
        client = None
        try:
            call("-f", str(config), "new-session", "-d", "-s", "audit")
            wait_until(marker.exists)
            assert call("show-options", "-gv", "@remote-ssh-root") == str(checkout)
            old_pid = call("display-message", "-p", "#{pane_pid}")
            with config.open("a") as stream:
                stream.write("\nset -g history-limit 12345\n")
            client = subprocess.Popen(
                [*command, "attach-session", "-t", "audit"],
                stdin=slave,
                stdout=slave,
                stderr=slave,
                env=env,
            )
            wait_until(lambda: bool(call("list-clients")))
            os.write(master, b"\x02r")
            wait_until(lambda: call("show-options", "-gv", "history-limit") == "12345")
            os.write(master, b"\x02q")
            time.sleep(0.1)
            assert call("display-message", "-p", "#{pane_pid}") == old_pid
            os.write(master, b"n")
            time.sleep(0.1)
            assert call("display-message", "-p", "#{pane_pid}") == old_pid
            os.write(master, b"\x02q")
            time.sleep(0.1)
            os.write(master, b"y")
            wait_until(lambda: call("display-message", "-p", "#{pane_pid}") != old_pid)
        finally:
            run_cmd([*command, "kill-server"], env=env)
            if client is not None:
                client.wait(timeout=5)
            os.close(master)
            os.close(slave)
