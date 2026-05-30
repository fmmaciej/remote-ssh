from __future__ import annotations

import textwrap
from pathlib import Path

from conftest import assert_ok, run_cmd


def _run_repo_bash(repo_dir: Path, script: str) -> str:
    result = run_cmd(
        ["bash", "-c", textwrap.dedent(script).lstrip(), "_", repo_dir],
        cwd=repo_dir,
    )
    assert_ok(result)
    return result.stdout.rstrip("\n")


def test_asset_name_mappings(repo_dir: Path) -> None:
    got = _run_repo_bash(
        repo_dir,
        r"""
        repo="$1"
        cd "$repo" || exit
        . "$repo/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/common.lib.sh"

        for def in "$repo"/tools/defs/*.sh; do
          unset TOOL_NAME GH_REPO RELEASE_TAG VERSION BINARY_NAME BINARY_ALIASES ASSETS CHECKSUMS
          . "$def"
          for rec in "${ASSETS[@]}"; do
            printf '%s|%s|%s\n' "$TOOL_NAME" "${rec%%|*}" "${rec#*|}"
          done
        done
        """,
    )

    expected = """atuin|darwin:aarch64:any|atuin-aarch64-apple-darwin.tar.gz
atuin|linux:aarch64:gnu|atuin-aarch64-unknown-linux-gnu.tar.gz
atuin|linux:aarch64:musl|atuin-aarch64-unknown-linux-musl.tar.gz
atuin|linux:x86_64:gnu|atuin-x86_64-unknown-linux-gnu.tar.gz
atuin|linux:x86_64:musl|atuin-x86_64-unknown-linux-musl.tar.gz
bat|darwin:aarch64:any|bat-v0.26.1-aarch64-apple-darwin.tar.gz
bat|darwin:x86_64:any|bat-v0.26.1-x86_64-apple-darwin.tar.gz
bat|linux:aarch64:musl|bat-v0.26.1-aarch64-unknown-linux-musl.tar.gz
bat|linux:x86_64:musl|bat-v0.26.1-x86_64-unknown-linux-musl.tar.gz
bat|linux:aarch64:gnu|bat-v0.26.1-aarch64-unknown-linux-gnu.tar.gz
bat|linux:x86_64:gnu|bat-v0.26.1-x86_64-unknown-linux-gnu.tar.gz
bottom|darwin:aarch64:any|bottom_aarch64-apple-darwin.tar.gz
bottom|darwin:x86_64:any|bottom_x86_64-apple-darwin.tar.gz
bottom|linux:aarch64:gnu|bottom_aarch64-unknown-linux-gnu.tar.gz
bottom|linux:aarch64:musl|bottom_aarch64-unknown-linux-musl.tar.gz
bottom|linux:x86_64:gnu|bottom_x86_64-unknown-linux-gnu-2-17.tar.gz
bottom|linux:x86_64:musl|bottom_x86_64-unknown-linux-musl.tar.gz
bssh|linux:aarch64:musl|bssh-linux-aarch64-musl.tar.gz
bssh|linux:aarch64:gnu|bssh-linux-aarch64.tar.gz
bssh|linux:x86_64:musl|bssh-linux-x86_64-musl.tar.gz
bssh|linux:x86_64:gnu|bssh-linux-x86_64.tar.gz
bssh|darwin:aarch64:any|bssh-macos-aarch64.zip
dust|linux:aarch64:gnu|dust-v1.2.4-aarch64-unknown-linux-gnu.tar.gz
dust|linux:aarch64:musl|dust-v1.2.4-aarch64-unknown-linux-musl.tar.gz
dust|darwin:x86_64:any|dust-v1.2.4-x86_64-apple-darwin.tar.gz
dust|linux:x86_64:gnu|dust-v1.2.4-x86_64-unknown-linux-gnu.tar.gz
dust|linux:x86_64:musl|dust-v1.2.4-x86_64-unknown-linux-musl.tar.gz
eza|linux:aarch64:gnu|eza_aarch64-unknown-linux-gnu.tar.gz
eza|linux:x86_64:musl|eza_x86_64-unknown-linux-musl.tar.gz
eza|linux:x86_64:gnu|eza_x86_64-unknown-linux-gnu.tar.gz
fd|darwin:aarch64:any|fd-v10.3.0-aarch64-apple-darwin.tar.gz
fd|darwin:x86_64:any|fd-v10.3.0-x86_64-apple-darwin.tar.gz
fd|linux:aarch64:musl|fd-v10.3.0-aarch64-unknown-linux-musl.tar.gz
fd|linux:x86_64:musl|fd-v10.3.0-x86_64-unknown-linux-musl.tar.gz
fd|linux:aarch64:gnu|fd-v10.3.0-aarch64-unknown-linux-gnu.tar.gz
fd|linux:x86_64:gnu|fd-v10.3.0-x86_64-unknown-linux-gnu.tar.gz
fzf|darwin:x86_64:any|fzf-0.67.0-darwin_amd64.tar.gz
fzf|darwin:aarch64:any|fzf-0.67.0-darwin_arm64.tar.gz
fzf|linux:x86_64:any|fzf-0.67.0-linux_amd64.tar.gz
fzf|linux:aarch64:any|fzf-0.67.0-linux_arm64.tar.gz
navi|darwin:aarch64:any|navi-v2.23.0-aarch64-apple-darwin.tar.gz
navi|darwin:x86_64:any|navi-v2.23.0-x86_64-apple-darwin.tar.gz
navi|linux:aarch64:gnu|navi-v2.23.0-aarch64-unknown-linux-gnu.tar.gz
navi|linux:x86_64:musl|navi-v2.23.0-x86_64-unknown-linux-musl.tar.gz
nu|darwin:aarch64:any|nu-0.112.2-aarch64-apple-darwin.tar.gz
nu|darwin:x86_64:any|nu-0.112.2-x86_64-apple-darwin.tar.gz
nu|linux:aarch64:musl|nu-0.112.2-aarch64-unknown-linux-musl.tar.gz
nu|linux:x86_64:musl|nu-0.112.2-x86_64-unknown-linux-musl.tar.gz
nu|linux:aarch64:gnu|nu-0.112.2-aarch64-unknown-linux-gnu.tar.gz
nu|linux:x86_64:gnu|nu-0.112.2-x86_64-unknown-linux-gnu.tar.gz
nvim|linux:aarch64:gnu|nvim-linux-arm64.tar.gz
nvim|linux:x86_64:gnu|nvim-linux-x86_64.tar.gz
nvim|darwin:aarch64:any|nvim-macos-arm64.tar.gz
nvim|darwin:x86_64:any|nvim-macos-x86_64.tar.gz
procs|linux:aarch64:gnu|procs-v0.14.11-aarch64-linux.zip
procs|linux:x86_64:gnu|procs-v0.14.11-x86_64-linux.zip
rg|darwin:aarch64:any|ripgrep-15.1.0-aarch64-apple-darwin.tar.gz
rg|darwin:x86_64:any|ripgrep-15.1.0-x86_64-apple-darwin.tar.gz
rg|linux:x86_64:musl|ripgrep-15.1.0-x86_64-unknown-linux-musl.tar.gz
rg|linux:aarch64:gnu|ripgrep-15.1.0-aarch64-unknown-linux-gnu.tar.gz
sd|darwin:aarch64:any|sd-v1.1.0-aarch64-apple-darwin.tar.gz
sd|darwin:x86_64:any|sd-v1.1.0-x86_64-apple-darwin.tar.gz
sd|linux:aarch64:musl|sd-v1.1.0-aarch64-unknown-linux-musl.tar.gz
sd|linux:x86_64:gnu|sd-v1.1.0-x86_64-unknown-linux-gnu.tar.gz
sd|linux:x86_64:musl|sd-v1.1.0-x86_64-unknown-linux-musl.tar.gz
starship|darwin:aarch64:any|starship-aarch64-apple-darwin.tar.gz
starship|darwin:x86_64:any|starship-x86_64-apple-darwin.tar.gz
starship|linux:aarch64:musl|starship-aarch64-unknown-linux-musl.tar.gz
starship|linux:x86_64:musl|starship-x86_64-unknown-linux-musl.tar.gz
starship|linux:x86_64:gnu|starship-x86_64-unknown-linux-gnu.tar.gz
tspin|darwin:aarch64:any|tailspin-aarch64-apple-darwin.tar.gz
tspin|darwin:x86_64:any|tailspin-x86_64-apple-darwin.tar.gz
tspin|linux:aarch64:musl|tailspin-aarch64-unknown-linux-musl.tar.gz
tspin|linux:x86_64:musl|tailspin-x86_64-unknown-linux-musl.tar.gz
vector|darwin:aarch64:any|vector-0.55.0-arm64-apple-darwin.tar.gz
vector|linux:aarch64:gnu|vector-0.55.0-aarch64-unknown-linux-gnu.tar.gz
vector|linux:aarch64:musl|vector-0.55.0-aarch64-unknown-linux-musl.tar.gz
vector|linux:x86_64:gnu|vector-0.55.0-x86_64-unknown-linux-gnu.tar.gz
vector|linux:x86_64:musl|vector-0.55.0-x86_64-unknown-linux-musl.tar.gz
yazi|darwin:aarch64:any|yazi-aarch64-apple-darwin.zip
yazi|darwin:x86_64:any|yazi-x86_64-apple-darwin.zip
yazi|linux:aarch64:musl|yazi-aarch64-unknown-linux-musl.zip
yazi|linux:x86_64:musl|yazi-x86_64-unknown-linux-musl.zip
yazi|linux:aarch64:gnu|yazi-aarch64-unknown-linux-gnu.zip
yazi|linux:x86_64:gnu|yazi-x86_64-unknown-linux-gnu.zip
zellij|darwin:aarch64:any|zellij-aarch64-apple-darwin.tar.gz
zellij|linux:aarch64:musl|zellij-aarch64-unknown-linux-musl.tar.gz
zellij|darwin:x86_64:any|zellij-x86_64-apple-darwin.tar.gz
zellij|linux:x86_64:musl|zellij-x86_64-unknown-linux-musl.tar.gz
zoxide|darwin:aarch64:any|zoxide-0.9.9-aarch64-apple-darwin.tar.gz
zoxide|darwin:x86_64:any|zoxide-0.9.9-x86_64-apple-darwin.tar.gz
zoxide|linux:aarch64:musl|zoxide-0.9.9-aarch64-unknown-linux-musl.tar.gz
zoxide|linux:x86_64:musl|zoxide-0.9.9-x86_64-unknown-linux-musl.tar.gz"""
    assert got == expected


def test_linux_gnu_asset_selection(repo_dir: Path) -> None:
    got = _run_repo_bash(
        repo_dir,
        r"""
        repo="$1"
        cd "$repo" || exit
        . "$repo/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/common.lib.sh"
        . "$TOOLS_LIB_DIR/install-tool/assets.sh"

        for def in "$repo"/tools/defs/*.sh; do
          unset TOOL_NAME GH_REPO RELEASE_TAG VERSION BINARY_NAME BINARY_ALIASES ASSETS CHECKSUMS
          . "$def"
          for platform in linux:x86_64:gnu linux:aarch64:gnu; do
            IFS=: read -r raw_os raw_arch libc <<<"$platform"
            asset="$(select_asset "$raw_os" "$raw_arch" "$libc" "${ASSETS[@]}")"
            printf '%s|%s|%s\n' "$TOOL_NAME" "$platform" "$asset"
          done
        done
        """,
    )

    expected = """atuin|linux:x86_64:gnu|atuin-x86_64-unknown-linux-musl.tar.gz
atuin|linux:aarch64:gnu|atuin-aarch64-unknown-linux-musl.tar.gz
bat|linux:x86_64:gnu|bat-v0.26.1-x86_64-unknown-linux-musl.tar.gz
bat|linux:aarch64:gnu|bat-v0.26.1-aarch64-unknown-linux-musl.tar.gz
bottom|linux:x86_64:gnu|bottom_x86_64-unknown-linux-musl.tar.gz
bottom|linux:aarch64:gnu|bottom_aarch64-unknown-linux-musl.tar.gz
bssh|linux:x86_64:gnu|bssh-linux-x86_64-musl.tar.gz
bssh|linux:aarch64:gnu|bssh-linux-aarch64-musl.tar.gz
dust|linux:x86_64:gnu|dust-v1.2.4-x86_64-unknown-linux-musl.tar.gz
dust|linux:aarch64:gnu|dust-v1.2.4-aarch64-unknown-linux-musl.tar.gz
eza|linux:x86_64:gnu|eza_x86_64-unknown-linux-musl.tar.gz
eza|linux:aarch64:gnu|eza_aarch64-unknown-linux-gnu.tar.gz
fd|linux:x86_64:gnu|fd-v10.3.0-x86_64-unknown-linux-musl.tar.gz
fd|linux:aarch64:gnu|fd-v10.3.0-aarch64-unknown-linux-musl.tar.gz
fzf|linux:x86_64:gnu|fzf-0.67.0-linux_amd64.tar.gz
fzf|linux:aarch64:gnu|fzf-0.67.0-linux_arm64.tar.gz
navi|linux:x86_64:gnu|navi-v2.23.0-x86_64-unknown-linux-musl.tar.gz
navi|linux:aarch64:gnu|navi-v2.23.0-aarch64-unknown-linux-gnu.tar.gz
nu|linux:x86_64:gnu|nu-0.112.2-x86_64-unknown-linux-musl.tar.gz
nu|linux:aarch64:gnu|nu-0.112.2-aarch64-unknown-linux-musl.tar.gz
nvim|linux:x86_64:gnu|nvim-linux-x86_64.tar.gz
nvim|linux:aarch64:gnu|nvim-linux-arm64.tar.gz
procs|linux:x86_64:gnu|procs-v0.14.11-x86_64-linux.zip
procs|linux:aarch64:gnu|procs-v0.14.11-aarch64-linux.zip
rg|linux:x86_64:gnu|ripgrep-15.1.0-x86_64-unknown-linux-musl.tar.gz
rg|linux:aarch64:gnu|ripgrep-15.1.0-aarch64-unknown-linux-gnu.tar.gz
sd|linux:x86_64:gnu|sd-v1.1.0-x86_64-unknown-linux-musl.tar.gz
sd|linux:aarch64:gnu|sd-v1.1.0-aarch64-unknown-linux-musl.tar.gz
starship|linux:x86_64:gnu|starship-x86_64-unknown-linux-musl.tar.gz
starship|linux:aarch64:gnu|starship-aarch64-unknown-linux-musl.tar.gz
tspin|linux:x86_64:gnu|tailspin-x86_64-unknown-linux-musl.tar.gz
tspin|linux:aarch64:gnu|tailspin-aarch64-unknown-linux-musl.tar.gz
vector|linux:x86_64:gnu|vector-0.55.0-x86_64-unknown-linux-musl.tar.gz
vector|linux:aarch64:gnu|vector-0.55.0-aarch64-unknown-linux-musl.tar.gz
yazi|linux:x86_64:gnu|yazi-x86_64-unknown-linux-musl.zip
yazi|linux:aarch64:gnu|yazi-aarch64-unknown-linux-musl.zip
zellij|linux:x86_64:gnu|zellij-x86_64-unknown-linux-musl.tar.gz
zellij|linux:aarch64:gnu|zellij-aarch64-unknown-linux-musl.tar.gz
zoxide|linux:x86_64:gnu|zoxide-0.9.9-x86_64-unknown-linux-musl.tar.gz
zoxide|linux:aarch64:gnu|zoxide-0.9.9-aarch64-unknown-linux-musl.tar.gz"""
    assert got == expected


def test_linux_glibc_asset_fallback(repo_dir: Path) -> None:
    got = _run_repo_bash(
        repo_dir,
        r"""
        repo="$1"
        cd "$repo" || exit
        . "$repo/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/common.lib.sh"
        . "$TOOLS_LIB_DIR/install-tool/assets.sh"

        ASSETS=(
          "linux:x86_64:glibc|tool-x86_64-linux-glibc.tgz"
          "linux:x86_64:any|tool-x86_64-linux-any.tgz"
        )
        select_asset linux x86_64 gnu "${ASSETS[@]}"
        """,
    )

    assert got == "tool-x86_64-linux-glibc.tgz"


def test_linux_any_asset_fallback(repo_dir: Path) -> None:
    got = _run_repo_bash(
        repo_dir,
        r"""
        repo="$1"
        cd "$repo" || exit
        . "$repo/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/common.lib.sh"
        . "$TOOLS_LIB_DIR/install-tool/assets.sh"

        ASSETS=(
          "linux:x86_64:any|tool-x86_64-linux-any.tgz"
        )
        select_asset linux x86_64 gnu "${ASSETS[@]}"
        """,
    )

    assert got == "tool-x86_64-linux-any.tgz"


def test_asset_selection_no_match(repo_dir: Path) -> None:
    _run_repo_bash(
        repo_dir,
        r"""
        repo="$1"
        cd "$repo" || exit
        . "$repo/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/common.lib.sh"
        . "$TOOLS_LIB_DIR/install-tool/assets.sh"

        ASSETS=(
          "linux:x86_64:any|tool-x86_64-linux-any.tgz"
        )
        if select_asset darwin aarch64 any "${ASSETS[@]}" >/dev/null; then
          printf 'Expected no matching asset for darwin/aarch64/any\n' >&2
          exit 1
        fi
        """,
    )


def test_checksum_manifest_contract(repo_dir: Path) -> None:
    _run_repo_bash(
        repo_dir,
        r"""
        repo="$1"
        cd "$repo" || exit
        . "$repo/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/common.lib.sh"

        for def in "$repo"/tools/defs/*.sh; do
          unset TOOL_NAME GH_REPO RELEASE_TAG VERSION BINARY_NAME BINARY_ALIASES ASSETS CHECKSUMS
          . "$def"

          for rec in "${CHECKSUMS[@]}"; do
            asset="${rec%%|*}"
            checksum="${rec#*|}"

            [[ $checksum =~ ^[0-9a-f]{64}$ ]] || {
              printf 'Invalid checksum for %s: %s\n' "$asset" "$checksum" >&2
              exit 1
            }

            found=0
            for asset_rec in "${ASSETS[@]}"; do
              [[ ${asset_rec#*|} == "$asset" ]] || continue
              found=1
              break
            done

            ((found == 1)) || {
              printf 'Checksum references unknown asset: %s\n' "$asset" >&2
              exit 1
            }
          done
        done
        """,
    )
