from __future__ import annotations

import json
import shutil
import textwrap
from pathlib import Path

import pytest
from conftest import IsolatedEnv, assert_failed, assert_ok, run_cmd, write_executable


def test_render_builtin_definition_has_explicit_library_members(repo_dir: Path):
    output = _run_repo_bash(
        repo_dir,
        r"""
      . "$1/tools/lib/env.sh"
      . "$TOOLS_LIB_DIR/generate-def.lib.sh"
      RELEASE_TAG=v1; VERSION=1
      GENERATE_LIBRARY_MEMBERS=('flyline-1-aarch64-apple-darwin.tar.gz|libflyline.dylib')
      ASSETS_EMIT=('"darwin:aarch64:any|flyline-1-aarch64-apple-darwin.tar.gz"')
      CHECKSUMS_EMIT=()
      render_defs flyline fixture/repo v1
    """,
    )
    assert 'INSTALL_LAYOUT="bash-builtin"' in output
    assert "LIBRARY_MEMBERS=(" in output and "libflyline.dylib" in output
    assert "BINARY_NAME=" not in output


def test_generate_skim_with_binary_name_override(repo_dir: Path, isolated_env: IsolatedEnv) -> None:
    assets = [
        "skim-aarch64-apple-darwin.tar.xz.sha256",
        "skim-aarch64-apple-darwin.tar.xz",
        "skim-x86_64-unknown-linux-musl.tar.xz",
        "skim-x86_64-pc-windows-msvc.zip",
        "source.tar.gz",
    ]
    fixture = isolated_env.home / "release.json"
    fixture.write_text(
        json.dumps(
            {
                "tag_name": "v5.9.0",
                "assets": [{"name": name, "digest": "sha256:" + "a" * 64} for name in assets],
            },
            indent=2,
        )
    )
    write_executable(isolated_env.bin_dir / "curl", '#!/bin/sh\ncat "$RELEASE_FIXTURE"\n')
    result = run_cmd(
        [
            "bash",
            repo_dir / "tools/generate-def.sh",
            "skim-rs/skim",
            "--tool",
            "sk",
            "--tag",
            "v5.9.0",
        ],
        env=isolated_env.env | {"RELEASE_FIXTURE": str(fixture)},
    )
    assert_ok(result)
    assert 'TOOL_NAME="sk"' in result.stdout
    assert 'BINARY_NAME="sk"' in result.stdout
    assert '"darwin:aarch64:any|skim-aarch64-apple-darwin.tar.xz"' in result.stdout
    assert '"linux:x86_64:musl|skim-x86_64-unknown-linux-musl.tar.xz"' in result.stdout
    assert f"skim-aarch64-apple-darwin.tar.xz|{'a' * 64}" in result.stdout
    assert "source.tar.gz" not in result.stdout
    assert ".sha256" not in result.stdout
    assert "windows" not in result.stdout
    assert "example" not in result.stdout


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
        got == "one.tar.gz|aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n"
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


def _generate_release_fixture(repo_dir, isolated_env, runtime_bash, tag, assets, arguments):
    checkout = isolated_env.home / "generator"
    for directory in ("lib", "tools"):
        shutil.copytree(repo_dir / directory, checkout / directory)
    fixture = isolated_env.home / "release.json"
    fixture.write_text(json.dumps({"tag_name": tag, "assets": assets}, indent=2))
    requests = isolated_env.home / "requests"
    write_executable(
        isolated_env.bin_dir / "curl",
        "#!/bin/sh\nfor argument do url=$argument; done\n"
        'printf "%s\\n" "$url" >> "$RELEASE_REQUESTS"\ncat "$RELEASE_FIXTURE"\n',
    )
    result = run_cmd(
        [runtime_bash, checkout / "tools/generate-def.sh", "fmmaciej/flyline", *arguments],
        env=isolated_env.env | {"RELEASE_FIXTURE": str(fixture), "RELEASE_REQUESTS": str(requests)},
    )
    return result, requests


@pytest.mark.parametrize("selector", ["--tag", "--version", None])
def test_generate_downstream_library_with_artifact_version(
    repo_dir, isolated_env, runtime_bash, selector
):
    tag = "remote-ssh-v1.10.0-pr974.aae68bb4.r5"
    version = "1.10.0-pr974.aae68bb4.r5"
    asset = f"flyline-{version}-aarch64-apple-darwin.tar.gz"
    checksum = "38a7c65eb6e3c8c7458cdebea36607ae2e5577279b96ce2f6e2907b5ff9afaf3"
    arguments = [
        "--artifact-version",
        version,
        "--library-member",
        f"{asset}|libflyline.dylib",
    ]
    if selector:
        arguments.extend([selector, tag])
    result, requests = _generate_release_fixture(
        repo_dir,
        isolated_env,
        runtime_bash,
        tag,
        [
            {"name": asset, "digest": f"sha256:{checksum}"},
            {"name": "SHA256SUMS", "digest": "sha256:" + "b" * 64},
            {"name": "provenance.json"},
        ],
        arguments,
    )
    assert_ok(result)
    assert f'RELEASE_TAG="{tag}"' in result.stdout
    assert f'VERSION="{version}"' in result.stdout
    assert 'INSTALL_LAYOUT="bash-builtin"' in result.stdout
    assert "LIBRARY_MEMBERS=(" in result.stdout and "libflyline.dylib" in result.stdout
    assert f'"darwin:aarch64:any|{asset}"' in result.stdout
    assert f'"{asset}|{checksum}"' in result.stdout
    assert "BINARY_NAME=" not in result.stdout
    assert "TODO" not in result.stdout and "example" not in result.stdout
    assert "provenance.json" not in result.stdout
    endpoint = f"tags/{tag}" if selector else "latest"
    assert requests.read_text().strip() == (
        f"https://api.github.com/repos/fmmaciej/flyline/releases/{endpoint}"
    )


@pytest.mark.parametrize("tag", ["v1.2.3", "1.2.3"])
def test_generate_without_artifact_version_preserves_tag_behavior(
    repo_dir, isolated_env, runtime_bash, tag
):
    asset = "flyline-1.2.3-aarch64-apple-darwin.tar.gz"
    result, requests = _generate_release_fixture(
        repo_dir,
        isolated_env,
        runtime_bash,
        tag,
        [{"name": asset, "digest": "sha256:" + "a" * 64}],
        ["--version", tag],
    )
    assert_ok(result)
    assert f'RELEASE_TAG="{tag}"' in result.stdout
    assert 'VERSION="1.2.3"' in result.stdout
    assert f'"darwin:aarch64:any|{asset}"' in result.stdout
    assert 'BINARY_NAME="flyline"' in result.stdout
    assert requests.read_text().strip().endswith(f"/releases/tags/{tag}")


@pytest.mark.parametrize(
    "value",
    [None, "", "../other", "1/2", ".", "..", "1 2", "1\n2", '1";echo bad', "--tag"],
)
def test_generate_rejects_invalid_artifact_version_before_request(
    repo_dir, isolated_env, runtime_bash, value
):
    arguments = ["--artifact-version"]
    if value is not None:
        arguments.append(value)
    result, requests = _generate_release_fixture(
        repo_dir,
        isolated_env,
        runtime_bash,
        "v1",
        [],
        arguments,
    )
    assert_failed(result)
    assert "--artifact-version" in result.stderr
    assert result.stdout == ""
    assert not requests.exists()
