from __future__ import annotations

import pytest

import check_assets_live


def test_parse_tool_defs_reads_assets_and_checksums() -> None:
    got = check_assets_live.parse_tool_defs(
        "\n".join(
            [
                "TOOL\tdemo\towner/repo\tv1.2.3",
                "ASSET\tdemo-linux.tar.gz",
                "ASSET\tdemo-darwin.zip",
                "CHECKSUM\tdemo-linux.tar.gz\t"
                "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                "END",
            ]
        )
    )

    assert got == [
        check_assets_live.ToolDef(
            name="demo",
            repo="owner/repo",
            tag="v1.2.3",
            assets=("demo-linux.tar.gz", "demo-darwin.zip"),
            checksums={
                "demo-linux.tar.gz": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
            },
        )
    ]


def test_parse_tool_defs_rejects_malformed_stream() -> None:
    with pytest.raises(check_assets_live.LiveCheckError):
        check_assets_live.parse_tool_defs("TOOL\tdemo\towner/repo\tv1.2.3\n")


def test_release_asset_names_and_digests() -> None:
    data = {
        "assets": [
            {
                "name": "one.tar.gz",
                "digest": "sha256:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            },
            {"name": "two.zip", "digest": "sha256:not-a-sha"},
            {"name": "three.tgz"},
        ]
    }

    assert check_assets_live.release_asset_names(data) == {
        "one.tar.gz",
        "two.zip",
        "three.tgz",
    }
    assert check_assets_live.release_asset_digests(data) == {
        "one.tar.gz": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    }


def test_parse_sha256_text() -> None:
    got = check_assets_live.parse_sha256_text(
        "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB  asset.tar.gz\n"
    )

    assert got == "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
