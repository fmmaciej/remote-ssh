from __future__ import annotations

import shlex
from pathlib import Path

import pytest
from conftest import IsolatedEnv, assert_ok, run_cmd, write_executable


@pytest.mark.parametrize("cancel", [False, True])
def test_zi_uses_skim_after_zoxide_init(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str, cancel: bool
) -> None:
    target = isolated_env.home / "project with spaces"
    target.mkdir()
    queries = isolated_env.home / "query.args"
    write_executable(
        isolated_env.bin_dir / "zoxide",
        """#!/bin/sh
        if [ "$1" = init ]; then printf 'zi() { return 99; }\n'; exit 0; fi
        printf '%s\n' "$@" >"$QUERY_ARGS"
        printf '%s\n' "$TARGET"
        """,
    )
    write_executable(
        isolated_env.bin_dir / "sk",
        '#!/bin/sh\n[ "$CANCEL" = 0 ] || exit 130\ncat\n',
    )
    result = run_cmd(
        [
            runtime_bash,
            "--noprofile",
            "--norc",
            "-ic",
            """
        . "$1/lib/guards.sh"
        . "$1/lib/helpers.sh"
        . "$1/shell/rc.d/21-zoxide.sh"
        zi 'project pattern'
        printf 'status=%s\npwd=%s\n' "$?" "$PWD"
        """,
            "_",
            repo_dir,
        ],
        cwd=isolated_env.home,
        env=isolated_env.env
        | {
            "TARGET": str(target),
            "QUERY_ARGS": str(queries),
            "CANCEL": str(int(cancel)),
            "_ZO_ECHO": "1",
        },
    )
    assert_ok(result)
    assert queries.read_text().splitlines() == ["query", "--list", "--", "project pattern"]
    expected = (
        ["status=130", f"pwd={isolated_env.home}"]
        if cancel
        else [str(target), "status=0", f"pwd={target}"]
    )
    assert result.stdout.splitlines() == expected


@pytest.mark.parametrize("cancel", [False, True])
def test_z_completion_uses_skim_and_retains_upstream_readline_protocol(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str, cancel: bool
) -> None:
    target = isolated_env.home / "project with 'quotes'"
    target.mkdir()
    queries = isolated_env.home / "query.args"
    binds = isolated_env.home / "bind.args"
    reply = isolated_env.home / "reply"
    write_executable(
        isolated_env.bin_dir / "zoxide",
        """#!/bin/sh
        if [ "$1" = init ]; then cat "$ZOXIDE_INIT_FIXTURE"; exit 0; fi
        printf '%s\n' "$@" >"$QUERY_ARGS"
        case "$*" in *--interactive*) exit 99;; esac
        printf '%s\n' "$TARGET"
    """,
    )
    write_executable(isolated_env.bin_dir / "sk", '#!/bin/sh\n[ "$CANCEL" = 0 ] || exit 130\ncat\n')
    result = run_cmd(
        [
            runtime_bash,
            "--noprofile",
            "--norc",
            "-ic",
            r"""
        . "$1/lib/guards.sh"
        . "$1/lib/helpers.sh"
        . "$1/shell/rc.d/21-zoxide.sh"
        if ! declare -F __zoxide_z_complete >/dev/null; then
          printf 'unsupported-bash\n'
          exit 0
        fi
        bind() { printf '%s\n' "$*" >>"$BIND_ARGS"; }
        complete -p z
        COMP_WORDS=(z project '')
        COMP_CWORD=2
        COMPREPLY=(stale)
        __zoxide_z_complete
        printf 'status=%s\npwd=%s\n' "$?" "$PWD"
        : >"$REPLY"
        for entry in "${COMPREPLY[@]}"; do printf '%s\0' "$entry" >>"$REPLY"; done
        if [[ "$CANCEL" == 0 ]]; then
          __zoxide_z_complete_helper >/dev/null 2>&1 || true
          printf 'line=%s\npoint=%s\n' "$READLINE_LINE" "$READLINE_POINT"
        fi
        # A normal path prefix must still complete without invoking the picker.
        COMP_WORDS=(z project)
        COMP_CWORD=1
        __zoxide_z_complete
        printf 'directory=%s\n' "${COMPREPLY[@]}"
        """,
            "_",
            repo_dir,
        ],
        cwd=isolated_env.home,
        env=isolated_env.env
        | {
            "TERM": "xterm-256color",
            "TARGET": str(target),
            "QUERY_ARGS": str(queries),
            "BIND_ARGS": str(binds),
            "REPLY": str(reply),
            "CANCEL": str(int(cancel)),
            "ZOXIDE_INIT_FIXTURE": str(
                repo_dir / "dev/tests/fixtures/zoxide-0.10.0-completion.bash"
            ),
        },
    )
    assert_ok(result)
    if "unsupported-bash" in result.stdout:
        version = run_cmd(
            [runtime_bash, "-c", 'printf "%s %s" "${BASH_VERSINFO[0]}" "${BASH_VERSINFO[1]}"']
        )
        assert tuple(map(int, version.stdout.split())) < (4, 4)
        assert not queries.exists()
        return
    assert "-F __zoxide_z_complete" in result.stdout
    assert "status=0" in result.stdout
    assert f"pwd={isolated_env.home}" in result.stdout
    assert queries.read_text().splitlines() == [
        "query",
        "--list",
        "--exclude",
        str(isolated_env.home),
        "--",
        "project",
    ]
    assert reply.read_bytes() == (b"" if cancel else f"z#{target}/\0".encode())
    assert f"directory={target.name}" in result.stdout
    bindings = binds.read_text()
    if cancel:
        assert "redraw-current-line" in bindings
        assert "__zoxide_z_complete_helper" not in bindings
    else:
        line = next(
            line.removeprefix("line=")
            for line in result.stdout.splitlines()
            if line.startswith("line=")
        )
        assert shlex.split(line) == ["z", str(target)]
        assert f"point={len(line)}" in result.stdout
        assert "__zoxide_z_complete_helper" in bindings
