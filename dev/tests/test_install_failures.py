from __future__ import annotations

import hashlib
import shlex
import shutil
import tarfile
from pathlib import Path

import pytest
from conftest import IsolatedEnv, assert_failed, assert_ok, run_cmd, write_executable


@pytest.mark.parametrize(
    "failure,kind",
    [
        (failure, kind)
        for failure in ("checksum", "curl", "hash-command", "missing-hasher", "archive", "none")
        for kind in ("raw", "tar")
        if failure != "archive" or kind == "tar"
    ],
)
def test_public_installer_preserves_previous_release_on_download_failure(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str, kind: str, failure: str
) -> None:
    root = isolated_env.home / "installer"
    shutil.copytree(repo_dir / "lib", root / "lib")
    shutil.copytree(repo_dir / "tools" / "lib", root / "tools" / "lib")
    shutil.copy2(repo_dir / "tools" / "install-tool.sh", root / "tools" / "install-tool.sh")
    defs = root / "tools" / "defs"
    defs.mkdir()
    payload = isolated_env.home / "payload"
    write_executable(payload, "#!/bin/sh\nprintf new\n")
    asset = "demo.tar.gz" if kind == "tar" else "demo-raw"
    archive = isolated_env.home / "download"
    if kind == "tar":
        with tarfile.open(archive, "w:gz") as tar:
            tar.add(payload, arcname="demo")
    else:
        shutil.copy2(payload, archive)
    if failure == "archive":
        archive.write_bytes(b"not a valid archive")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if failure == "checksum":
        digest = "0" * 64
    (defs / "demo.sh").write_text(
        "TOOL_NAME=demo\nGH_REPO=owner/demo\nRELEASE_TAG=v1\nVERSION=1\nBINARY_NAME=demo\n"
        f'ASSETS=("linux:x86_64:musl|{asset}")\n'
        f'CHECKSUMS=("{asset}|{digest}")\nBINARY_ALIASES=(demo-alias)\n'
    )
    (isolated_env.bin_dir / "bash").symlink_to(runtime_bash)
    write_executable(
        isolated_env.bin_dir / "uname",
        "#!/bin/sh\ncase $1 in -s) echo Linux;; *) echo x86_64;; esac\n",
    )
    write_executable(
        isolated_env.bin_dir / "curl",
        f'#!/bin/sh\ncp {shlex.quote(str(archive))} "$2"\nexit {22 if failure == "curl" else 0}\n',
    )
    if failure == "hash-command":
        for command in ("sha256sum", "shasum"):
            write_executable(isolated_env.bin_dir / command, "#!/bin/sh\nexit 9\n")
    opt = isolated_env.home / "opt"
    old = opt / "demo-0" / "demo"
    write_executable(old, "#!/bin/sh\nprintf old\n")
    link = isolated_env.bin_dir / "demo"
    link.symlink_to(old)
    temp = isolated_env.home / "downloads"
    temp.mkdir()
    env = isolated_env.env | {
        "INSTALL_PREFIX": str(opt),
        "INSTALL_BIN_DIR": str(isolated_env.bin_dir),
        "TMPDIR": str(temp),
    }
    if failure == "missing-hasher":
        for command in (
            "dirname",
            "basename",
            "mkdir",
            "rm",
            "cp",
            "chmod",
            "grep",
            "sed",
            "find",
            "tar",
            "mktemp",
            "tr",
            "head",
            "mv",
            "ln",
            "readlink",
            "gzip",
        ):
            executable = shutil.which(command)
            assert executable
            (isolated_env.bin_dir / command).symlink_to(executable)
        env["PATH"] = str(isolated_env.bin_dir)
    result = run_cmd([runtime_bash, root / "tools" / "install-tool.sh", "demo"], env=env)
    if failure == "none":
        assert_ok(result)
        assert run_cmd([link], env=env).stdout == "new"
    else:
        assert_failed(result)
        assert link.readlink() == old
        assert run_cmd([link], env=env).stdout == "old"
        assert not (opt / "demo-1").exists()
    assert list(temp.iterdir()) == []


def test_install_without_optional_arrays_under_nounset(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str
) -> None:
    payload = isolated_env.home / "extract"
    write_executable(payload / "demo", "#!/bin/sh\nprintf demo\n")
    result = run_cmd(
        [
            runtime_bash,
            "-c",
            """
        set -euo pipefail
        . "$1/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/install-tool.lib.sh"
        install_binary demo demo 1 "$2"
        """,
            "_",
            repo_dir,
            payload,
        ],
        env=isolated_env.env
        | {
            "INSTALL_PREFIX": str(isolated_env.home / "opt"),
            "INSTALL_BIN_DIR": str(isolated_env.bin_dir),
        },
    )
    assert_ok(result)
    assert run_cmd([isolated_env.bin_dir / "demo"], env=isolated_env.env).stdout == "demo"
