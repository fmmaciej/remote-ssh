from __future__ import annotations

import textwrap
from pathlib import Path

from conftest import assert_ok, prepare_minimal_remote_tree, run_cmd, write_executable


def test_rc_loads_os_and_host_overrides(repo_dir: Path, tmp_path: Path) -> None:
    remote = prepare_minimal_remote_tree(repo_dir, tmp_path)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (remote / "shell" / "rc.d" / "os.d").mkdir()
    (remote / "shell" / "rc.d" / "host.d").mkdir()
    (remote / "shell" / "rc.d" / "10-base.sh").write_text(
        textwrap.dedent(
            """
            # shellcheck shell=bash
            ensure_this_file_sourced
            RC_FLOW="${RC_FLOW:-}:base"
            export RC_FLOW
            """
        ).lstrip(),
        encoding="utf-8",
    )
    (remote / "shell" / "rc.d" / "os.d" / "linux.sh").write_text(
        textwrap.dedent(
            """
            # shellcheck shell=bash
            ensure_this_file_sourced
            RC_FLOW="${RC_FLOW:-}:linux"
            export RC_FLOW
            """
        ).lstrip(),
        encoding="utf-8",
    )
    (remote / "shell" / "rc.d" / "host.d" / "testbox.sh").write_text(
        textwrap.dedent(
            """
            # shellcheck shell=bash
            ensure_this_file_sourced
            RC_FLOW="${RC_FLOW:-}:host"
            export RC_FLOW
            """
        ).lstrip(),
        encoding="utf-8",
    )
    write_executable(
        bin_dir / "uname",
        """
        #!/usr/bin/env bash
        printf 'Linux\\n'
        """,
    )
    write_executable(
        bin_dir / "hostname",
        """
        #!/usr/bin/env bash
        if [[ "${1:-}" == "-s" ]]; then
          printf 'testbox\\n'
        else
          printf 'testbox.example\\n'
        fi
        """,
    )

    result = run_cmd(
        [
            "bash",
            "-c",
            """
            set -euo pipefail
            PATH="$1:$PATH"
            . "$2/shell/rc.sh"
            printf '%s\n' "$RC_FLOW"
            """,
            "_",
            bin_dir,
            remote,
        ]
    )

    assert_ok(result)
    assert result.stdout.rstrip("\n") == ":base:linux:host"


def test_update_check_rc_skips_noninteractive_shells(repo_dir: Path, tmp_path: Path) -> None:
    remote = prepare_minimal_remote_tree(repo_dir, tmp_path)
    shutil_source = repo_dir / "shell" / "rc.d" / "04-update-check.sh"
    update_check = remote / "shell" / "rc.d" / "04-update-check.sh"
    update_check.write_text(shutil_source.read_text(encoding="utf-8"), encoding="utf-8")
    called = tmp_path / "called"
    write_executable(
        remote / "bin" / "remote-ssh",
        f"""
        #!/usr/bin/env bash
        touch {called}
        exit 1
        """,
    )

    result = run_cmd(
        [
            "bash",
            "-c",
            """
            set -euo pipefail
            export REMOTE_SSH_UPDATE_CHECK_STATE_DIR="$1/state"
            . "$2/shell/rc.sh"
            if [[ -e "$1/called" ]]; then
              printf 'called\n'
            else
              printf 'skipped\n'
            fi
            """,
            "_",
            tmp_path,
            remote,
        ]
    )

    assert_ok(result)
    assert result.stdout.rstrip("\n") == "skipped"
