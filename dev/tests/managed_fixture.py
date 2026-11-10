from __future__ import annotations

from conftest import copy_public_tree

import hashlib
import shlex
import subprocess
import tarfile
from dataclasses import dataclass
from pathlib import Path

from conftest import IsolatedEnv, write_executable


@dataclass
class EngineEnv:
    repo: Path
    opt: Path
    bin: Path
    assets: Path
    env: dict[str, str]
    bash: str

    def private(self, body: str, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                self.bash,
                "-c",
                f"set -euo pipefail\n. {shlex.quote(str(self.repo / 'tools/lib/env.sh'))}\n"
                '. "$TOOLS_LIB_DIR/install.lib.sh"\n. "$TOOLS_LIB_DIR/install-tool.lib.sh"\n'
                '. "$TOOLS_LIB_DIR/managed.lib.sh"\n' + body,
                "_",
                *args,
            ],
            env=self.env,
            text=True,
            capture_output=True,
            timeout=120,
        )

    def install(self, *tools: str) -> subprocess.CompletedProcess[str]:
        return self.private(
            'ms_state_load\nms_install_preflight "$@"\nms_create_roots 1\n'
            'ms_lock_acquire "$MS_PREFIX" "$MS_BIN"\nms_state_load\nms_recovery_gate\nms_journal_prepare\n'
            'ms_install_preflight "$@"\nif [[ "$MS_ADOPTED" == 0 ]]; then ms_migration_commit; fi\n'
            'ms_recovery_gate\nms_install_batch "$@"\n',
            *tools,
        )

    def asset(
        self,
        tool: str,
        *,
        layout: str = "binary",
        version: str = "1.0",
        aliases: tuple[str, ...] = (),
    ) -> None:
        tree = self.assets / f"tree-{tool}"
        member = (
            f"lib/{tool}.so"
            if layout == "bash-builtin"
            else f"bin/{tool}"
            if layout == "bundle"
            else tool
        )
        write_executable(tree / member, f"#!/bin/sh\nprintf {tool}-{version}\\n\n")
        if layout == "bundle":
            (tree / "share/nvim/runtime").mkdir(parents=True, exist_ok=True)
            (tree / "share/nvim/runtime/data").write_text("required runtime data")
        asset = self.assets / f"{tool}.tar.gz"
        with tarfile.open(asset, "w:gz") as archive:
            for path in sorted(tree.rglob("*")):
                archive.add(
                    path,
                    arcname=("bundle/" if layout == "bundle" else "")
                    + str(path.relative_to(tree)),
                    recursive=False,
                )
        checksum = hashlib.sha256(asset.read_bytes()).hexdigest()
        extra = ""
        if layout == "bundle":
            extra = f'BINARY_PATH="{member}"\nBUNDLE_ROOTS=("{asset.name}|bundle")\nBUNDLE_REQUIRED_PATHS=("share/nvim/runtime")\n'
        elif layout == "bash-builtin":
            extra = f'LIBRARY_MEMBERS=("{asset.name}|{member}")\n'
        (self.repo / f"tools/defs/{tool}.sh").write_text(
            f"TOOL_NAME={tool}\nGH_REPO=local/{tool}\nRELEASE_TAG=v{version}\nVERSION={version}\n"
            f'BINARY_NAME={tool}\nINSTALL_LAYOUT={layout}\nASSETS=("linux:x86_64:gnu|{asset.name}")\n'
            f'CHECKSUMS=("{asset.name}|{checksum}")\nBINARY_ALIASES=({" ".join(aliases)})\n'
            + extra
        )


def make_engine(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str
) -> EngineEnv:
    repo = isolated_env.home / "repo"
    for rel in ["lib", "tools", "bin", "shell", "dots", "docs/post-install.d"]:
        copy_public_tree(repo_dir, rel, repo / rel)
    (repo / "tools/defs").mkdir(parents=True, exist_ok=True)
    for definition in (repo / "tools/defs").glob("*.sh"):
        definition.unlink()
    assets = isolated_env.home / "assets"
    assets.mkdir()
    opt = isolated_env.home / "opt"
    bin_dir = isolated_env.home / "install-bin"
    # The management interpreter is explicit; env-bash children select this
    # runtime too. The optional probe stub is separate and added only per test.
    (isolated_env.bin_dir / "bash").symlink_to(runtime_bash)
    write_executable(
        isolated_env.bin_dir / "uname",
        '#!/bin/sh\ncase "$1" in -s) echo Linux;; *) echo x86_64;; esac\n',
    )
    write_executable(isolated_env.bin_dir / "ldd", '#!/bin/sh\necho "GNU libc"\n')
    write_executable(
        isolated_env.bin_dir / "curl",
        '#!/bin/sh\nprintf "%s\\n" "$3" >>"$HOME/curl.calls"\ncp "$ASSET_DIR/${3##*/}" "$2"\n',
    )
    env = isolated_env.env | {
        "INSTALL_PREFIX": str(opt),
        "INSTALL_BIN_DIR": str(bin_dir),
        "REMOTE_ENV_DIR": str(repo),
        "ASSET_DIR": str(assets),
        "PATH": f"{bin_dir}:{isolated_env.env['PATH']}",
    }
    return EngineEnv(repo, opt, bin_dir, assets, env, runtime_bash)
