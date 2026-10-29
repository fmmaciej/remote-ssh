from __future__ import annotations

import errno
import fcntl
import os
import pty
import select
import shlex
import shutil
import signal
import subprocess
import termios
import time
import uuid
from collections.abc import Iterator
from pathlib import Path

import pytest
from conftest import IsolatedEnv, assert_ok, write_executable
from test_install_cli import CliInstall, prepare_cli_install


@pytest.fixture
def shell_install(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str
) -> Iterator[CliInstall]:
    c = prepare_cli_install(repo_dir, isolated_env, runtime_bash)
    for key in list(c.env):
        if key.startswith(("TOOLS_", "REMOTE_", "BASH_FUNC_")) or key in (
            "BASH_ENV",
            "ENV",
            "SHELLOPTS",
            "BASHOPTS",
            "CDPATH",
            "ZDOTDIR",
            "LIB_DIR",
            "BIN_DIR",
            "DOTS_DIR",
            "SHELL_DIR",
            "SCRIPT_DIR",
            "REPO_DIR",
        ):
            c.env.pop(key, None)
    # The installer fixture removes inherited REMOTE_*, exported functions and
    # interpreter/startup overrides. Keep this module's optional integrations off.
    c.env.update(
        {
            "XDG_CACHE_HOME": str(c.home / ".cache"),
            "ZDOTDIR": str(c.home),
            "REMOTE_SSH_WELCOME": "0",
            "REMOTE_SSH_UPDATE_CHECK": "0",
            "REMOTE_SSH_ENABLE_GIT_SESSION_IDENTITY": "0",
            "REMOTE_SSH_ENABLE_ATUIN": "0",
            "REMOTE_SSH_ENABLE_ATUIN_AUTO_IMPORT": "0",
            "TERM": "dumb",
            "PS1": "test> ",
            "PROMPT": "test> ",
        }
    )
    startup = {p: p.read_bytes() for p in c.home.glob(".*") if p.is_file()}
    yield c
    assert not c.network.exists(), c.network.read_text() if c.network.exists() else ""
    assert {p: p.read_bytes() for p in startup} == startup


def run(
    c: CliInstall,
    args: list[str | Path],
    *,
    input: str = "",
    env: dict[str, str] | None = None,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    with subprocess.Popen(
        [str(a) for a in args],
        env=env or c.env,
        cwd=cwd or c.home,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    ) as process:
        try:
            stdout, stderr = process.communicate(input, timeout=20)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate(timeout=5)
            pytest.fail(f"Timed out: {args!r}\n{stdout}\n{stderr}")
        return subprocess.CompletedProcess(args, process.returncode, stdout, stderr)


def install(c: CliInstall) -> tuple[int, Path, bytes]:
    assert_ok(c.run("install", "--yes", "demo"))
    return c.command.lstat().st_ino, c.command.readlink(), c.expected.read_bytes()


def unchanged(c: CliInstall, snapshot: tuple[int, Path, bytes]) -> None:
    assert (c.command.lstat().st_ino, c.command.readlink(), c.expected.read_bytes()) == snapshot


def activation(c: CliInstall, root: Path, cwd: Path) -> str:
    return (
        "case $- in *i*) ;; *) exit 81;; esac; "
        f'test "$PWD" = {shlex.quote(str(cwd))} || exit 82; '
        f'test "$REMOTE_ENV_DIR" = {shlex.quote(str(root))} || exit 83; '
        f'case "$PATH" in {shlex.quote(str(root / "bin"))}:*) ;; *) exit 84;; esac; '
        "alias rhelp >/dev/null || exit 85; "
        "declare -F log >/dev/null || exit 86; "
        'printf "ACTIVATED:%s:%s\\n" "$BASH_VERSION" "$PWD"\n'
    )


def test_dispatch_exact_argv_cwd_and_status(shell_install: CliInstall) -> None:
    c = shell_install
    capture = c.home / "argv"
    (c.transport / "bash").unlink()
    write_executable(
        c.transport / "bash",
        '#!/bin/sh\nprintf "%s\\0" "$@" > "$CAPTURE"\npwd > "$CAPTURE.cwd"\nexit 23\n',
    )
    rc = c.root / "shell/rc.sh"
    rc.write_text('printf loaded > "$HOME/rc-loaded"\n')
    other = c.home / "unrelated cwd"
    other.mkdir()
    result = run(
        c,
        [c.bash, c.root / "bin/remote-ssh", "shell"],
        env=c.env | {"CAPTURE": str(capture)},
        cwd=other,
    )
    assert result.returncode == 23, result.stderr
    assert capture.read_bytes().split(b"\0") == [b"--rcfile", os.fsencode(rc), b"-i", b""]
    assert Path(str(capture) + ".cwd").read_text().strip() == str(other)
    assert not (c.home / "rc-loaded").exists()


@pytest.mark.parametrize(
    "args",
    [
        [],
        ["-h"],
        ["--help"],
        ["help"],
        ["shell", "-h"],
        ["shell", "--help"],
        ["shell", "help"],
        ["shell", "--"],
        ["shell", "-c"],
        ["shell", "-l"],
        ["shell", "--rcfile"],
        ["shell", "position"],
        ["shell", "--help", "extra"],
        ["shell", "-h", "extra"],
        ["shell", "-c", "exit 0"],
    ],
)
def test_help_and_argument_boundary(shell_install: CliInstall, args: list[str]) -> None:
    c = shell_install
    (c.transport / "bash").unlink()
    write_executable(c.transport / "bash", '#!/bin/sh\ntouch "$HOME/launched"\nexit 98\n')
    rc = c.root / "shell/rc.sh"
    rc.write_text('touch "$HOME/rc-loaded"\n')
    result = run(c, [c.bash, c.root / "bin/remote-ssh", *args])
    invalid = args[:1] == ["shell"] and args[1:] not in (["-h"], ["--help"])
    assert result.returncode == int(invalid), result.stdout + result.stderr
    output = result.stderr if invalid else result.stdout
    assert "Usage: remote-ssh" in output
    if args[:1] == ["shell"]:
        assert "Usage: remote-ssh shell" in output
        assert "exit" in output
    if invalid:
        assert "does not accept arguments" in output
    assert not (c.home / "launched").exists()
    assert not (c.home / "rc-loaded").exists()
    # Help and argument parsing must still win when both preflights would fail.
    rc.unlink()
    (c.transport / "bash").unlink()
    restricted = c.home / "restricted"
    restricted.mkdir()
    for tool in ("dirname", "cat"):
        (restricted / tool).symlink_to(shutil.which(tool) or f"/usr/bin/{tool}")
    again = run(
        c, [c.bash, c.root / "bin/remote-ssh", *args], env=c.env | {"PATH": str(restricted)}
    )
    assert again.returncode == int(invalid), again.stdout + again.stderr
    assert "rcfile is not" not in again.stderr
    assert "cannot find" not in again.stderr


@pytest.mark.parametrize("status", [0, 23])
def test_installed_no_tty_matches_manual_and_bare_path(
    shell_install: CliInstall, status: int
) -> None:
    c = shell_install
    snapshot = install(c)
    cwd = c.home / "other dir"
    cwd.mkdir()
    body = activation(c, c.root, cwd) + f"exit {status}\n"
    direct = run(c, [c.command, "shell"], input=body, cwd=cwd)
    manual = run(c, [c.bash, "--rcfile", c.root / "shell/rc.sh", "-i"], input=body, cwd=cwd)
    assert direct.returncode == manual.returncode == status, direct.stdout + direct.stderr
    assert "ACTIVATED:" in direct.stdout
    version = run(c, [c.bash, "--noprofile", "--norc", "-c", 'printf "%s" "$BASH_VERSION"'])
    assert_ok(version)
    assert f"ACTIVATED:{version.stdout}:" in direct.stdout
    assert direct.stdout == manual.stdout
    bare = run(
        c,
        [c.bash, "--noprofile", "--norc", "-c", "remote-ssh shell"],
        env=c.env | {"PATH": f"{c.bin}:{c.env['PATH']}"},
        input=body,
        cwd=cwd,
    )
    assert bare.returncode == status, bare.stdout + bare.stderr
    assert bare.stdout == direct.stdout
    unchanged(c, snapshot)


def test_effective_checkout_override(shell_install: CliInstall) -> None:
    c = shell_install
    snapshot = install(c)
    other = c.home / 'other checkout " $ ; &'
    shutil.copytree(c.root, other)
    with (other / "shell/rc.sh").open("a") as stream:
        stream.write('\nprintf "OVERRIDE-RC\\n"\n')
    result = run(
        c,
        [c.command, "shell"],
        env=c.env | {"REMOTE_ENV_DIR": str(other)},
        input=activation(c, other, c.home) + "exit\n",
    )
    assert_ok(result)
    assert "OVERRIDE-RC" in result.stdout
    assert "ACTIVATED:" in result.stdout
    original = run(c, [c.command, "shell"], input=activation(c, c.root, c.home) + "exit\n")
    assert_ok(original)
    assert "OVERRIDE-RC" not in original.stdout
    unchanged(c, snapshot)


@pytest.mark.parametrize("kind", ["missing", "directory", "unreadable", "bash"])
def test_preflight_failures(shell_install: CliInstall, kind: str) -> None:
    c = shell_install
    rc = c.root / "shell/rc.sh"
    rc.write_text('touch "$HOME/rc-loaded"\n')
    env = c.env
    if kind == "missing":
        rc.unlink()
    elif kind == "directory":
        rc.unlink()
        rc.mkdir()
    elif kind == "unreadable":
        assert os.geteuid() != 0, "Unreadability must be verified as an ordinary user"
        rc.chmod(0)
        assert not os.access(rc, os.R_OK), "chmod did not make the file unreadable"
    else:
        restricted = c.home / "restricted"
        restricted.mkdir()
        (restricted / "dirname").symlink_to(shutil.which("dirname") or "/usr/bin/dirname")
        env = c.env | {"PATH": str(restricted)}
    try:
        result = run(c, [c.bash, c.root / "bin/remote-ssh", "shell"], env=env)
        assert result.returncode == (127 if kind == "bash" else 1), result.stderr
        assert "remote-ssh shell:" in result.stderr
        assert ("Bash in PATH" if kind == "bash" else str(rc)) in result.stderr
        assert not (c.home / "rc-loaded").exists()
    finally:
        if kind == "unreadable":
            rc.chmod(0o644)


def descendant_depths(parent: int) -> dict[int, int]:
    result = subprocess.run(
        ["/bin/ps", "-axo", "pid=,ppid="], capture_output=True, text=True, timeout=5, check=True
    )
    rows = [tuple(map(int, line.split())) for line in result.stdout.splitlines()]
    found = {parent: 0}
    while True:
        added = {pid: found[ppid] + 1 for pid, ppid in rows if ppid in found and pid not in found}
        if not added:
            return {pid: depth for pid, depth in found.items() if pid != parent}
        found.update(added)


def descendants(parent: int) -> set[int]:
    return set(descendant_depths(parent))


def alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


class Terminal:
    """Task-local controlling PTY, with bounded reads and descendant cleanup.

    Snapshot the descendant tree before terminating its root: job-control shells
    may have different process groups. Kill/reap descendants before their parent,
    retaining known PIDs across cleanup snapshots. No runtime handler is needed.
    """

    def __init__(self, args: list[str | Path], c: CliInstall):
        # Fail before spawning any shell if cleanup cannot inspect its tree.
        descendants(os.getpid())
        self.master, slave = pty.openpty()
        attrs = termios.tcgetattr(slave)
        attrs[3] &= ~termios.ECHO
        termios.tcsetattr(slave, termios.TCSANOW, attrs)
        self.output = b""
        self.offset = 0
        self.owned: dict[int, int] = {}

        def controlling_terminal() -> None:
            fcntl.ioctl(0, termios.TIOCSCTTY, 0)

        try:
            self.process = subprocess.Popen(
                [str(a) for a in args],
                env=c.env,
                cwd=c.home,
                stdin=slave,
                stdout=slave,
                stderr=slave,
                start_new_session=True,
                preexec_fn=controlling_terminal,
            )
        except BaseException:
            os.close(self.master)
            raise
        finally:
            os.close(slave)

    def send(self, text: str) -> None:
        os.write(self.master, text.encode())

    def until(self, expected: str, timeout: float = 15) -> str:
        deadline = time.monotonic() + timeout
        needle = expected.encode()
        while needle not in self.output[self.offset :]:
            assert time.monotonic() < deadline, self.output.decode(errors="replace")
            ready, _, _ = select.select(
                [self.master], [], [], min(0.1, max(0, deadline - time.monotonic()))
            )
            if not ready:
                continue
            try:
                data = os.read(self.master, 65536)
            except OSError as exc:
                if exc.errno == errno.EIO:
                    data = b""
                else:
                    raise
            assert data, self.output.decode(errors="replace")
            self.output += data
        end = self.output.index(needle, self.offset) + len(needle)
        result = self.output[self.offset : end].decode(errors="replace")
        self.offset = end
        return result

    def command(self, command: str) -> str:
        token = uuid.uuid4().hex
        marker = "DONE-" + token
        # Readline/ZLE may re-enable terminal echo. Never place the complete
        # executed marker in input; an echoed command cannot satisfy readiness.
        self.send(
            command
            + "; PS1='PTY-READY> '; PROMPT=$PS1; "
            + f"printf '\\n%s%s\\n' DONE-{token[:16]} {token[16:]}\n"
        )
        result = self.until("\r\n" + marker + "\r\n")
        # Wait past execution to the next prompt before sending terminal Ctrl-C.
        return result + self.until("PTY-READY> ")

    def close(self) -> None:
        inspection_error = None
        master_closed = False
        try:
            try:
                self.owned.update(descendant_depths(self.process.pid))
                for sig in (signal.SIGTERM, signal.SIGKILL):
                    self.owned.update(descendant_depths(self.process.pid))
                    # Deepest first: waiting shells can reap their children before
                    # they themselves are terminated, despite distinct job groups.
                    for pid in sorted(self.owned, key=self.owned.get, reverse=True):
                        try:
                            os.kill(pid, sig)
                        except ProcessLookupError:
                            continue
                        deadline = time.monotonic() + 0.5
                        while alive(pid) and time.monotonic() < deadline:
                            time.sleep(0.02)
            except (OSError, subprocess.SubprocessError) as exc:
                inspection_error = exc
            finally:
                # Closing the controlling terminal's master must precede wait:
                # macOS can otherwise keep even a killed shell in tty teardown.
                os.close(self.master)
                master_closed = True
                # Always reap our direct child, including inventory failures.
                if self.process.poll() is None:
                    self.process.terminate()
                try:
                    self.process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=2)
        finally:
            if not master_closed:
                os.close(self.master)
        deadline = time.monotonic() + 2
        while any(alive(pid) for pid in self.owned) and time.monotonic() < deadline:
            time.sleep(0.02)
        assert not [pid for pid in self.owned if alive(pid)], self.output.decode(errors="replace")
        if inspection_error is not None:
            raise inspection_error


@pytest.mark.parametrize("caller", ["bash", "zsh"])
def test_pty_parent_return_nested_ctrl_c(shell_install: CliInstall, caller: str) -> None:
    c = shell_install
    snapshot = install(c)
    if caller == "zsh":
        zsh = shutil.which("zsh")
        assert zsh, "The required available Zsh caller must be verified"
        args = [zsh, "-f", "-i"]
    else:
        args = [c.bash, "--noprofile", "--norc", "-i"]
    terminal = Terminal(args, c)
    try:
        baseline = terminal.command(
            'printf "PARENT:%s:%s:%s\\n" "$PWD" "${REMOTE_ENV_DIR-unset}" "${CHILD_ONLY-unset}"; '
            "alias rhelp >/dev/null 2>&1 && printf 'LEAKED-%s' ALIAS; "
            "typeset -f log >/dev/null && printf 'LEAKED-%s' FUNCTION; command -v ssh-find || :"
        )
        assert f"PARENT:{c.home}:unset:unset" in baseline
        assert str(c.root / "bin") not in baseline
        assert "LEAKED-ALIAS" not in baseline
        assert "LEAKED-FUNCTION" not in baseline
        terminal.send(shlex.quote(str(c.command)) + " shell\n")
        active = terminal.command(activation(c, c.root, c.home).strip())
        assert "ACTIVATED:" in active, active
        # Ctrl-C at the child's ready prompt must leave an ordinary usable shell.
        terminal.send("\x03")
        terminal.until("PTY-READY> ")
        assert "AFTER-INT" in terminal.command("printf 'AFTER-%s\\n' INT")
        terminal.command('export CHILD_ONLY=outer; printf "OUTER:%s\\n" "$$"')
        terminal.send(shlex.quote(str(c.command)) + " shell\n")
        inner = terminal.command('printf "INNER:%s:%s\\n" "$$" "$CHILD_ONLY"')
        assert ":outer" in inner
        terminal.send("export CHILD_ONLY=inner; exit 23\n")
        returned = terminal.command('printf "NESTED-RETURN:%s:%s\\n" "$?" "$CHILD_ONLY"')
        assert "NESTED-RETURN:23:outer" in returned
        terminal.send("cd /; export CHILD_ONLY=changed; exit 23\n")
        returned = terminal.command(
            'printf "RETURN:%s:%s:%s:%s\\n" "$?" "$PWD" "${REMOTE_ENV_DIR-unset}" "${CHILD_ONLY-unset}"; '
            "alias rhelp >/dev/null 2>&1 && printf 'LEAKED-%s' ALIAS; "
            "typeset -f log >/dev/null && printf 'LEAKED-%s' FUNCTION; command -v ssh-find || :"
        )
        assert f"RETURN:23:{c.home}:unset:unset" in returned, returned
        assert str(c.root / "bin") not in returned
        assert "LEAKED-ALIAS" not in returned
        assert "LEAKED-FUNCTION" not in returned
        terminal.send("exit\n")
    finally:
        terminal.close()
    unchanged(c, snapshot)


def test_pty_cleanup_covers_job_control_groups(shell_install: CliInstall) -> None:
    c = shell_install
    install(c)
    terminal = Terminal([c.bash, "--noprofile", "--norc", "-i"], c)
    owned: set[int] = set()
    try:
        terminal.command("printf 'PARENT-READY\\n'")
        terminal.send(shlex.quote(str(c.command)) + " shell\n")
        terminal.command("printf 'CHILD-READY\\n'")
        terminal.send(shlex.quote(str(c.command)) + " shell\n")
        terminal.command("printf 'NESTED-READY\\n'")
        owned = descendants(terminal.process.pid)
        assert len(owned) >= 2
        groups = {os.getpgid(pid) for pid in owned | {terminal.process.pid}}
        assert len(groups) >= 3, groups
    finally:
        terminal.close()
    assert not any(alive(pid) for pid in owned)


def test_exec_pid_and_native_signal(shell_install: CliInstall) -> None:
    c = shell_install
    snapshot = install(c)
    terminal = Terminal([c.command, "shell"], c)
    try:
        result = terminal.command('printf "EXEC-PID:%s\\n" "$$"')
        assert f"EXEC-PID:{terminal.process.pid}\r\n" in result
        os.kill(terminal.process.pid, signal.SIGKILL)
        assert terminal.process.wait(timeout=5) == -signal.SIGKILL
    finally:
        terminal.close()
    unchanged(c, snapshot)


def test_preinstall_guide_is_copyable_in_bash_and_zsh(shell_install: CliInstall) -> None:
    c = shell_install
    assert not c.command.exists()
    rendered = c.run("guide", "post-install")
    assert_ok(rendered)
    assert "@SHELL_COMMAND@" not in rendered.stdout
    assert "@INTERACTIVE_COMMAND@" not in rendered.stdout
    primary = next(line.strip() for line in rendered.stdout.splitlines() if line.endswith(" shell"))
    fallback = next(
        line.strip() for line in rendered.stdout.splitlines() if "  bash --rcfile " in line
    )
    callers = [[c.bash, "--noprofile", "--norc", "-c"]]
    zsh = shutil.which("zsh")
    assert zsh, "The available Zsh caller must be exercised"
    callers.append([zsh, "-f", "-c"])
    for caller in callers:
        capture = run(c, [*caller, "capture() { printf '%s\\0' \"$@\"; }; capture " + primary])
        assert_ok(capture)
        assert capture.stdout == str(c.root / "bin/remote-ssh") + "\0shell\0"
        manual = run(c, [*caller, "bash() { printf '%s\\0' \"$@\"; }; " + fallback])
        assert_ok(manual)
        assert manual.stdout == "--rcfile\0" + str(c.root / "shell/rc.sh") + "\0-i\0"
        for command in (primary, fallback):
            result = run(c, [*caller, command], input=activation(c, c.root, c.home) + "exit\n")
            assert_ok(result)
            assert "ACTIVATED:" in result.stdout
        assert not c.command.exists()
        assert not c.expected.exists()
