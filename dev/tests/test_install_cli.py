from __future__ import annotations

import os
import shlex
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest
from conftest import IsolatedEnv, assert_failed, assert_ok, mark_managed_release, write_executable


@dataclass
class CliInstall:
    root: Path
    env: dict[str, str]
    home: Path
    bin: Path
    transport: Path
    bash: str

    @property
    def command(self) -> Path:
        return self.bin / "remote-ssh"

    @property
    def expected(self) -> Path:
        return Path(self.env["XDG_CONFIG_HOME"]) / "remote-ssh/expected-tools"

    @property
    def network(self) -> Path:
        return self.home / "network.log"

    def run(self, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        return self.shell([self.bash, self.root / "bin/remote-ssh", *args], cwd=cwd)

    def shell(
        self, args: list[str | Path], *, cwd: Path | None = None
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(a) for a in args],
            env=self.env,
            cwd=cwd or self.home,
            text=True,
            capture_output=True,
            timeout=20,
            check=False,
        )


def prepare_cli_install(repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str) -> CliInstall:
    """Real runtime tree; only network/transport boundaries are replaced."""
    root = isolated_env.home / "repo space ' $ ; &"
    root.mkdir()
    for name in ("bin", "lib", "shell", "dots", "tools", "docs"):
        shutil.copytree(repo_dir / name, root / name)
    shutil.copy2(repo_dir / "runme.sh", root / "runme.sh")
    shutil.rmtree(root / "tools/defs")
    (root / "tools/defs").mkdir()
    for tool in ("demo", "second", "third"):
        (root / f"tools/defs/{tool}.sh").write_text(
            f"TOOL_NAME={tool}\nGH_REPO=owner/{tool}\nRELEASE_TAG=v1\nVERSION=1\n"
            f'BINARY_NAME={tool}\nASSETS=("linux:x86_64:any|{tool}")\n'
        )
    install_bin = isolated_env.home / "local bin ' $ ; &"
    install_bin.mkdir()
    prefix = isolated_env.home / "opt"
    binary = prefix / "demo-1/demo"
    write_executable(binary, "#!/bin/sh\nprintf demo\n")
    mark_managed_release(binary.parent, "demo", "1", executable="demo")
    (install_bin / "demo").symlink_to(binary)
    (isolated_env.bin_dir / "bash").symlink_to(runtime_bash)
    write_executable(
        isolated_env.bin_dir / "uname",
        "#!/bin/sh\ncase $1 in -s) echo Linux;; *) echo x86_64;; esac\n",
    )
    for network in ("curl", "wget", "git"):
        write_executable(
            isolated_env.bin_dir / network,
            f'#!/bin/sh\nprintf "%s\\n" "{network} $*" >> "$HOME/network.log"\nexit 99\n',
        )
    env = isolated_env.env.copy()
    for key in list(env):
        if key.startswith(("REMOTE_", "BASH_FUNC_")) or key in (
            "BASH_ENV",
            "ENV",
            "CDPATH",
            "SHELLOPTS",
            "BASHOPTS",
            "ZDOTDIR",
            "FORCE",
            "INSTALL_LAYOUT",
            "TOOLS_DIR",
            "REPO_DIR",
            "SSH_CONNECTION",
            "SSH_CLIENT",
        ):
            env.pop(key, None)
    env.update({"INSTALL_BIN_DIR": str(install_bin), "INSTALL_PREFIX": str(prefix)})
    for startup in (".bashrc", ".bash_profile", ".profile", ".zshrc", ".zshenv"):
        (isolated_env.home / startup).write_text("# untouched user startup\n")
    # Disable optional shell integrations, including the network-capable update hook.
    env["REMOTE_SSH_UPDATE_CHECK"] = "0"
    env["REMOTE_SSH_ENABLE_GIT_SESSION_IDENTITY"] = "0"
    return CliInstall(root, env, isolated_env.home, install_bin, isolated_env.bin_dir, runtime_bash)


@pytest.fixture
def cli_install(repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str) -> CliInstall:
    return prepare_cli_install(repo_dir, isolated_env, runtime_bash)


def footer_commands(output: str) -> tuple[str, str, str | None]:
    lines = output.splitlines()
    guide = next(line.strip().removeprefix("run: ") for line in lines if "  run: " in line)
    start = next(
        line.strip() for line in lines if line.startswith("  ") and line.rstrip().endswith(" shell")
    )
    export = next((line.strip() for line in lines if "  export PATH=" in line), None)
    return guide, start, export


@pytest.mark.parametrize("destination", ["custom", "default", "relative"])
def test_install_ownership_reinstall_and_destination(
    cli_install: CliInstall, destination: str
) -> None:
    c = cli_install
    if destination == "default":
        c.env.pop("INSTALL_BIN_DIR")
        c.bin = c.home / ".local/bin"
        c.bin.mkdir(parents=True)
        (c.bin / "demo").symlink_to(c.home / "opt/demo-1/demo")
    elif destination == "relative":
        c.env["INSTALL_BIN_DIR"] = os.path.relpath(c.bin, c.home)
    for _ in range(2):
        result = c.run("install", "--yes", "demo")
        assert_ok(result)
        assert c.command.readlink() == c.root / "bin/remote-ssh"
        assert set(p.name for p in c.bin.iterdir()) == {"demo", "remote-ssh"}
        assert c.expected.read_text().splitlines()[-1] == "demo"
        assert not c.network.exists()
    before = c.command.lstat()
    assert_ok(c.run("install"))  # Saved set needs no new confirmation.
    assert c.command.lstat().st_ino == before.st_ino
    other = c.home / "new bin"
    other.mkdir()
    (other / "demo").symlink_to(c.home / "opt/demo-1/demo")
    c.env["INSTALL_BIN_DIR"] = str(other)
    assert_ok(c.run("install", "--yes", "demo"))
    assert (other / "remote-ssh").readlink() == c.root / "bin/remote-ssh"
    assert c.command.readlink() == c.root / "bin/remote-ssh"


@pytest.mark.parametrize(
    "existing",
    [
        "file",
        "directory",
        "hardlink",
        "broken",
        "foreign",
        "relative",
        "chain",
        "spelling",
        "checkout",
    ],
)
def test_collision_is_nonmutating_before_confirmation(
    cli_install: CliInstall, existing: str
) -> None:
    c = cli_install
    source = c.root / "bin/remote-ssh"
    if existing == "file":
        c.command.write_text("keep me\n")
    elif existing == "directory":
        c.command.mkdir()
    elif existing == "hardlink":
        os.link(source, c.command)
    elif existing == "broken":
        c.command.symlink_to("missing")
    elif existing == "foreign":
        c.command.symlink_to("/bin/sh")
    elif existing == "relative":
        c.command.symlink_to(os.path.relpath(source, c.bin))
    elif existing == "chain":
        (c.bin / "indirect").symlink_to(source)
        c.command.symlink_to(c.bin / "indirect")
    elif existing == "spelling":
        c.command.symlink_to(str(c.root / "bin") + "/../bin/remote-ssh")
    else:
        other = c.home / "other checkout"
        shutil.copytree(c.root, other)
        c.command.symlink_to(other / "bin/remote-ssh")
    link = c.command.readlink() if c.command.is_symlink() else None
    inode = c.command.lstat().st_ino
    source.chmod(0o644)  # Preflight must not prepare the checkout on collision.
    result = c.run("install", "second")
    assert_failed(result)
    assert "refusing to replace" in result.stderr
    assert str(c.command) in result.stderr
    assert str(source) in result.stderr
    assert "No replacement was made" in result.stderr
    assert "requires confirmation" not in result.stderr
    assert not c.expected.exists()
    assert not c.network.exists()
    assert source.stat().st_mode & 0o111 == 0
    assert c.command.lstat().st_ino == inode
    if link is not None:
        assert c.command.readlink() == link
    if existing == "directory":
        assert list(c.command.iterdir()) == []


@pytest.mark.parametrize("args", [("--bad",), ("--yes", "unknown"), ("demo",)])
def test_invalid_input_and_declined_confirmation_do_not_publish(
    cli_install: CliInstall, args: tuple[str, ...]
) -> None:
    c = cli_install
    assert_failed(c.run("install", *args))
    assert not c.command.exists()
    assert not c.expected.exists()
    assert not c.network.exists()


def test_absent_bin_and_failure_after_publication(cli_install: CliInstall) -> None:
    c = cli_install
    c.bin = c.home / "absent/deep/bin"
    c.env["INSTALL_BIN_DIR"] = str(c.bin)
    result = c.run("install", "--yes", "second")
    assert_failed(result)
    assert c.command.readlink() == c.root / "bin/remote-ssh"
    assert not c.expected.exists()
    assert "Done." not in result.stdout
    assert "Installed CLI:" not in result.stdout
    assert c.network.read_text().startswith("curl ")
    assert_ok(c.shell([c.command, "--help"]))


@pytest.mark.parametrize("occupied", ["file", "directory", "symlink"])
def test_publication_rechecks_and_never_nests(cli_install: CliInstall, occupied: str) -> None:
    c = cli_install
    # A controlled ln boundary occupies the final entry after the last ownership
    # check, proving the real ln directory operand never descends into it.
    write_executable(
        c.transport / "ln",
        """#!/bin/sh
case "$OCCUPIED" in
file) printf keep > "$INSTALL_BIN_DIR/remote-ssh";;
directory) mkdir "$INSTALL_BIN_DIR/remote-ssh";;
symlink) ln_target="$HOME/foreign"; mkdir "$ln_target"; /bin/ln -s "$ln_target" "$INSTALL_BIN_DIR/remote-ssh";;
esac
exec /bin/ln "$@"
""",
    )
    c.env["OCCUPIED"] = occupied
    result = c.run("install", "--yes", "second")
    assert_failed(result)
    assert not c.network.exists()
    assert not c.expected.exists()
    assert not (c.command / "remote-ssh").exists()
    if occupied == "file":
        assert c.command.read_text() == "keep"
    elif occupied == "symlink":
        assert c.command.readlink() == c.home / "foreign"
    else:
        assert list(c.command.iterdir()) == []


def test_publication_recheck_before_ln(cli_install: CliInstall) -> None:
    c = cli_install
    write_executable(
        c.transport / "mkdir",
        """#!/bin/sh
/bin/mkdir "$@" || exit $?
case "$*" in *"local bin"*) printf occupied > "$INSTALL_BIN_DIR/remote-ssh";; esac
""",
    )
    result = c.run("install", "--yes", "second")
    assert_failed(result)
    assert "refusing to replace" in result.stderr
    assert c.command.read_text() == "occupied"
    assert not c.network.exists()


def test_bootstrap_links_override_and_doctor(cli_install: CliInstall) -> None:
    c = cli_install
    assert_ok(c.run("install", "--yes", "demo"))
    relative = c.bin / "relative"
    relative.symlink_to("remote-ssh")
    chain = c.home / "chain"
    chain.symlink_to(os.path.relpath(relative, c.home))
    for command in (c.root / "bin/remote-ssh", c.command, relative, chain):
        for args in (("--help",), ("guide", "post-install")):
            result = c.shell([command, *args], cwd=c.home.parent)
            assert_ok(result)
            assert "Usage: remote-ssh" in result.stdout or "Interactive usage" in result.stdout
    override = c.home / "override"
    shutil.copytree(c.root, override)
    c.env["REMOTE_ENV_DIR"] = str(override)
    assert str(override) in c.shell([c.command, "guide", "paths"]).stdout
    c.env["REMOTE_ENV_DIR"] = str(c.home / "missing checkout")
    doctor = c.shell([c.command, "doctor"])
    assert "missing checkout" in doctor.stdout
    assert "No such file" not in doctor.stderr
    c.env.pop("REMOTE_ENV_DIR")
    # More than 40 acyclic links bypass kernel execution depth by explicitly
    # reading them as a Bash script. The script's own bound is the assertion.
    previous = c.command
    for index in range(42):
        link = c.home / f"deep-{index}"
        link.symlink_to(previous)
        previous = link
    # BASH_SOURCE can be supplied by sourcing the real dispatcher from a wrapper
    # after replacing only its initial path expression in the disposable copy.
    bootstrap = (
        (c.root / "bin/remote-ssh")
        .read_text()
        .replace('script_path="${BASH_SOURCE[0]}"', f"script_path={shlex.quote(str(previous))}", 1)
    )
    wrapper = c.home / "bootstrap-depth"
    wrapper.write_text(bootstrap)
    result = c.shell([c.bash, wrapper, "--help"])
    assert_failed(result)
    assert "symlink depth exceeds 40" in result.stderr
    previous.unlink()
    previous.symlink_to("missing")
    wrapper.write_text(bootstrap)
    result = c.shell([c.bash, wrapper, "--help"])
    assert_failed(result)
    assert "cannot resolve CLI source" in result.stderr


def test_lifecycle_preserves_cli_and_user_paths(cli_install: CliInstall) -> None:
    c = cli_install
    assert_ok(c.run("install", "--yes", "demo"))
    startup = {p: p.read_bytes() for p in c.home.glob(".*") if p.is_file()}
    foreign = c.home / "opt/foreign-1"
    foreign.mkdir()
    assert_ok(c.shell([c.command, "uninstall", "--yes", "demo"]))
    assert not (c.bin / "demo").exists()
    assert not (c.home / "opt/demo-1").exists()
    stale = c.home / "opt/demo-0"
    write_executable(stale / "demo", "#!/bin/sh\nexit 0\n")
    mark_managed_release(stale, "demo", "0", executable="demo")
    assert "candidate:" in c.shell([c.command, "prune"]).stdout
    assert stale.exists()
    assert_ok(c.shell([c.command, "prune", "--apply"]))
    assert not stale.exists()
    assert c.command.is_symlink() and c.root.is_dir() and foreign.is_dir()
    assert_ok(c.shell([c.command, "--help"]))
    assert all(p.read_bytes() == before for p, before in startup.items())
    assert not c.network.exists()


@pytest.mark.parametrize("failure", ["demo", "second", "prefix"])
def test_tool_batch_failure_stops_without_completion(cli_install: CliInstall, failure: str) -> None:
    c = cli_install
    (c.bin / "demo").unlink()
    c.expected.parent.mkdir(parents=True)
    c.expected.write_text("# user sentinel\ndemo\n")
    c.env["FAIL_TOOL"] = failure
    write_executable(
        c.root / "tools/install-tool.sh",
        """#!/usr/bin/env bash
printf '%s\n' "$1" >> "$HOME/attempts"
[[ "$1" != "$FAIL_TOOL" ]] || exit 23
mkdir -p "$INSTALL_PREFIX/$1-1" || exit 1
printf '#!/bin/sh\nexit 0\n' > "$INSTALL_PREFIX/$1-1/$1"
chmod +x "$INSTALL_PREFIX/$1-1/$1"
ln -s "$INSTALL_PREFIX/$1-1/$1" "$INSTALL_BIN_DIR/$1"
""",
    )
    rcfile = c.root / "shell/rc.sh"
    rcfile.chmod(0o644)
    helper = c.root / "bin/ssh-find"
    helper.chmod(0o644)
    if failure == "prefix":
        invalid = c.home / "prefix-file"
        invalid.write_text("keep")
        c.env["INSTALL_PREFIX"] = str(invalid)
    # Exercise the facade in a conditional context too: explicit propagation
    # must work when Bash disables errexit for all nested function calls.
    script = """
. "$1/tools/lib/env.sh"
. "$TOOLS_LIB_DIR/commands.lib.sh"
if remote_ssh_cmd_install_main "$1" --yes demo second third; then exit 0; else exit 17; fi
"""
    result = c.shell([c.bash, "-c", script, "bash", c.root])
    assert result.returncode == 17
    attempts = c.home / "attempts"
    if failure == "prefix":
        assert not attempts.exists()
    else:
        assert attempts.read_text().splitlines() == (
            ["demo"] if failure == "demo" else ["demo", "second"]
        )
    if failure == "second":
        assert (c.bin / "demo").is_symlink()
        assert (c.home / "opt/demo-1/demo").is_file()
    assert c.expected.read_text() == "# user sentinel\ndemo\n"
    assert "Configuring environment" not in result.stdout
    assert rcfile.stat().st_mode & 0o111 == 0
    assert helper.stat().st_mode & 0o111 == 0
    assert "Done." not in result.stdout and "Installed CLI:" not in result.stdout
    assert c.command.is_symlink()
    assert_ok(c.shell([c.command, "--help"]))
    assert not c.network.exists()


def test_absent_destination_success_uses_real_tool_installer(cli_install: CliInstall) -> None:
    c = cli_install
    c.bin = c.home / "new/deep/bin"
    c.env["INSTALL_BIN_DIR"] = str(c.bin)
    # Supply a tiny raw fixture at the download boundary; all extraction,
    # staging, ownership records and tool symlink publication remain real.
    write_executable(
        c.transport / "curl",
        """#!/bin/sh
printf '%s\n' "$*" >> "$HOME/fixture-downloads"
[ "$1" = -fsSLo ] || exit 98
printf '#!/bin/sh\nprintf fixture-tool\n' > "$2"
""",
    )
    result = c.run("install", "--yes", "second")
    assert_ok(result)
    assert c.command.readlink() == c.root / "bin/remote-ssh"
    assert (c.bin / "second").is_symlink()
    assert (c.home / "opt/second-1/.remote-ssh-release").is_file()
    assert (c.home / "fixture-downloads").read_text().count("https://") == 1
    assert not c.network.exists()
    assert set(p.name for p in c.bin.iterdir()) == {"remote-ssh", "second"}


def test_install_respects_effective_checkout_override(cli_install: CliInstall) -> None:
    c = cli_install
    override = c.home / "effective checkout"
    shutil.copytree(c.root, override)
    c.env["REMOTE_ENV_DIR"] = str(override)
    result = c.run("install", "--yes", "demo")
    assert_ok(result)
    assert c.command.readlink() == override / "bin/remote-ssh"
    _, start, _ = footer_commands(result.stdout)
    assert shlex.split(start) == [str(c.command), "shell"]
    env = c.env | {
        "REMOTE_SSH_WELCOME": "0",
        "REMOTE_SSH_ENABLE_ATUIN": "0",
        "REMOTE_SSH_ENABLE_ATUIN_AUTO_IMPORT": "0",
        "XDG_CACHE_HOME": str(c.home / ".cache"),
    }
    activation = subprocess.run(
        [c.bash, "--noprofile", "--norc", "-c", start],
        env=env,
        cwd=c.home,
        input='printf "EFFECTIVE:%s\\n" "$REMOTE_ENV_DIR"\nexit\n',
        text=True,
        capture_output=True,
        timeout=20,
        check=False,
    )
    assert_ok(activation)
    assert f"EFFECTIVE:{override}\n" in activation.stdout
    assert c.command.readlink() == override / "bin/remote-ssh"
    assert_ok(c.shell([c.command, "--help"]))


def test_env_bash_children_use_selected_runtime(cli_install: CliInstall) -> None:
    c = cli_install
    parent = c.shell([c.bash, "-c", 'printf "%s" "$BASH_VERSION"'])
    child = c.shell(["/usr/bin/env", "bash", "-c", 'printf "%s" "$BASH_VERSION"'])
    assert_ok(parent)
    assert_ok(child)
    assert child.stdout == parent.stdout
