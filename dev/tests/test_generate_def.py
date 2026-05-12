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


def test_generate_def_atuin_fixture(repo_dir: Path) -> None:
    got = _run_repo_bash(
        repo_dir,
        r"""
        repo="$1"
        cd "$repo" || exit
        . "$repo/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/generate-def.lib.sh"

        GITHUB_TAG="v18.14.1"
        GITHUB_ASSETS=(
          "atuin-aarch64-apple-darwin-update"
          "atuin-aarch64-apple-darwin.tar.gz"
          "atuin-aarch64-unknown-linux-gnu-update"
          "atuin-aarch64-unknown-linux-gnu.tar.gz"
          "atuin-x86_64-unknown-linux-gnu-update"
          "atuin-x86_64-unknown-linux-gnu.tar.gz"
          "atuin-aarch64-unknown-linux-musl-update"
          "atuin-aarch64-unknown-linux-musl.tar.gz"
          "atuin-x86_64-unknown-linux-musl-update"
          "atuin-x86_64-unknown-linux-musl.tar.gz"
          "atuin-x86_64-pc-windows-msvc.zip"
          "atuin-installer.sh"
          "atuin-aarch64-apple-darwin.tar.gz.sha256"
          "atuin-server-x86_64-apple-darwin.tar.gz"
        )
        GITHUB_ASSET_DIGESTS=(
          "atuin-aarch64-apple-darwin.tar.gz|1111111111111111111111111111111111111111111111111111111111111111"
          "atuin-aarch64-unknown-linux-gnu.tar.gz|2222222222222222222222222222222222222222222222222222222222222222"
          "atuin-x86_64-unknown-linux-gnu.tar.gz|3333333333333333333333333333333333333333333333333333333333333333"
          "atuin-aarch64-unknown-linux-musl.tar.gz|4444444444444444444444444444444444444444444444444444444444444444"
          "atuin-x86_64-unknown-linux-musl.tar.gz|5555555555555555555555555555555555555555555555555555555555555555"
          "atuin-server-x86_64-apple-darwin.tar.gz|6666666666666666666666666666666666666666666666666666666666666666"
        )

        tag_prefix_and_version "$GITHUB_TAG"
        detect_asset_prefix "atuin" "$VERSION" "${GITHUB_ASSETS[@]}"
        build_assets_from_assets "${GITHUB_ASSETS[@]}"
        build_checksums_from_emitted_assets
        render_defs "atuin" "atuinsh/atuin" "$GITHUB_TAG"
        """,
    )

    expected = """# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="atuin"
GH_REPO="atuinsh/atuin"
RELEASE_TAG="v18.14.1"
VERSION="18.14.1"

BINARY_NAME="atuin"

# "<os>:<arch>:<libc>|<asset_name>"
#
# Uwaga: szkic na podstawie assets z tagu: v18.14.1
ASSETS=(
  "darwin:aarch64:any|atuin-aarch64-apple-darwin.tar.gz"
  "linux:aarch64:gnu|atuin-aarch64-unknown-linux-gnu.tar.gz"
  "linux:x86_64:gnu|atuin-x86_64-unknown-linux-gnu.tar.gz"
  "linux:aarch64:musl|atuin-aarch64-unknown-linux-musl.tar.gz"
  "linux:x86_64:musl|atuin-x86_64-unknown-linux-musl.tar.gz"
)

CHECKSUMS=(
  "atuin-aarch64-apple-darwin.tar.gz|1111111111111111111111111111111111111111111111111111111111111111"
  "atuin-aarch64-unknown-linux-gnu.tar.gz|2222222222222222222222222222222222222222222222222222222222222222"
  "atuin-x86_64-unknown-linux-gnu.tar.gz|3333333333333333333333333333333333333333333333333333333333333333"
  "atuin-aarch64-unknown-linux-musl.tar.gz|4444444444444444444444444444444444444444444444444444444444444444"
  "atuin-x86_64-unknown-linux-musl.tar.gz|5555555555555555555555555555555555555555555555555555555555555555"
)"""
    assert got == expected


def test_github_parse_asset_digests(repo_dir: Path) -> None:
    got = _run_repo_bash(
        repo_dir,
        r"""
        repo="$1"
        cd "$repo" || exit
        . "$repo/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/generate-def.lib.sh"

        json='{
          "assets": [
            {"name": "one.tar.gz", "digest": "sha256:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"},
            {"name": "two.zip", "digest": "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"}
          ]
        }'
        github_parse_asset_digests "$json"
        """,
    )

    assert (
        got
        == "one.tar.gz|aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n"
        "two.zip|bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    )


def test_generate_def_infers_tool_from_repo(repo_dir: Path) -> None:
    got = _run_repo_bash(
        repo_dir,
        r"""
        repo="$1"
        cd "$repo" || exit
        . "$repo/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/generate-def.lib.sh"

        printf '%s\n' "$(infer_tool_name_from_repo chmln/sd)"
        printf '%s\n' "$(infer_tool_name_from_repo BurntSushi/ripgrep.git)"
        """,
    )

    assert got == "sd\nripgrep"


def test_github_parse_release_tags(repo_dir: Path) -> None:
    got = _run_repo_bash(
        repo_dir,
        r"""
        repo="$1"
        cd "$repo" || exit
        . "$repo/tools/lib/env.sh"
        . "$TOOLS_LIB_DIR/generate-def.lib.sh"

        json='[
          {"tag_name": "v1.2.0", "name": "one"},
          {"tag_name": "v1.1.0", "name": "two"}
        ]'
        github_parse_release_tags "$json"
        """,
    )

    assert got == "v1.2.0\nv1.1.0"
