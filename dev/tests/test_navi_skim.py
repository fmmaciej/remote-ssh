from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from conftest import IsolatedEnv, assert_ok, run_cmd, write_executable


@pytest.mark.parametrize("form", ["none", "separate", "equals"])
@pytest.mark.parametrize("status", [0, 130])
def test_navi_skim_adapter_preserves_arguments_and_status(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str, form: str, status: int
) -> None:
    real = isolated_env.bin_dir / "real-sk"
    write_executable(real, '#!/bin/sh\nprintf "%s\\0" "$@"\nexit "$SKIM_STATUS"\n')
    args = ["--prompt", "item > ", "--preview", "printf '%s\\n' {}", "--bind", "ctrl-j:down"]
    expected = ["--prompt=item > ", "--preview=printf '%s\\n' {}", "--bind=ctrl-j:down"]
    if form != "none":
        args += ["--expect", "tab,enter"] if form == "separate" else ["--expect=tab,enter"]
        expected += ["--bind=tab:accept(tab),enter:accept(enter)"]
    result = run_cmd(
        [runtime_bash, repo_dir / "shell/navi-bin/fzf", *args],
        env=isolated_env.env | {"REMOTE_SSH_NAVI_SK_BIN": str(real), "SKIM_STATUS": str(status)},
    )
    assert result.returncode == status
    assert result.stdout.split("\0")[:-1] == expected


@pytest.mark.parametrize(
    "select_flags,expected",
    [
        (["--select-1", "--no-select-1"], []),
        (["--no-select-1", "--select-1"], ["--select-1"]),
    ],
)
def test_adapter_handles_navi_free_input_flags(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    runtime_bash: str,
    select_flags: list[str],
    expected: list[str],
) -> None:
    real = isolated_env.bin_dir / "real-sk"
    write_executable(real, '#!/bin/sh\nprintf "%s\\0" "$@"\n')
    result = run_cmd(
        [
            runtime_bash,
            repo_dir / "shell/navi-bin/fzf",
            *select_flags,
            "--print-query",
            "--query",
            "--expect",
        ],
        env=isolated_env.env | {"REMOTE_SSH_NAVI_SK_BIN": str(real)},
    )
    assert_ok(result)
    # A query that happens to equal an option name stays opaque data.
    assert result.stdout.split("\0")[:-1] == ["--print-query", "--query=--expect", *expected]


def _fake_navi(isolated_env: IsolatedEnv) -> None:
    write_executable(
        isolated_env.bin_dir / "sk", '#!/bin/sh\nprintf "skim\\n"\nprintf "%s\\n" "$@"\n'
    )
    write_executable(isolated_env.bin_dir / "fzf", '#!/bin/sh\nprintf "native-fzf\\n"\n')
    write_executable(
        isolated_env.bin_dir / "navi",
        r"""#!/bin/bash
        finder="$NAVI_FINDER"
        while (($#)); do
          case "$1" in
            --finder) finder="$2"; shift 2 ;;
            --finder=*) finder="${1#*=}"; shift ;;
            *) break ;;
          esac
        done
        case "${1:-}" in
          --help) printf 'help\n'; exit 0 ;;
          nested)
            exec "$TEST_BASH" --noprofile --norc -c '
              . "$REPO/lib/guards.sh"
              . "$REPO/lib/helpers.sh"
              . "$REPO/shell/rc.d/24-navi.sh"
              navi leaf
            ' ;;
          child) exec navi leaf ;;
          absolute-child) exec "$0" leaf ;;
        esac
        # Pinned navi only includes the free-input flags in its fzf path.
        if [[ "$finder" == fzf ]]; then
          exec fzf --select-1 --print-query --no-select-1
        fi
        printf 'wrong-protocol\n'
        exit 99
    """,
    )


@pytest.mark.parametrize("mode", ["leaf", "nested", "child", "absolute-child"])
def test_session_routes_navi_protocol_without_recursive_adapters(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str, mode: str
) -> None:
    _fake_navi(isolated_env)
    result = subprocess.run(
        [
            runtime_bash,
            "-c",
            r"""
        set -euo pipefail
        . "$1/lib/guards.sh"
        . "$1/lib/helpers.sh"
        REMOTE_DOTS_DIR="$1/dots"
        REMOTE_SHELL_DIR="$1/shell"
        export REMOTE_DOTS_DIR REMOTE_SHELL_DIR
        . "$1/shell/rc.d/24-navi.sh"
        saved_path="$PATH"
        navi "$3"
        [[ "$PATH" == "$saved_path" && "$NAVI_FINDER" == skim ]]
        [[ "$SKIM_DEFAULT_OPTIONS" == 'user defaults' && "$SKIM_OPTIONS_FILE" == 'user file' ]]
        [[ -z "${REMOTE_SSH_NAVI_SK_BIN:-}" && -z "${REMOTE_SSH_NAVI_BIN:-}" ]]
        [[ "$(type -P sk)" == "$2/sk" ]]
        """,
            "_",
            repo_dir,
            isolated_env.bin_dir,
            mode,
        ],
        env=isolated_env.env
        | {
            "REPO": str(repo_dir),
            "TEST_BASH": runtime_bash,
            "NAVI_FINDER": "skim",
            "SKIM_DEFAULT_OPTIONS": "user defaults",
            "SKIM_OPTIONS_FILE": "user file",
        },
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    assert_ok(result)
    assert result.stdout.splitlines() == ["skim", "--print-query"]


def test_real_binary_resolution_skips_cached_adapters(
    repo_dir: Path, isolated_env: IsolatedEnv
) -> None:
    _fake_navi(isolated_env)
    dispatcher = repo_dir / "shell/navi-bin/navi"
    result = subprocess.run(
        [dispatcher],
        env=isolated_env.env
        | {
            "NAVI_FINDER": "skim",
            "REMOTE_SSH_NAVI_BIN": str(dispatcher),
            "REMOTE_SSH_NAVI_SK_BIN": str(repo_dir / "shell/navi-bin/fzf"),
        },
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    assert_ok(result)
    assert result.stdout.splitlines() == ["skim", "--print-query"]

    # A PATH containing only adapters must fail clearly, rather than recurse.
    result = subprocess.run(
        [dispatcher],
        env=isolated_env.env
        | {
            "NAVI_FINDER": "skim",
            "REMOTE_SSH_NAVI_BIN": str(dispatcher),
            "PATH": f"{repo_dir / 'shell/navi-bin'}:/usr/bin:/bin",
        },
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    assert result.returncode == 127
    assert "cannot find the real navi executable" in result.stderr


@pytest.mark.parametrize(
    "finder,args",
    [
        ("fzf", []),
        ("skim", ["--finder", "fzf"]),
        ("skim", ["--finder=fzf"]),
    ],
)
def test_explicit_fzf_bypasses_private_adapter(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str, finder: str, args: list[str]
) -> None:
    _fake_navi(isolated_env)
    # Native fzf must work even without skim installed.
    (isolated_env.bin_dir / "sk").unlink()
    result = run_cmd(
        [runtime_bash, repo_dir / "shell/navi-bin/navi", *args],
        env=isolated_env.env | {"NAVI_FINDER": finder},
    )
    assert_ok(result)
    assert result.stdout == "native-fzf\n"


@pytest.mark.parametrize("args", [[], ["--finder", "skim"], ["--finder=SKIM"]])
def test_explicit_skim_uses_fzf_protocol(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str, args: list[str]
) -> None:
    _fake_navi(isolated_env)
    result = run_cmd(
        [runtime_bash, repo_dir / "shell/navi-bin/navi", *args],
        env=isolated_env.env | {"NAVI_FINDER": "skim"},
    )
    assert_ok(result)
    assert result.stdout.splitlines() == ["skim", "--print-query"]


def test_adapter_rejects_itself_as_real_picker(repo_dir: Path, isolated_env: IsolatedEnv) -> None:
    adapter = repo_dir / "shell/navi-bin/fzf"
    result = run_cmd(
        [adapter, "--version"], env=isolated_env.env | {"REMOTE_SSH_NAVI_SK_BIN": str(adapter)}
    )
    assert result.returncode == 127
    assert "recursively" in result.stderr


def test_help_does_not_require_skim(repo_dir: Path, isolated_env: IsolatedEnv) -> None:
    _fake_navi(isolated_env)
    (isolated_env.bin_dir / "sk").unlink()
    result = run_cmd(
        [repo_dir / "shell/navi-bin/navi", "--help"], env=isolated_env.env | {"NAVI_FINDER": "skim"}
    )
    assert_ok(result)
    assert result.stdout == "help\n"


@pytest.mark.parametrize(
    "mode,status,expected",
    [
        ("automatic", 0, "alpha\n\nalpha\n"),
        ("interactive", 0, "alpha\nenter\nalpha\n"),
        ("custom", 1, "custom\nenter\n"),
        ("empty", 0, "\n\n\n"),
        ("filter", 0, "alpha\nalpha\n"),
    ],
)
def test_expected_key_protocol_includes_automatic_and_custom_values(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    runtime_bash: str,
    mode: str,
    status: int,
    expected: str,
) -> None:
    real = isolated_env.bin_dir / "real-sk"
    write_executable(
        real,
        r"""#!/bin/bash
        while (($#)); do
          if [[ "$1" == --bind=* ]]; then
            key="${1##*enter:accept(}"
            key="${key%%)*}"
          fi
          shift
        done
        case "$MODE" in
          automatic|filter) printf 'alpha\nalpha\n' ;;
          interactive) printf 'alpha\n%s\nalpha\n' "$key" ;;
          custom) printf 'custom\n%s\n' "$key" ;;
          empty) printf '\n\n' ;;
        esac
        exit "$STATUS"
    """,
    )
    args = ["--select-1", "--print-query", "--expect", "tab,enter"]
    if mode == "filter":
        args += ["--filter", "alpha"]
    result = run_cmd(
        [runtime_bash, repo_dir / "shell/navi-bin/fzf", *args],
        env=isolated_env.env
        | {"REMOTE_SSH_NAVI_SK_BIN": str(real), "MODE": mode, "STATUS": str(status)},
    )
    assert result.returncode == status
    assert result.stdout == expected


@pytest.mark.parametrize("option", ["--query", "-q", "--fzf-overrides", "--fzf-overrides-var"])
@pytest.mark.parametrize(
    "value", ["--finder=skim", "--finder=fzf", "--help", "-h", "--version", ""]
)
def test_dispatcher_keeps_option_values_opaque(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str, option: str, value: str
) -> None:
    write_executable(isolated_env.bin_dir / "navi", '#!/bin/sh\nprintf "%s\\0" "$@"\n')
    write_executable(isolated_env.bin_dir / "sk", "#!/bin/sh\nexit 0\n")
    result = run_cmd(
        [runtime_bash, repo_dir / "shell/navi-bin/navi", option, value],
        env=isolated_env.env | {"NAVI_FINDER": "skim"},
    )
    assert_ok(result)
    assert result.stdout.split("\0")[:-1] == ["--finder=fzf", option, value]


@pytest.mark.parametrize("option", ["--query", "--filter", "--prompt", "--preview"])
@pytest.mark.parametrize("value", ["--help", "--finder=skim", "", "a 'quoted' value", "a\nb"])
def test_adapter_passes_values_as_single_arguments(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str, option: str, value: str
) -> None:
    real = isolated_env.bin_dir / "real-sk"
    write_executable(real, '#!/bin/sh\nprintf "%s\\0" "$@"\n')
    result = run_cmd(
        [runtime_bash, repo_dir / "shell/navi-bin/fzf", option, value],
        env=isolated_env.env | {"REMOTE_SSH_NAVI_SK_BIN": str(real)},
    )
    assert_ok(result)
    assert result.stdout.split("\0")[:-1] == [f"{option}={value}"]


@pytest.mark.parametrize(
    "args",
    [
        ["--query=--help"],
        ["-q--finder=skim"],
        ["preview", "--finder=skim"],
        ["--", "--finder=skim"],
    ],
)
def test_dispatcher_keeps_attached_values_and_subcommand_arguments(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str, args: list[str]
) -> None:
    write_executable(isolated_env.bin_dir / "navi", '#!/bin/sh\nprintf "%s\\0" "$@"\n')
    write_executable(isolated_env.bin_dir / "sk", "#!/bin/sh\nexit 0\n")
    result = run_cmd(
        [runtime_bash, repo_dir / "shell/navi-bin/navi", *args],
        env=isolated_env.env | {"NAVI_FINDER": "skim"},
    )
    assert_ok(result)
    assert result.stdout.split("\0")[:-1] == ["--finder=fzf", *args]


def test_navi_picker_isolates_global_skim_settings(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str
) -> None:
    real = isolated_env.bin_dir / "real-sk"
    write_executable(
        real,
        '#!/bin/sh\nfor arg do printf "%s\\0" "$arg"; done\nprintf "ENV=%s\\0FILE=%s\\0" "$SKIM_DEFAULT_OPTIONS" "$SKIM_OPTIONS_FILE"\n',
    )
    marker = isolated_env.home / "must-not-exist"
    options = isolated_env.home / "skim options"
    options.write_text(f"--select-1 --print-query --header '$(touch {marker})'\n")
    result = run_cmd(
        [runtime_bash, repo_dir / "shell/navi-bin/fzf", "--no-select-1", "--prompt", "navi> "],
        env=isolated_env.env
        | {
            "REMOTE_SSH_NAVI_SK_BIN": str(real),
            "SKIM_DEFAULT_OPTIONS": f"--filter=x --header '$(touch {marker})'",
            "SKIM_OPTIONS_FILE": str(options),
        },
    )
    assert_ok(result)
    assert result.stdout.split("\0")[:-1] == [
        "--prompt=navi> ",
        "ENV=--height=40% --reverse --border",
        "FILE=",
    ]
    assert not marker.exists()
