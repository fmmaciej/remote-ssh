"""Literal configuration and reload contracts, independent of welcome rendering."""

from __future__ import annotations

from pathlib import Path

import pytest
from conftest import IsolatedEnv, assert_ok, run_cmd


def config_environment(isolated_env: IsolatedEnv, runtime_bash: str) -> dict[str, str]:
    (isolated_env.bin_dir / "bash").symlink_to(runtime_bash)
    return {
        key: value
        for key, value in isolated_env.env.items()
        if not key.startswith("REMOTE_SSH_") and key != "NO_COLOR"
    }


def config_path(isolated_env: IsolatedEnv) -> Path:
    path = Path(isolated_env.env["XDG_CONFIG_HOME"]) / "remote-ssh" / "config"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def test_config_literal_parser_and_compatibility_lookups(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str
) -> None:
    env = config_environment(isolated_env, runtime_bash)
    config = config_path(isolated_env)
    sentinel = isolated_env.home / "executed"
    literal = f"$(touch {sentinel}) `touch {sentinel}` | # \\end=tail"
    config.write_bytes(
        (
            " \t# comment\r\n\t\r\nmalformed\nUNKNOWN_KEY=ignored\n"
            "export REMOTE_SSH_WELCOME=ignored\n"
            "REMOTE_SSH_WELCOME=first\nREMOTE_SSH_WELCOME=\n"
            " \tREMOTE_SSH_WELCOME_BANNER\t = \t0 \r\n"
            "REMOTE_SSH_WELCOME_COLOR='  inner\tspace  '\n"
            "REMOTE_SSH_WELCOME_DEBUG=\"unterminated'\n"
            "REMOTE_SSH_WELCOME_USER='single'\n"
            f"REMOTE_SSH_UPDATE_CHECK='{literal}'\n"
            "REMOTE_SSH_UPDATE_CHECK_INTERVAL=one=two\n"
            'REMOTE_SSH_ENABLE_GIT_SESSION_IDENTITY="double"\n'
            "NO_COLOR=  '  '  "
        ).encode()
    )
    expected = [
        "",
        "0",
        "  inner\tspace  ",
        "\"unterminated'",
        "single",
        literal,
        "one=two",
        "double",
        "  ",
    ]
    script = r"""
        remote_ssh_config_load
        while IFS='|' read -r key _default; do
          printf '%s\0' "${!key}"
          remote_ssh_config_value_is_current_owned "$key"
          remote_ssh_config_file_value_raw "$key"
          remote_ssh_config_file_value "$key"
        done < <(remote_ssh_config_entries)
        [[ -z "${UNKNOWN_KEY+x}" ]]
        if remote_ssh_config_file_value_raw UNKNOWN_KEY; then exit 91; fi
        REMOTE_SSH_CONFIG=off
        remote_ssh_config_file_value_raw REMOTE_SSH_WELCOME
        if remote_ssh_config_file_value REMOTE_SSH_WELCOME; then exit 92; fi
    """
    result = run_cmd(
        [
            runtime_bash,
            "--noprofile",
            "--norc",
            "-c",
            'set -euo pipefail; . "$1/shell/config.lib.sh"; ' + script,
            "_",
            repo_dir,
        ],
        env=env,
    )
    assert_ok(result)
    assert result.stdout == "".join(f"{value}\0{value}\n{value}\n" for value in expected) + "\n"
    assert not sentinel.exists()


@pytest.mark.parametrize(
    "location", ["xdg", "home", "neither", "missing", "empty", "unavailable", "directory"]
)
def test_config_locations_and_unavailable_files(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str, location: str
) -> None:
    env = config_environment(isolated_env, runtime_bash)
    home_config = config_path(isolated_env)
    home_config.write_text("REMOTE_SSH_WELCOME_USER=home\n")
    expected = "absent"
    if location == "xdg":
        xdg = isolated_env.home / "separate-xdg"
        config = xdg / "remote-ssh" / "config"
        config.parent.mkdir(parents=True)
        config.write_text("REMOTE_SSH_WELCOME_USER=xdg\n")
        env["XDG_CONFIG_HOME"] = str(xdg)
        expected = "xdg"
    elif location == "home":
        env["XDG_CONFIG_HOME"] = ""
        expected = "home"
    elif location == "neither":
        env.pop("HOME")
        env.pop("XDG_CONFIG_HOME")
    else:
        home_config.unlink()
        if location == "empty":
            home_config.touch()
        elif location == "unavailable":
            # A symlink loop is unavailable even for a privileged test runner.
            home_config.symlink_to(home_config.name)
        elif location == "directory":
            home_config.mkdir()
    result = run_cmd(
        [
            runtime_bash,
            "-c",
            r"""
            set -euo pipefail
            . "$1/shell/config.lib.sh"
            remote_ssh_config_load
            printf '%s\n' "${REMOTE_SSH_WELCOME_USER-absent}"
            [[ -z "${NO_COLOR+x}" ]]
            if [[ "$2" == absent ]]; then
              if remote_ssh_config_file_value_raw REMOTE_SSH_WELCOME_USER; then exit 93; fi
              [[ -z "${REMOTE_SSH_CONFIG_SOURCE_WELCOME_USER+x}" ]]
              [[ -z "${REMOTE_SSH_CONFIG_LOADED_VALUE_WELCOME_USER+x}" ]]
            fi
        """,
            "_",
            repo_dir,
            expected,
        ],
        env=env,
    )
    assert_ok(result)
    assert result.stdout == expected + "\n"


def test_config_empty_environment_and_incomplete_markers(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str
) -> None:
    env = config_environment(isolated_env, runtime_bash)
    config_path(isolated_env).write_text(
        "REMOTE_SSH_WELCOME=1\nREMOTE_SSH_WELCOME_BANNER=0\n"
        "REMOTE_SSH_WELCOME_COLOR=0\nREMOTE_SSH_WELCOME_DEBUG=0\n"
        "REMOTE_SSH_WELCOME_USER=0\nNO_COLOR=1\n"
    )
    env.update(
        {
            "REMOTE_SSH_WELCOME": "",
            "REMOTE_SSH_WELCOME_BANNER": "manual",
            "REMOTE_SSH_CONFIG_SOURCE_WELCOME_BANNER": "config",
            "REMOTE_SSH_WELCOME_COLOR": "manual",
            "REMOTE_SSH_CONFIG_LOADED_VALUE_WELCOME_COLOR": "manual",
            "REMOTE_SSH_WELCOME_DEBUG": "manual",
            "REMOTE_SSH_CONFIG_SOURCE_WELCOME_DEBUG": "config",
            "REMOTE_SSH_CONFIG_LOADED_VALUE_WELCOME_DEBUG": "other",
            "REMOTE_SSH_WELCOME_USER": "legacy",
            "REMOTE_SSH_CONFIG_SOURCE_REMOTE_SSH_WELCOME_USER": "config",
            "NO_COLOR": "",
            "REMOTE_SSH_CONFIG_SOURCE_NO_COLOR": "config",
            "REMOTE_SSH_CONFIG_LOADED_VALUE_NO_COLOR": "",
        }
    )
    result = run_cmd(
        [
            runtime_bash,
            "-c",
            r"""
            set -euo pipefail
            . "$1/shell/config.lib.sh"
            remote_ssh_config_load
            [[ "$REMOTE_SSH_WELCOME" == '' && "$NO_COLOR" == 1 ]]
            remote_ssh_config_value_is_current_owned NO_COLOR
            [[ -z "${REMOTE_SSH_UPDATE_CHECK+x}" ]]
            for key in REMOTE_SSH_WELCOME REMOTE_SSH_WELCOME_BANNER \
              REMOTE_SSH_WELCOME_COLOR REMOTE_SSH_WELCOME_DEBUG REMOTE_SSH_WELCOME_USER; do
              if remote_ssh_config_value_is_current_owned "$key"; then exit 94; fi
              printf '%s\n' "${!key}"
              source_var="$(remote_ssh_config_source_var "$key")"
              loaded_var="$(remote_ssh_config_loaded_value_var "$key")"
              [[ -z "${!source_var+x}" && -z "${!loaded_var+x}" ]]
            done
            [[ "$REMOTE_SSH_CONFIG_SOURCE_REMOTE_SSH_WELCOME_USER" == config ]]
        """,
            "_",
            repo_dir,
        ],
        env=env,
    )
    assert_ok(result)
    assert result.stdout.splitlines() == ["", "manual", "manual", "manual", "legacy"]


def test_config_reload_lifecycle_and_exported_child(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str
) -> None:
    env = config_environment(isolated_env, runtime_bash)
    config = config_path(isolated_env)
    config.write_text("REMOTE_SSH_WELCOME_USER=0\nNO_COLOR=\n")
    result = run_cmd(
        [
            runtime_bash,
            "-c",
            r"""
            set -euo pipefail
            . "$1/shell/config.lib.sh"
            remote_ssh_config_load
            bash -c '
              set -euo pipefail
              . "$1/shell/config.lib.sh"
              [[ "$REMOTE_SSH_WELCOME_USER" == 0 && "$NO_COLOR" == "" ]]
              remote_ssh_config_value_is_current_owned REMOTE_SSH_WELCOME_USER
              remote_ssh_config_value_is_current_owned NO_COLOR
              printf "REMOTE_SSH_WELCOME_USER=child\nNO_COLOR=\n" >"$2"
              remote_ssh_config_load
              [[ "$REMOTE_SSH_WELCOME_USER" == child ]]
              rm "$2"
              remote_ssh_config_load
              [[ -z "${REMOTE_SSH_WELCOME_USER+x}" && -z "${NO_COLOR+x}" ]]
            ' _ "$1" "$2"
            for cycle in 1 2; do
              printf 'REMOTE_SSH_WELCOME_USER=0\nNO_COLOR=\n' >"$2"
              remote_ssh_config_load
              remote_ssh_config_load
              REMOTE_SSH_WELCOME_USER=0
              remote_ssh_config_value_is_owned REMOTE_SSH_WELCOME_USER
              printf 'REMOTE_SSH_WELCOME_USER=\nNO_COLOR=\n' >"$2"
              remote_ssh_config_load
              [[ "$REMOTE_SSH_WELCOME_USER" == '' ]]
              remote_ssh_config_value_is_owned REMOTE_SSH_WELCOME_USER
              unset REMOTE_SSH_WELCOME_USER
              remote_ssh_config_load
              [[ -n "${REMOTE_SSH_WELCOME_USER+x}" ]]
              REMOTE_SSH_WELCOME_USER=manual
              : >"$2"
              remote_ssh_config_load
              [[ "$REMOTE_SSH_WELCOME_USER" == manual && -z "${NO_COLOR+x}" ]]
              [[ -z "${REMOTE_SSH_CONFIG_SOURCE_WELCOME_USER+x}" ]]
              unset REMOTE_SSH_WELCOME_USER
              printf 'REMOTE_SSH_WELCOME_USER=0\nNO_COLOR=\n' >"$2"
              remote_ssh_config_load
              REMOTE_SSH_WELCOME_USER=''
              REMOTE_SSH_CONFIG=off
              remote_ssh_config_load
              [[ -n "${REMOTE_SSH_WELCOME_USER+x}" && "$REMOTE_SSH_WELCOME_USER" == '' ]]
              [[ -z "${REMOTE_SSH_CONFIG_LOADED_VALUE_WELCOME_USER+x}" ]]
              [[ -z "${NO_COLOR+x}" && -z "${REMOTE_SSH_CONFIG_SOURCE_NO_COLOR+x}" ]]
              unset REMOTE_SSH_WELCOME_USER REMOTE_SSH_CONFIG
              remote_ssh_config_load
              [[ "$REMOTE_SSH_WELCOME_USER" == 0 ]]
              rm "$2"
              remote_ssh_config_load
              [[ -z "${REMOTE_SSH_WELCOME_USER+x}" ]]
              [[ -z "${REMOTE_SSH_CONFIG_LOADED_VALUE_WELCOME_USER+x}" ]]
            done
        """,
            "_",
            repo_dir,
            config,
        ],
        env=env,
    )
    assert_ok(result)


@pytest.mark.parametrize("toggle", ["0", "false", "no", "off", "", "FALSE", "1"])
def test_config_toggle_semantics(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str, toggle: str
) -> None:
    env = config_environment(isolated_env, runtime_bash) | {"REMOTE_SSH_CONFIG": toggle}
    config_path(isolated_env).write_text("REMOTE_SSH_WELCOME_USER=0\n")
    disabled = toggle in {"0", "false", "no", "off"}
    result = run_cmd(
        [
            runtime_bash,
            "-c",
            r"""
            set -euo pipefail
            . "$1/shell/config.lib.sh"
            access_log="$3"
            if [[ "$2" == disabled ]]; then
              # Disabled loading must not resolve or inspect a config path.
              remote_ssh_config_file() { printf 'path accessed\n' >>"$access_log"; return 1; }
            fi
            remote_ssh_config_load
            printf '%s\n' "${REMOTE_SSH_WELCOME_USER-absent}"
        """,
            "_",
            repo_dir,
            "disabled" if disabled else "enabled",
            isolated_env.home / "path-accessed",
        ],
        env=env,
    )
    assert_ok(result)
    assert result.stdout == ("absent\n" if disabled else "0\n")
    assert not (isolated_env.home / "path-accessed").exists()


@pytest.mark.parametrize("scenario", ["fresh", "reload", "disabled"])
@pytest.mark.parametrize("strict", [False, True], ids=["ordinary", "strict"])
def test_config_catalog_failure_status_and_state(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    runtime_bash: str,
    scenario: str,
    strict: bool,
) -> None:
    env = config_environment(isolated_env, runtime_bash)
    config = config_path(isolated_env)
    config.write_text("REMOTE_SSH_WELCOME_USER=old\n")
    version = run_cmd([runtime_bash, "-c", 'printf "%s" "$BASH_VERSINFO"'], env=env)
    assert_ok(version)
    fails_catalog = version.stdout == "3"
    result = run_cmd(
        [
            runtime_bash,
            "--noprofile",
            "--norc",
            "-c",
            r"""
            . "$1/shell/config.lib.sh"
            if [[ "$3" != fresh ]]; then
              remote_ssh_config_load
            fi
            printf 'REMOTE_SSH_WELCOME_USER=new\n' >"$2"
            if [[ "$3" == disabled ]]; then
              REMOTE_SSH_CONFIG=off
            fi
            trap 'status=$?; printf "exit=%s value=%s source=%s loaded=%s\n" \
              "$status" "${REMOTE_SSH_WELCOME_USER-unset}" \
              "${REMOTE_SSH_CONFIG_SOURCE_WELCOME_USER-unset}" \
              "${REMOTE_SSH_CONFIG_LOADED_VALUE_WELCOME_USER-unset}"' EXIT
            set -o posix
            if [[ "$4" == strict ]]; then
              set -euo pipefail
            fi
            # Standalone call: do not suppress errexit with if/! or an AND/OR list.
            remote_ssh_config_load
            load_status=$?
            printf 'load=%s\nreached\n' "$load_status"
            """,
            "_",
            repo_dir,
            config,
            scenario,
            "strict" if strict else "ordinary",
        ],
        env=env,
    )
    failed_load = fails_catalog and scenario != "disabled"
    expected_status = int(failed_load and strict)
    if fails_catalog:
        expected_state = (
            "value=unset source=unset loaded=unset"
            if scenario == "fresh"
            else "value=old source=config loaded=old"
        )
    else:
        expected_state = (
            "value=unset source=unset loaded=unset"
            if scenario == "disabled"
            else "value=new source=config loaded=new"
        )
    expected_lines = [] if expected_status else [f"load={int(failed_load)}", "reached"]
    expected_lines.append(f"exit={expected_status} {expected_state}")
    assert (result.returncode, result.stdout.splitlines()) == (expected_status, expected_lines), (
        result.stderr
    )


def test_config_raw_lookup_stops_after_catalog_initialization_failure(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str
) -> None:
    env = config_environment(isolated_env, runtime_bash)
    config = config_path(isolated_env)
    config.write_text("REMOTE_SSH_WELCOME_USER=new\n")
    access_log = isolated_env.home / "path-accessed"
    result = run_cmd(
        [
            runtime_bash,
            "--noprofile",
            "--norc",
            "-c",
            r"""
            . "$1/shell/config.lib.sh"
            config_file="$2"
            access_log="$3"
            remote_ssh_config_file() {
              printf 'resolved\n' >>"$access_log"
              printf '%s\n' "$config_file"
            }
            set -o posix
            remote_ssh_config_file_value_raw REMOTE_SSH_WELCOME_USER
            lookup_status=$?
            printf 'lookup=%s bash=%s\n' "$lookup_status" "$BASH_VERSINFO"
            """,
            "_",
            repo_dir,
            config,
            access_log,
        ],
        env=env,
    )
    assert_ok(result)
    if result.stdout == "lookup=1 bash=3\n":
        assert not access_log.exists()
    else:
        assert result.stdout == "new\nlookup=0 bash=5\n"
        assert access_log.read_text() == "resolved\n"
