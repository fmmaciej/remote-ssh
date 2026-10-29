"""Bounded diagnostic only: compare direct-child reap before/after closing PTY."""
from __future__ import annotations

import json
import os
import shlex
import signal
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(root / "dev/tests"))
from test_shell_command import Terminal, descendants  # noqa: E402

out = Path(__file__).resolve().parent
report = {}
with tempfile.TemporaryDirectory(prefix="shell-command-pty-close-") as directory:
    home = Path(directory)
    env = {k: v for k, v in os.environ.items() if not k.startswith(("REMOTE_", "BASH_FUNC_")) and k not in ("BASH_ENV", "ENV", "SHELLOPTS", "BASHOPTS", "CDPATH", "ZDOTDIR")}
    env.update(HOME=str(home), XDG_CONFIG_HOME=str(home / "config"), XDG_STATE_HOME=str(home / "state"), XDG_CACHE_HOME=str(home / "cache"), ZDOTDIR=str(home), PATH="/usr/bin:/bin", TERM="dumb")
    terminal = Terminal(["/bin/bash", "--noprofile", "--norc", "-i"], SimpleNamespace(env=env, home=home))
    closed = False
    owned = set()
    try:
        terminal.command("printf 'PARENT-READY\\n'")
        terminal.send(shlex.quote("/bin/bash") + " --noprofile --norc -i\n")
        terminal.command("printf 'CHILD-READY\\n'")
        terminal.send("exit 23\n")
        report["returned"] = terminal.command('printf "RETURN:%s\\n" "$?"')
        report["pid"] = terminal.process.pid
        owned = descendants(terminal.process.pid)
        report["descendants"] = sorted(owned)
        terminal.send("exit\n")
        for label, sig in (("term_master_open", signal.SIGTERM), ("kill_master_open", signal.SIGKILL)):
            if terminal.process.poll() is None:
                terminal.process.send_signal(sig)
            try:
                report[label] = {"returncode": terminal.process.wait(timeout=0.5)}
            except subprocess.TimeoutExpired:
                report[label] = {"timeout": True}
                report[label]["ps"] = subprocess.run(["/bin/ps", "-p", str(terminal.process.pid), "-o", "pid=,ppid=,pgid=,stat=,wchan=,comm="], capture_output=True, text=True, timeout=5, check=False).stdout
        os.close(terminal.master)
        closed = True
        report["after_master_close"] = {"returncode": terminal.process.wait(timeout=3)}
    finally:
        owned.update(descendants(terminal.process.pid))
        for pid in owned:
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        if not closed:
            os.close(terminal.master)
        if terminal.process.poll() is None:
            terminal.process.kill()
        report["cleanup_returncode"] = terminal.process.wait(timeout=3)
        report["terminal_output"] = terminal.output.decode(errors="replace")
        (out / "diagnose-pty-close-result.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report), flush=True)
