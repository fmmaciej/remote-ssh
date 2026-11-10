from __future__ import annotations

import io
import os
import shlex
import shutil
import stat
import tarfile
import textwrap
from pathlib import Path

import pytest
from conftest import IsolatedEnv, assert_failed, assert_ok, run_cmd, write_executable


def _install_env(isolated_env: IsolatedEnv) -> dict[str, str]:
    return isolated_env.env | {
        "INSTALL_PREFIX": str(isolated_env.home / "opt"),
        "INSTALL_BIN_DIR": str(isolated_env.home / "bin"),
    }


def _run_install_binary_bash(
    repo_dir: Path,
    script: str,
    *,
    env: dict[str, str],
    args: list[str | Path] | None = None,
) -> str:
    result = run_cmd(
        [
            "bash",
            "-c",
            textwrap.dedent(script).lstrip(),
            "_",
            repo_dir,
            *(args or []),
        ],
        cwd=repo_dir,
        env=env,
    )
    assert_ok(result)
    return result.stdout.rstrip("\n")


def _run_install_binary_bash_failed(
    repo_dir: Path,
    script: str,
    *,
    env: dict[str, str],
    args: list[str | Path] | None = None,
) -> str:
    result = run_cmd(
        [
            "bash",
            "-c",
            textwrap.dedent(script).lstrip(),
            "_",
            repo_dir,
            *(args or []),
        ],
        cwd=repo_dir,
        env=env,
    )
    assert_failed(result)
    return result.stdout + result.stderr


def test_install_binary_aliases(repo_dir: Path, isolated_env: IsolatedEnv) -> None:
    env = _install_env(isolated_env)
    extract = isolated_env.home / "extract"
    (extract / "bin").mkdir(parents=True)
    write_executable(extract / "bin" / "nu", "#!/usr/bin/env bash\n")

    _run_install_binary_bash(
        repo_dir,
        """
        repo="$1"
        extract="$2"
        . "$repo/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/install-tool.lib.sh"
        install_binary nu nu 1.2.3 "$extract" nushell
        """,
        env=env,
        args=[extract],
    )

    opt = Path(env["INSTALL_PREFIX"])
    bin_dir = Path(env["INSTALL_BIN_DIR"])
    assert os.readlink(bin_dir / "nu") == str(opt / "nu-1.2.3" / "nu")
    assert os.readlink(bin_dir / "nushell") == str(opt / "nu-1.2.3" / "nu")


def test_install_binary_preserves_existing_version_on_failure(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    env = _install_env(isolated_env)
    opt = Path(env["INSTALL_PREFIX"])
    bin_dir = Path(env["INSTALL_BIN_DIR"])
    extract = isolated_env.home / "extract"
    (opt / "demo-1.0.0").mkdir(parents=True)
    (extract / "bin").mkdir(parents=True)
    bin_dir.mkdir(parents=True)
    write_executable(opt / "demo-1.0.0" / "demo", "#!/usr/bin/env bash\nprintf old\n")
    write_executable(extract / "bin" / "demo", "#!/usr/bin/env bash\nprintf new\n")
    (extract / "bin" / "demo").chmod(0o111)
    (bin_dir / "demo").symlink_to(opt / "demo-1.0.0" / "demo")

    got = _run_install_binary_bash_failed(
        repo_dir,
        """
        repo="$1"
        extract="$2"
        . "$repo/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/install-tool.lib.sh"
        install_binary demo demo 1.0.0 "$extract"
        """,
        env=env,
        args=[extract],
    )

    assert os.readlink(bin_dir / "demo") == str(opt / "demo-1.0.0" / "demo")
    result = run_cmd([bin_dir / "demo"], env=env)
    assert_ok(result)
    assert result.stdout == "old"
    assert "Permission denied" in got


def test_install_binary_rejects_unmanaged_alias_without_switching_primary(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    env = _install_env(isolated_env)
    opt = Path(env["INSTALL_PREFIX"])
    bin_dir = Path(env["INSTALL_BIN_DIR"])
    extract = isolated_env.home / "extract"
    (opt / "nu-1.0.0").mkdir(parents=True)
    (extract / "bin").mkdir(parents=True)
    bin_dir.mkdir(parents=True)
    write_executable(opt / "nu-1.0.0" / "nu", "#!/usr/bin/env bash\nprintf old\n")
    write_executable(extract / "bin" / "nu", "#!/usr/bin/env bash\nprintf new\n")
    (bin_dir / "nu").symlink_to(opt / "nu-1.0.0" / "nu")
    (bin_dir / "nushell").write_text("not managed\n", encoding="utf-8")

    got = _run_install_binary_bash_failed(
        repo_dir,
        """
        repo="$1"
        extract="$2"
        . "$repo/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/install-tool.lib.sh"
        install_binary nu nu 2.0.0 "$extract" nushell
        """,
        env=env,
        args=[extract],
    )

    assert f"Refusing to replace unmanaged path: {bin_dir / 'nushell'}" in got
    assert os.readlink(bin_dir / "nu") == str(opt / "nu-1.0.0" / "nu")


def test_install_binary_rejects_alias_directory_without_switching_primary(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    env = _install_env(isolated_env)
    opt = Path(env["INSTALL_PREFIX"])
    bin_dir = Path(env["INSTALL_BIN_DIR"])
    extract = isolated_env.home / "extract"
    (opt / "nu-1.0.0").mkdir(parents=True)
    (extract / "bin").mkdir(parents=True)
    (bin_dir / "nushell").mkdir(parents=True)
    write_executable(opt / "nu-1.0.0" / "nu", "#!/usr/bin/env bash\nprintf old\n")
    write_executable(extract / "bin" / "nu", "#!/usr/bin/env bash\nprintf new\n")
    (bin_dir / "nu").symlink_to(opt / "nu-1.0.0" / "nu")

    got = _run_install_binary_bash_failed(
        repo_dir,
        """
        repo="$1"
        extract="$2"
        . "$repo/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/install-tool.lib.sh"
        install_binary nu nu 2.0.0 "$extract" nushell
        """,
        env=env,
        args=[extract],
    )

    assert f"Refusing to replace unmanaged path: {bin_dir / 'nushell'}" in got
    assert os.readlink(bin_dir / "nu") == str(opt / "nu-1.0.0" / "nu")


@pytest.mark.parametrize(
    "scenario",
    [
        "flat",
        "nested",
        "mixed",
        "ambiguous",
        "missing",
        "rejected",
        "literal-brackets",
        "literal-star",
        "literal-question",
        "spaces-apostrophes",
        "control-newline",
        "control-tab",
        "control-byte",
        "control-del",
        "explicit",
        "explicit-literal-target",
        "explicit-missing",
        "explicit-empty",
        "explicit-absolute",
        "explicit-traversal",
        "explicit-separators",
        "explicit-dot",
        "explicit-trailing",
        "explicit-backslash",
        "explicit-control",
        "explicit-symlink-parent",
        "explicit-symlink-file",
        "explicit-non-executable",
        "explicit-directory",
        "depth-four",
        "depth-five",
        "explicit-deep",
        "scanner-failure",
        "raw",
        "raw-literal",
        "raw-same-name",
    ],
)
def test_public_installer_selects_binary_or_preserves_previous_release(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str, scenario: str
) -> None:
    root = isolated_env.home / "installer"
    shutil.copytree(repo_dir / "lib", root / "lib")
    shutil.copytree(repo_dir / "tools/lib", root / "tools/lib")
    shutil.copy2(repo_dir / "tools/install-tool.sh", root / "tools/install-tool.sh")
    for code_dir in ("bin", "shell"):
        shutil.copytree(repo_dir / code_dir, root / code_dir)
    definitions = root / "tools/defs"
    definitions.mkdir()
    binary_name = "demo"
    binary_path: str | None = None
    members = [("bin/demo", "new")]
    expected_error = ""
    if scenario == "flat":
        members = [("demo", "new")]
    elif scenario == "nested":
        members = [("package/bin/demo", "new")]
    elif scenario == "mixed":
        members = [
            ("docs/demo", "non-executable"),
            ("directory/demo", "directory"),
            ("linked/demo", "symlink"),
            ("bin/demo", "new"),
        ]
    elif scenario == "ambiguous":
        members = [("first/demo", "new"), ("second/demo", "other")]
        expected_error = "Ambiguous binary"
    elif scenario == "missing":
        members = [("bin/other", "new")]
        expected_error = "No valid binary"
    elif scenario == "rejected":
        members = [
            ("docs/demo", "non-executable"),
            ("directory/demo", "directory"),
            ("linked/demo", "symlink"),
        ]
        expected_error = "No valid binary"
    elif scenario.startswith("literal-"):
        binary_name = {
            "literal-brackets": "demo[1]",
            "literal-star": "demo*",
            "literal-question": "demo?",
        }[scenario]
        members = [("bin/demo1", "other"), (f"bin/{binary_name}", "new")]
    elif scenario == "spaces-apostrophes":
        binary_name = "de mo's"
        members = [(f"package's bin/{binary_name}", "new")]
    elif scenario.startswith("control-"):
        control = {
            "control-newline": "\n",
            "control-tab": "\t",
            "control-byte": "\x01",
            "control-del": "\x7f",
        }[scenario]
        members = [(f"bad{control}folder/demo", "new")]
        expected_error = "unsafe relative path"
    elif scenario in {"explicit", "explicit-literal-target"}:
        if scenario == "explicit-literal-target":
            binary_name = "de mo's[1]*?"
        binary_path = "chosen/renamed"
        members = [
            ("first/demo", "other"),
            ("second/demo", "other"),
            (binary_path, "new"),
        ]
    elif scenario == "explicit-missing":
        binary_path = "missing/demo"
        expected_error = "not a regular file"
    elif scenario in {
        "explicit-empty",
        "explicit-absolute",
        "explicit-traversal",
        "explicit-separators",
        "explicit-dot",
        "explicit-trailing",
        "explicit-backslash",
        "explicit-control",
    }:
        binary_path = {
            "explicit-empty": "",
            "explicit-absolute": "/bin/demo",
            "explicit-traversal": "../demo",
            "explicit-separators": "bin//demo",
            "explicit-dot": "bin/./demo",
            "explicit-trailing": "bin/demo/",
            "explicit-backslash": "bin\\demo",
            "explicit-control": "bad\x01/demo",
        }[scenario]
        expected_error = "Invalid BINARY_PATH"
    elif scenario == "explicit-symlink-parent":
        binary_path = "shortcut/demo"
        members += [("shortcut", "symlink-parent")]
        expected_error = "symbolic link in path"
    elif scenario == "explicit-symlink-file":
        binary_path = "linked/demo"
        members += [(binary_path, "symlink")]
        expected_error = "symbolic link in path"
    elif scenario == "explicit-non-executable":
        binary_path = "docs/demo"
        members += [(binary_path, "non-executable")]
        expected_error = "not executable"
    elif scenario == "explicit-directory":
        binary_path = "directory/demo"
        members += [(binary_path, "directory")]
        expected_error = "not a regular file"
    elif scenario == "depth-four":
        members = [("a/b/c/demo", "new")]
    elif scenario in {"depth-five", "explicit-deep"}:
        members = [("a/b/c/d/demo", "new")]
        if scenario == "explicit-deep":
            binary_path = members[0][0]
        else:
            expected_error = "No valid binary"
    elif scenario == "scanner-failure":
        expected_error = "synthetic scan failure"
    elif scenario == "raw-literal":
        binary_name = "demo*"
    raw = scenario.startswith("raw")
    asset = (
        "demo"
        if scenario == "raw-same-name"
        else "demo-release"
        if raw
        else "demo.tar.gz"
    )
    archive = isolated_env.home / "asset"
    if raw:
        archive.write_bytes(b"#!/bin/sh\nprintf new\n")
    else:
        with tarfile.open(archive, "w:gz") as tar:
            for name, kind in members:
                info = tarfile.TarInfo(name)
                info.mode = 0o755
                if kind == "directory":
                    info.type = tarfile.DIRTYPE
                    tar.addfile(info)
                elif kind in {"symlink", "symlink-parent"}:
                    info.type = tarfile.SYMTYPE
                    info.linkname = "bin" if kind == "symlink-parent" else "../bin/demo"
                    tar.addfile(info)
                else:
                    data = f"#!/bin/sh\nprintf {kind if kind != 'non-executable' else 'other'}\n".encode()
                    info.size = len(data)
                    if kind == "non-executable":
                        info.mode = 0o644
                    tar.addfile(info, io.BytesIO(data))
    (definitions / "demo.sh").write_text(
        "TOOL_NAME=demo\nGH_REPO=owner/demo\nRELEASE_TAG=v1\nVERSION=1\n"
        f"BINARY_NAME={shlex.quote(binary_name)}\n"
        f'ASSETS=("linux:x86_64:musl|{asset}")\nBINARY_ALIASES=(demo-alias)\n'
        + (
            f"BINARY_PATH={shlex.quote(binary_path)}\n"
            if binary_path is not None
            else ""
        )
    )
    (isolated_env.bin_dir / "bash").symlink_to(runtime_bash)
    write_executable(
        isolated_env.bin_dir / "uname",
        "#!/bin/sh\ncase $1 in -s) echo Linux;; *) echo x86_64;; esac\n",
    )
    write_executable(
        isolated_env.bin_dir / "curl",
        f'#!/bin/sh\ncp {shlex.quote(str(archive))} "$2"\n',
    )
    if scenario == "scanner-failure":
        write_executable(
            isolated_env.bin_dir / "find",
            '#!/bin/sh\nprintf "%s\\000" "$1/bin/demo"\n'
            "printf 'synthetic scan failure\\n' >&2\nexit 9\n",
        )
    opt = isolated_env.home / "opt"
    old = opt / "demo-0" / "demo"
    write_executable(old, "#!/bin/sh\nprintf old\n")
    (old.parent / ".remote-ssh-release").write_text(
        "format=1\ntool=demo\nversion=0\nlayout=binary\nexecutable=demo\n"
    )
    link = isolated_env.bin_dir / "demo"
    alias = isolated_env.bin_dir / "demo-alias"
    link.symlink_to(old)
    alias.symlink_to(old)
    downloads = isolated_env.home / "downloads"
    downloads.mkdir()
    env = isolated_env.env | {
        "INSTALL_PREFIX": str(opt),
        "REMOTE_ENV_DIR": str(root),
        "INSTALL_BIN_DIR": str(isolated_env.bin_dir),
        "TMPDIR": str(downloads),
    }
    result = run_cmd(
        [runtime_bash, root / "bin/remote-ssh", "install", "demo", "--yes"], env=env
    )
    if expected_error:
        assert expected_error not in result.stdout, (
            "Selection diagnostic leaked onto stdout"
        )
    assert list(downloads.iterdir()) == [], (
        "Selection or download temporary files remain"
    )
    if expected_error:
        assert_failed(result)
        assert expected_error in result.stderr
        assert link.readlink() == old and alias.readlink() == old
        assert run_cmd([link], env=env).stdout == "old"
        assert run_cmd([alias], env=env).stdout == "old"
        assert all(
            path == old.parent or path.name.startswith(".") for path in opt.iterdir()
        )
        if scenario == "ambiguous":
            assert "first/demo" in result.stderr and "second/demo" in result.stderr
        if scenario == "rejected":
            for reason in (
                "not executable",
                "not a regular file",
                "symbolic link in path",
            ):
                assert reason in result.stderr
        if scenario == "control-newline":
            assert "bad\nfolder" not in result.stderr
            assert "bad\\nfolder" in result.stderr
        if scenario == "scanner-failure":
            assert "synthetic scan failure" in result.stderr
    else:
        assert_ok(result)
        assert run_cmd([link], env=env).stdout == "new"
        assert run_cmd([alias], env=env).stdout == "new"
        assert link.resolve().name == binary_name
        assert alias.readlink() == link.readlink()
        metadata = (link.resolve().parent / ".remote-ssh-release").read_text()
        assert "layout=binary\n" in metadata
        assert f"executable={binary_name}\n" in metadata


@pytest.mark.parametrize(
    "entrypoint,binary_name",
    [
        (entrypoint, name)
        for entrypoint in ("public", "binary", "bundle")
        for name in (
            "nested/demo",
            "../demo",
            "/demo",
            ".",
            "..",
            "demo\\name",
            "demo|record",
            "demo\nrecord",
            "",
        )
        if name or entrypoint != "public"
    ],
)
def test_invalid_binary_name_is_rejected_before_file_operations(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    runtime_bash: str,
    entrypoint: str,
    binary_name: str,
) -> None:
    root = isolated_env.home / "installer"
    shutil.copytree(repo_dir / "lib", root / "lib")
    shutil.copytree(repo_dir / "tools/lib", root / "tools/lib")
    shutil.copy2(repo_dir / "tools/install-tool.sh", root / "tools/install-tool.sh")
    for code_dir in ("bin", "shell"):
        shutil.copytree(repo_dir / code_dir, root / code_dir)
    definitions = root / "tools/defs"
    definitions.mkdir()
    (definitions / "demo.sh").write_text(
        "TOOL_NAME=demo\nGH_REPO=owner/demo\nRELEASE_TAG=v1\nVERSION=1\n"
        f"BINARY_NAME={shlex.quote(binary_name)}\nBINARY_PATH=bin/source\n"
        'ASSETS=("linux:x86_64:musl|demo.tar.gz")\nBINARY_ALIASES=(demo-alias)\n'
    )
    extract = isolated_env.home / "extract"
    write_executable(extract / "bin/source", "#!/bin/sh\nprintf new\n")
    write_executable(extract / "package/bin/source", "#!/bin/sh\nprintf new\n")
    opt = isolated_env.home / "opt"
    old = opt / "demo-0/demo"
    write_executable(old, "#!/bin/sh\nprintf old\n")
    metadata = old.parent / ".remote-ssh-release"
    metadata.write_text(
        "format=1\ntool=demo\nversion=0\nlayout=binary\nexecutable=demo\n"
    )
    sentinel = opt / "sentinel"
    sentinel.write_bytes(b"unchanged test data\n")
    sentinel.chmod(0o600)
    originals = {
        path: (path.read_bytes(), stat.S_IMODE(path.stat().st_mode))
        for path in (old, metadata, sentinel)
    }
    link = isolated_env.bin_dir / "demo"
    alias = isolated_env.bin_dir / "demo-alias"
    link.symlink_to(old)
    alias.symlink_to(old)
    downloads = isolated_env.home / "downloads"
    downloads.mkdir()
    operations = isolated_env.home / "operations"
    # These stubs prevent side effects even if a rejection regression occurs.
    for command in ("curl", "find", "mktemp", "mkdir", "cp"):
        write_executable(
            isolated_env.bin_dir / command,
            "#!/bin/sh\n"
            f"printf '%s\\n' {shlex.quote(command)} >>{shlex.quote(str(operations))}\n"
            "exit 99\n",
        )
    (isolated_env.bin_dir / "bash").symlink_to(runtime_bash)
    env = isolated_env.env | {
        "INSTALL_PREFIX": str(opt),
        "REMOTE_ENV_DIR": str(root),
        "INSTALL_BIN_DIR": str(isolated_env.bin_dir),
        "TMPDIR": str(downloads),
    }
    if entrypoint == "public":
        args = [runtime_bash, root / "bin/remote-ssh", "install", "demo", "--yes"]
    else:
        args = [
            runtime_bash,
            "-c",
            """
            set -euo pipefail
            . "$1/tools/lib/env.sh"
            . "$TOOLS_LIB_DIR/install-tool.lib.sh"
            INSTALL_LAYOUT="$4"
            BINARY_PATH=bin/source
            REMOTE_SSH_BINARY_PATH_EXPLICIT=1
            SELECTED_BUNDLE_ROOT=package
            install_binary demo "$2" 1 "$3" demo-alias
            """,
            "_",
            root,
            binary_name,
            extract,
            entrypoint,
        ]
    result = run_cmd(args, env=env)
    assert_failed(result)
    assert "Invalid BINARY_NAME" in result.stderr
    assert result.stdout == ""
    assert not operations.exists(), (
        "Invalid name reached download, scan, staging, or copy"
    )
    assert list(downloads.iterdir()) == []
    assert set(opt.iterdir()) == {old.parent, sentinel}
    assert link.readlink() == old and alias.readlink() == old
    assert run_cmd([link], env=env).stdout == "old"
    assert run_cmd([alias], env=env).stdout == "old"
    for path, original in originals.items():
        assert (path.read_bytes(), stat.S_IMODE(path.stat().st_mode)) == original
