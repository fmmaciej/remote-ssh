from __future__ import annotations

import os
import textwrap
from pathlib import Path

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
