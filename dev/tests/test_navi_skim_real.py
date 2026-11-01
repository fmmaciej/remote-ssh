"""Offline acceptance tests; explicitly supply both pinned executables to run."""

from __future__ import annotations

import os
import re
import shlex
import subprocess
import time
from pathlib import Path

import pytest
from conftest import IsolatedEnv, assert_ok
from pty_shell import PtyShell


@pytest.fixture(scope="module")
def picker_binaries(request: pytest.FixtureRequest, repo_dir: Path) -> dict[str, Path]:
    supplied = {
        name: request.config.getoption(option)
        for name, option in (("navi", "--navi-bin"), ("sk", "--skim-bin"))
    }
    if not any(supplied.values()):
        pytest.skip("real picker tests require --navi-bin and --skim-bin (no downloads)")
    binaries = {}
    for name, value in supplied.items():
        if not value:
            pytest.fail("supply both --navi-bin and --skim-bin; no PATH fallback is used")
        path = Path(value)
        if not path.is_absolute() or not path.is_file() or not os.access(path, os.X_OK):
            pytest.fail(f"{name}: expected an absolute path to an executable, got {value!r}")
        definition = (repo_dir / "tools" / "defs" / f"{name}.sh").read_text()
        version = re.search(r'^VERSION="([^"]+)"$', definition, re.MULTILINE)
        assert version is not None
        result = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=5)
        assert_ok(result)
        assert result.stdout.strip() == f"{name} {version[1]}", result.stdout
        binaries[name] = path.resolve()
    return binaries


@pytest.fixture
def picker_env(
    isolated_env: IsolatedEnv, picker_binaries: dict[str, Path], repo_dir: Path
) -> dict[str, str]:
    env = {
        key: value
        for key, value in isolated_env.env.items()
        if not key.startswith(("NAVI_", "SKIM_", "FZF_", "REMOTE_SSH_NAVI_"))
        and key != "value__query"
    }
    for name, binary in picker_binaries.items():
        (isolated_env.bin_dir / name).symlink_to(binary)
    options = isolated_env.home / "global skim options"
    options.write_text("--print-query --filter=global-file-must-not-affect-navi\n")
    env.update(
        TERM="xterm-256color",
        SHELL="/bin/bash",
        NAVI_FINDER="skim",
        NAVI_PATH=str(isolated_env.home / "cheats"),
        NAVI_FZF_OVERRIDES="--no-select-1 --prompt=SNIPPET>",
        NAVI_FZF_OVERRIDES_VAR="--no-select-1 --prompt=VALUE>",
        REMOTE_SHELL_DIR=str(repo_dir / "shell"),
        REMOTE_DOTS_DIR=str(repo_dir / "dots"),
        SKIM_DEFAULT_OPTIONS="--select-1 --filter=global-env-must-not-affect-navi",
        SKIM_OPTIONS_FILE=str(options),
    )
    return env


def run_picker(
    bash: str,
    env: dict[str, str],
    repo_dir: Path,
    command: str,
    interactions: list[tuple[bytes, bytes]],
    result_path: Path,
    *,
    status: int = 0,
) -> str:
    setup = "; ".join(
        f". {shlex.quote(str(repo_dir / path))}"
        for path in ("lib/guards.sh", "lib/helpers.sh", "shell/rc.d/24-navi.sh")
    )
    with PtyShell(bash, env, terminal_size=(35, 120), respond_to_cursor=True) as terminal:
        # Unlike the echoed input, only execution emits these control bytes.
        script = f"{setup}; {command} > {shlex.quote(str(result_path))}"
        os.write(terminal.fd, (script + "; printf '\\036picker:%s\\037' \"$?\"\n").encode())
        for visible, keys in interactions:
            terminal.until(
                lambda visible=visible: (
                    visible in terminal.output or b"\x1epicker:" in terminal.output
                )
            )
            assert visible in terminal.output, terminal.output.decode(errors="replace")
            terminal.output.clear()
            # Allow the picker to finish drawing before Readline sends the keys.
            time.sleep(0.1)
            os.write(terminal.fd, keys)
        terminal.until(lambda: b"\x1epicker:" in terminal.output and b"\x1f" in terminal.output)
        match = re.search(rb"\x1epicker:(\d+)\x1f", terminal.output)
        assert match is not None
        assert int(match[1]) == status, terminal.output.decode(errors="replace")
    return result_path.read_text()


@pytest.mark.parametrize(
    "mode,value,keys",
    [
        ("free", "space 'quoted' value", b"space 'quoted' value\r"),
        ("list", "beta", b"bet\r"),
        ("tab", "bet", b"bet\t"),
        ("custom", "space 'quoted' value", b"space 'quoted' value\r"),
        ("single", "alpha", b""),
        ("cancel-main", "", b""),
        ("cancel-var", "", b"\x1b"),
    ],
    ids=["free", "list", "tab", "custom", "single", "cancel-main", "cancel-var"],
)
def test_real_navi_print_and_parameter_input(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    runtime_bash: str,
    picker_env: dict[str, str],
    mode: str,
    value: str,
    keys: bytes,
) -> None:
    cheats = Path(picker_env["NAVI_PATH"])
    cheats.mkdir()
    text = "% audit\n# audit case\nprintf '%s\\n' \"<value>\"\n"
    if mode != "free":
        options = "alpha" if mode == "single" else "alpha beta"
        text += f"\n$ value: printf '%s\\n' {options}\n"
    (cheats / "audit.cheat").write_text(text)
    interactions = [(b"SNIPPET>", b"\x1b" if mode == "cancel-main" else b"\r")]
    if mode == "single":
        picker_env.update(value__query="alpha", NAVI_FZF_OVERRIDES_VAR="--prompt=VALUE>")
    elif mode != "cancel-main":
        interactions.append((b"VALUE>", keys))
    cancelled = mode.startswith("cancel")
    printed = run_picker(
        runtime_bash,
        picker_env,
        repo_dir,
        'navi --print --query "audit case"',
        interactions,
        isolated_env.home / "result",
        status=130 if cancelled else 0,
    )
    if cancelled:
        assert printed == ""
    else:
        assert shlex.split(printed) == ["printf", "%s\\n", value]
        executed = subprocess.run(
            [runtime_bash, "--noprofile", "--norc", "-c", printed],
            env=picker_env,
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert_ok(executed)
        assert executed.stdout == value + "\n"


@pytest.mark.parametrize(
    "keys,value,status",
    [
        (b"\r", "alpha", 0),
        (b"custom 'quoted' value\r", "custom 'quoted' value", 0),
        (b"a\t", "a", 0),
        (b"\x1b", None, 130),
    ],
    ids=["enter", "custom", "tab", "cancel"],
)
def test_real_navi_parameter_input_with_default_select_one(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    runtime_bash: str,
    picker_env: dict[str, str],
    keys: bytes,
    value: str | None,
    status: int,
) -> None:
    cheats = Path(picker_env["NAVI_PATH"])
    cheats.mkdir()
    (cheats / "audit.cheat").write_text(
        "% audit\n# audit case\nprintf '%s\\n' \"<value>\"\n\n$ value: printf '%s\\n' alpha beta\n"
    )
    # Keep navi's default --select-1. Two candidates keep the picker interactive
    # so Enter/Tab/custom input exercise its expected-key normalization path.
    picker_env["NAVI_FZF_OVERRIDES_VAR"] = "--prompt=VALUE>"
    printed = run_picker(
        runtime_bash,
        picker_env,
        repo_dir,
        "navi --print --best-match --query 'audit case'",
        [(b"VALUE>", keys)],
        isolated_env.home / "result",
        status=status,
    )
    if value is None:
        assert printed == ""
    else:
        assert shlex.split(printed) == ["printf", "%s\\n", value]


def test_real_navi_nested_execution_keeps_parameter_protocol(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str, picker_env: dict[str, str]
) -> None:
    outer = Path(picker_env["NAVI_PATH"])
    outer.mkdir()
    inner = isolated_env.home / "inner cheats"
    inner.mkdir()
    (inner / "inner.cheat").write_text("% audit\n# inner case\nprintf '%s\\n' \"<value>\"\n")
    (outer / "outer.cheat").write_text(
        "% audit\n# outer case\nnavi --path "
        + shlex.quote(str(inner))
        + " --print --best-match --query 'inner case'\n"
    )
    printed = run_picker(
        runtime_bash,
        picker_env,
        repo_dir,
        "navi --best-match --query 'outer case'",
        [(b"VALUE>", b"nested 'quoted' value\r")],
        isolated_env.home / "result",
    )
    assert shlex.split(printed) == ["printf", "%s\\n", "nested 'quoted' value"]
