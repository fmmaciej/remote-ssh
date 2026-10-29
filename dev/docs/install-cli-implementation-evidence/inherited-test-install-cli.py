from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from conftest import IsolatedEnv, assert_failed, assert_ok, run_cmd, write_executable


def _prepare_install(repo_dir: Path, isolated_env: IsolatedEnv) -> tuple[Path, dict[str, str]]:
    root = isolated_env.home / "repo with spaces"
    shutil.copytree(repo_dir / "lib", root / "lib")
    shutil.copytree(repo_dir / "tools/lib", root / "tools/lib")
    shutil.copytree(repo_dir / "docs/post-install.d", root / "docs/post-install.d")
    shutil.copytree(repo_dir / "shell", root / "shell")
    shutil.copytree(repo_dir / "dots", root / "dots")
    (root / "bin").mkdir()
    shutil.copy2(repo_dir / "bin/remote-ssh", root / "bin/remote-ssh")
    write_executable(root / "shell/rc.sh", "#!/bin/bash\n:\n")
    (root / "tools/defs").mkdir()
    (root / "tools/defs/demo.sh").write_text(
        'TOOL_NAME=demo\nGH_REPO=owner/demo\nRELEASE_TAG=v1\nVERSION=1\nBINARY_NAME=demo\n'
        'ASSETS=("linux:x86_64:any|demo")\n'
    )
    install_bin = isolated_env.home / "local bin ' $"
    install_bin.mkdir()
    binary = isolated_env.home / "opt/demo-1/demo"
    write_executable(binary, "#!/bin/sh\nexit 0\n")
    (install_bin / "demo").symlink_to(binary)
    write_executable(
        isolated_env.bin_dir / "uname",
        "#!/bin/sh\ncase $1 in -s) echo Linux;; *) echo x86_64;; esac\n",
    )
    write_executable(isolated_env.bin_dir / "curl", "#!/bin/sh\nexit 99\n")
    env = isolated_env.env | {
        "INSTALL_BIN_DIR": str(install_bin),
        "INSTALL_PREFIX": str(isolated_env.home / "opt"),
    }
    env.pop("REMOTE_ENV_DIR", None)
    return root, env


def test_install_exposes_cli_and_prints_working_local_startup(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str
) -> None:
    root, env = _prepare_install(repo_dir, isolated_env)
    # Children launched through /usr/bin/env use the same runtime as the installer.
    (isolated_env.bin_dir / "bash").symlink_to(runtime_bash)
    command = Path(env["INSTALL_BIN_DIR"]) / "remote-ssh"
    for _ in range(2):
        result = run_cmd([runtime_bash, root / "bin/remote-ssh", "install", "--yes", "demo"], env=env)
        assert_ok(result)
        assert command.is_symlink()
        assert command.resolve() == root / "bin/remote-ssh"

        export = next(line.strip() for line in result.stdout.splitlines() if "export PATH=" in line)
        guide = run_cmd([runtime_bash, "-c", f"{export}\nremote-ssh guide post-install"], env=env)
        assert_ok(guide)
        assert f'bash --rcfile "{root}/shell/rc.sh" -i' in guide.stdout
        assert "@INSTALL_DIR@" not in guide.stdout

        start = next(line.strip() for line in result.stdout.splitlines() if "bash --rcfile " in line)
        shell = run_cmd([runtime_bash, "-c", f"{start} -c 'printf local-shell-ok'"], env=env)
        assert_ok(shell)
        assert shell.stdout == "local-shell-ok"

    relative = command.parent / "relative-remote-ssh"
    relative.symlink_to("remote-ssh")
    help_result = run_cmd([relative, "--help"], env=env)
    assert_ok(help_result)
    assert "Usage: remote-ssh" in help_result.stdout


@pytest.mark.parametrize("existing", ["file", "directory", "symlink"])
def test_install_preserves_conflicting_cli_path(
    repo_dir: Path, isolated_env: IsolatedEnv, existing: str
) -> None:
    root, env = _prepare_install(repo_dir, isolated_env)
    command = Path(env["INSTALL_BIN_DIR"]) / "remote-ssh"
    if existing == "file":
        command.write_text("keep me\n")
    elif existing == "directory":
        command.mkdir()
    else:
        command.symlink_to("missing-command")

    result = run_cmd(["bash", root / "bin/remote-ssh", "install", "--yes", "demo"], env=env)
    assert_failed(result)
    assert "refusing to replace" in result.stderr
    assert "Done." not in result.stdout
    if existing == "file":
        assert command.read_text() == "keep me\n"
    elif existing == "directory":
        assert command.is_dir()
        assert list(command.iterdir()) == []
    else:
        assert command.readlink() == Path("missing-command")
