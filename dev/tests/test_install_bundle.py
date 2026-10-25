from __future__ import annotations

import io
import shlex
import shutil
import tarfile
from pathlib import Path

import pytest
from conftest import IsolatedEnv, assert_failed, assert_ok, run_cmd, write_executable


@pytest.mark.parametrize(
    "unsafe",
    [
        "none",
        "traversal",
        "absolute",
        "symlink",
        "hardlink",
        "fifo",
        "directory",
        "missing",
        "not-executable",
        "staged-directory",
    ],
)
def test_bundle_installer_preserves_runtime_and_rejects_invalid_package(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str, unsafe: str
) -> None:
    root = isolated_env.home / "installer"
    shutil.copytree(repo_dir / "lib", root / "lib")
    shutil.copytree(repo_dir / "tools" / "lib", root / "tools" / "lib")
    shutil.copy2(repo_dir / "tools" / "install-tool.sh", root / "tools" / "install-tool.sh")
    defs = root / "tools" / "defs"
    defs.mkdir()
    shutil.copy2(repo_dir / "tools" / "defs" / "nvim.sh", defs / "nvim.sh")
    with (defs / "nvim.sh").open("a") as definition:
        definition.write("\nBINARY_ALIASES=(nvim-alias)\n")
    package = "nvim-macos-arm64"
    archive = isolated_env.home / "bundle.tar.gz"
    outside = isolated_env.home / "escaped"
    with tarfile.open(archive, "w:gz") as tar:
        members = [(f"{package}/share/nvim/runtime/filetype.lua", b"runtime\n", 0o644)]
        if unsafe not in {"directory", "missing"}:
            members.append(
                (
                    f"{package}/bin/nvim",
                    b"#!/bin/sh\nprintf new\n",
                    0o644 if unsafe == "not-executable" else 0o755,
                )
            )
        for name, data, mode in members:
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mode = mode
            tar.addfile(info, io.BytesIO(data))
        if unsafe == "directory":
            info = tarfile.TarInfo(f"{package}/bin/nvim")
            info.type = tarfile.DIRTYPE
            info.mode = 0o755
            tar.addfile(info)
        if unsafe in {"traversal", "absolute", "symlink", "hardlink", "fifo"}:
            info = tarfile.TarInfo(f"{package}/bad")
            if unsafe == "traversal":
                info.name = "../escaped"
            elif unsafe == "absolute":
                info.name = str(outside)
            elif unsafe in {"symlink", "hardlink"}:
                info.type = tarfile.SYMTYPE if unsafe == "symlink" else tarfile.LNKTYPE
                info.linkname = str(outside)
            elif unsafe == "fifo":
                info.type = tarfile.FIFOTYPE
            tar.addfile(info)
    (isolated_env.bin_dir / "bash").symlink_to(runtime_bash)
    write_executable(
        isolated_env.bin_dir / "uname",
        "#!/bin/sh\ncase $1 in -s) echo Darwin;; *) echo arm64;; esac\n",
    )
    write_executable(
        isolated_env.bin_dir / "curl", f'#!/bin/sh\ncp {shlex.quote(str(archive))} "$2"\n'
    )
    if unsafe == "staged-directory":
        real_cp = shutil.which("cp")
        assert real_cp
        write_executable(
            isolated_env.bin_dir / "cp",
            f"""#!/bin/sh
            {shlex.quote(real_cp)} "$@" || exit 1
            # Simulate a candidate changed while copying into staging.
            if [ "$#" = 3 ] && [ "$1" = -R ]; then
              rm "${{3%/}}/bin/nvim"
              mkdir "${{3%/}}/bin/nvim"
            fi
            """,
        )
    opt = isolated_env.home / "opt"
    old = opt / "nvim-0.11.5" / "nvim"
    write_executable(old, "#!/bin/sh\nprintf old\n")
    link = isolated_env.bin_dir / "nvim"
    link.symlink_to(old)
    alias = isolated_env.bin_dir / "nvim-alias"
    alias.symlink_to(old)
    downloads = isolated_env.home / "downloads"
    downloads.mkdir()
    env = isolated_env.env | {
        "INSTALL_PREFIX": str(opt),
        "INSTALL_BIN_DIR": str(isolated_env.bin_dir),
        "TMPDIR": str(downloads),
    }
    result = run_cmd([runtime_bash, root / "tools" / "install-tool.sh", "nvim"], env=env)
    assert not outside.exists()
    assert list(downloads.iterdir()) == []
    if unsafe == "none":
        assert_ok(result)
        target = link.resolve()
        assert target.name == "nvim" and target.parent.name == "bin"
        release = target.parent.parent
        assert (release / "share/nvim/runtime/filetype.lua").read_text() == "runtime\n"
        assert "layout=bundle" in (release / ".remote-ssh-release").read_text()
        assert run_cmd([link], env=env).stdout == "new"
        assert alias.readlink() == link.readlink()
    else:
        assert_failed(result)
        assert link.readlink() == old
        assert alias.readlink() == old
        assert run_cmd([link], env=env).stdout == "old"
        assert run_cmd([alias], env=env).stdout == "old"
        assert old.read_text() == "#!/bin/sh\nprintf old\n"
        assert list(opt.iterdir()) == [old.parent]


def test_old_single_file_neovim_is_not_skipped(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str
) -> None:
    opt = isolated_env.home / "opt"
    old = opt / "nvim-0.11.5" / "nvim"
    write_executable(old, "#!/bin/sh\nexit 0\n")
    (isolated_env.bin_dir / "nvim").symlink_to(old)
    result = run_cmd(
        [
            runtime_bash,
            "-c",
            """
        set -euo pipefail
        . "$1/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/install.lib.sh"
        load_defs "$TOOLS_DIR/defs" nvim
        if is_tool_installed nvim 0.11.5; then exit 9; fi
        """,
            "_",
            repo_dir,
        ],
        env=isolated_env.env
        | {
            "INSTALL_PREFIX": str(opt),
            "INSTALL_BIN_DIR": str(isolated_env.bin_dir),
        },
    )
    assert_ok(result)
