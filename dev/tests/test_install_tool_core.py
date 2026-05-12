from __future__ import annotations

import shutil
import textwrap
from pathlib import Path

import pytest
from conftest import (
    IsolatedEnv,
    assert_failed,
    assert_ok,
    run_cmd,
    write_executable,
)


def _run_repo_bash(
    repo_dir: Path,
    script: str,
    *,
    cwd: Path | None = None,
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
        cwd=cwd or repo_dir,
        env=env,
    )
    assert_ok(result)
    return result.stdout.rstrip("\n")


def _run_repo_bash_failed(
    repo_dir: Path,
    script: str,
    *,
    cwd: Path | None = None,
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
        cwd=cwd or repo_dir,
        env=env,
    )
    assert_failed(result)
    return result.stdout + result.stderr


def _install_env(isolated_env: IsolatedEnv) -> dict[str, str]:
    return isolated_env.env | {
        "INSTALL_PREFIX": str(isolated_env.home / "opt"),
        "INSTALL_BIN_DIR": str(isolated_env.home / "bin"),
    }


def _make_fake_binary(path: Path) -> None:
    write_executable(path, "#!/usr/bin/env bash\n")


def _make_tar_archive(src: Path, archive: Path) -> None:
    result = run_cmd(["tar", "-C", src, "-czf", archive, "."], env=None)
    assert_ok(result)


def test_stage_tar_gz_asset(repo_dir: Path, isolated_env: IsolatedEnv) -> None:
    src = isolated_env.home / "src"
    work = isolated_env.home / "work"
    (src / "bin").mkdir(parents=True)
    work.mkdir()
    _make_fake_binary(src / "bin" / "demo")
    _make_tar_archive(src, work / "demo.tar.gz")

    _run_repo_bash(
        repo_dir,
        """
        repo="$1"
        . "$repo/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/install-tool.lib.sh"
        stage_downloaded_asset demo.tar.gz demo
        [[ -x "$PWD/bin/demo" ]]
        """,
        cwd=work,
        env=isolated_env.env,
    )


def test_stage_tgz_asset(repo_dir: Path, isolated_env: IsolatedEnv) -> None:
    src = isolated_env.home / "src"
    work = isolated_env.home / "work"
    (src / "bin").mkdir(parents=True)
    work.mkdir()
    _make_fake_binary(src / "bin" / "demo")
    _make_tar_archive(src, work / "demo.tgz")

    _run_repo_bash(
        repo_dir,
        """
        repo="$1"
        . "$repo/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/install-tool.lib.sh"
        stage_downloaded_asset demo.tgz demo
        [[ -x "$PWD/bin/demo" ]]
        """,
        cwd=work,
        env=isolated_env.env,
    )


def test_stage_zip_asset(repo_dir: Path, isolated_env: IsolatedEnv) -> None:
    if shutil.which("zip") is None or shutil.which("unzip") is None:
        pytest.skip("zip and unzip are required")

    src = isolated_env.home / "src"
    work = isolated_env.home / "work"
    (src / "bin").mkdir(parents=True)
    work.mkdir()
    _make_fake_binary(src / "bin" / "demo")
    result = run_cmd(["zip", "-qr", work / "demo.zip", "."], cwd=src, env=isolated_env.env)
    assert_ok(result)

    _run_repo_bash(
        repo_dir,
        """
        repo="$1"
        . "$repo/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/install-tool.lib.sh"
        ZIP_SUPPORTED=1
        stage_downloaded_asset demo.zip demo
        [[ -x "$PWD/bin/demo" ]]
        """,
        cwd=work,
        env=isolated_env.env,
    )


def test_stage_raw_executable_asset(repo_dir: Path, isolated_env: IsolatedEnv) -> None:
    work = isolated_env.home / "work"
    work.mkdir()
    (work / "demo-linux-amd64").write_text("#!/usr/bin/env bash\n", encoding="utf-8")

    _run_repo_bash(
        repo_dir,
        """
        repo="$1"
        . "$repo/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/install-tool.lib.sh"
        stage_downloaded_asset demo-linux-amd64 demo
        [[ -x "$PWD/demo" ]]
        """,
        cwd=work,
        env=isolated_env.env,
    )


def test_verify_asset_checksum_accepts_match(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    work = isolated_env.home / "work"
    work.mkdir()
    (work / "demo").write_text("hello\n", encoding="utf-8")
    checksum = "5891b5b522d5df086d0ff0b110fbd9d21bb4fc7163af34d08286a2e846f6be03"

    _run_repo_bash(
        repo_dir,
        """
        repo="$1"
        checksum="$2"
        . "$repo/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/install-tool.lib.sh"
        verify_asset_checksum demo "$checksum"
        """,
        cwd=work,
        env=isolated_env.env,
        args=[checksum],
    )


def test_verify_asset_checksum_rejects_mismatch(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    work = isolated_env.home / "work"
    work.mkdir()
    (work / "demo").write_text("hello\n", encoding="utf-8")

    got = _run_repo_bash_failed(
        repo_dir,
        """
        repo="$1"
        . "$repo/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/install-tool.lib.sh"
        verify_asset_checksum demo 0000000000000000000000000000000000000000000000000000000000000000
        """,
        cwd=work,
        env=isolated_env.env,
    )

    assert "Checksum mismatch for demo" in got


def _write_exact_def(defs: Path, asset_key: str) -> None:
    defs.mkdir(parents=True)
    (defs / "exact.sh").write_text(
        "\n".join(
            [
                "# shellcheck shell=bash",
                'TOOL_NAME="exact"',
                'GH_REPO="owner/repo"',
                'RELEASE_TAG="v1.2.3"',
                'VERSION="1.2.3"',
                'BINARY_NAME="exact"',
                "ASSETS=(",
                f'  "{asset_key}|exact.tar.gz"',
                ")",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _exact_manifest_error(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    *,
    req_version: str,
    asset_key: str,
) -> str:
    root = isolated_env.home / f"exact-{req_version or 'empty'}"
    tools = root / "tools"
    defs = root / "defs"
    tools.mkdir(parents=True)
    _write_exact_def(defs, asset_key)

    return _run_repo_bash_failed(
        repo_dir,
        """
        repo="$1"
        tools="$2"
        req_version="$3"
        . "$repo/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/install-tool.lib.sh"
        install_tool_main "$tools" exact "$req_version"
        """,
        env=isolated_env.env,
        args=[tools, req_version],
    )


def test_exact_manifest_rejects_latest(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    got = _exact_manifest_error(
        repo_dir,
        isolated_env,
        req_version="latest",
        asset_key="darwin:aarch64:any",
    )

    assert "supports only VERSION=1.2.3" in got
    assert "requested 'latest'" in got


def test_exact_manifest_rejects_other_version(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    got = _exact_manifest_error(
        repo_dir,
        isolated_env,
        req_version="9.9.9",
        asset_key="darwin:aarch64:any",
    )

    assert "supports only VERSION=1.2.3" in got
    assert "requested '9.9.9'" in got


def test_exact_manifest_reports_missing_asset(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    got = _exact_manifest_error(
        repo_dir,
        isolated_env,
        req_version="",
        asset_key="plan9:x86_64:any",
    )

    assert "No matching asset for exact" in got
    assert "Available assets:" in got
    assert "plan9:x86_64:any|exact.tar.gz" in got


def test_install_bin_idempotency(repo_dir: Path, isolated_env: IsolatedEnv) -> None:
    env = _install_env(isolated_env)
    opt = Path(env["INSTALL_PREFIX"])
    bin_dir = Path(env["INSTALL_BIN_DIR"])
    (opt / "rg-15.1.0").mkdir(parents=True)
    bin_dir.mkdir(parents=True)
    _make_fake_binary(opt / "rg-15.1.0" / "rg")
    (bin_dir / "rg").symlink_to(opt / "rg-15.1.0" / "rg")

    _run_repo_bash(
        repo_dir,
        """
        repo="$1"
        . "$repo/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/install.lib.sh"
        is_tool_installed rg 15.1.0
        """,
        env=env,
    )


def test_install_bin_ignores_external_path_tool(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    env = _install_env(isolated_env)
    opt = Path(env["INSTALL_PREFIX"])
    bin_dir = Path(env["INSTALL_BIN_DIR"])
    external = isolated_env.home / "external"
    opt.mkdir(parents=True)
    bin_dir.mkdir(parents=True)
    external.mkdir()
    _make_fake_binary(external / "rg")
    env = env | {"PATH": f"{external}:/usr/bin:/bin"}

    _run_repo_bash(
        repo_dir,
        """
        repo="$1"
        . "$repo/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/install.lib.sh"
        ! is_tool_installed rg 15.1.0
        """,
        env=env,
    )


def test_install_bin_reinstalls_stale_local_version(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    env = _install_env(isolated_env)
    opt = Path(env["INSTALL_PREFIX"])
    bin_dir = Path(env["INSTALL_BIN_DIR"])
    (opt / "rg-14.1.0").mkdir(parents=True)
    bin_dir.mkdir(parents=True)
    _make_fake_binary(opt / "rg-14.1.0" / "rg")
    (bin_dir / "rg").symlink_to(opt / "rg-14.1.0" / "rg")

    _run_repo_bash(
        repo_dir,
        """
        repo="$1"
        . "$repo/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/install.lib.sh"
        ! is_tool_installed rg 15.1.0
        """,
        env=env,
    )
