"""Offline R5 effective-settings equivalence and combined-call rollback gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

import managed

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1] / "docs/interactive-tools-performance-evidence")
)
from benchmark import Session, environment  # noqa: E402

READY = b"\x1eSETTINGS_READY\x1f"
PROMPT = b"SETTINGS> "
LIBRARY_SHA = "ac989a041026f49df1d3b544290ee3e67b497a0d3f82fe4785cd3c106e431d57"
MANDATORY = {
    "run_tutorial": "false",
    "show_animations": "false",
    "enable_easter_eggs": "false",
    "enable_extended_key_codes": "false",
    "send_shell_integration_codes": "None",
    "mouse_mode": "Disabled",
    "cursor.backend": "Terminal",
    "auto_suggest": "false",
    "auto_suggest_inline": "false",
    "flycomp.enabled": "false",
    "history.backend": "bash",
    "vim_mode": "true",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_settings(text: str) -> dict[str, str]:
    plain = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", text)
    result = {}
    for block in plain.split("\n\n"):
        lines = block.splitlines()
        if not lines:
            continue
        values = []
        capturing = False
        for line in lines[1:]:
            if line.startswith("  Default:"):
                break
            if line.startswith("  Current:"):
                capturing = True
                value = line.removeprefix("  Current:")
                if value.startswith(" "):
                    values.append(value[1:])
            elif capturing:
                values.append(line.removeprefix("    "))
        if capturing:
            result[lines[0]] = "\n".join(values)
    return result


def fixture(args: argparse.Namespace, home: Path, profile: str) -> tuple[Path, dict[str, str]]:
    for sub in ("config", "data", "state", "cache", "bin"):
        (home / sub).mkdir()
    (home / "bin/bash").symlink_to(args.bash)
    if profile in ("atuin", "nobind"):
        (home / "bin/atuin").symlink_to(args.atuin)
    if profile == "skim":
        (home / "bin/sk").symlink_to(args.skim)
    env = environment(home, home / "bin")
    env.update(REMOTE_SSH_ENABLE_ATUIN="1" if profile in ("atuin", "nobind") else "0", NO_COLOR="1")
    if profile == "nobind":
        env["ATUIN_NOBIND"] = "1"
    checkout = managed.install(args.repo, args.bash, args.library, home, env)
    env["CHECKOUT"] = str(checkout)
    return checkout, env


def native_snapshot(
    args: argparse.Namespace,
    checkout: Path,
    home: Path,
    env: dict[str, str],
    variant: str,
    profile: str,
) -> dict[str, Any]:
    rc = home / "rc.sh"
    env = env | {"VARIANT": variant}
    rc.write_text(r"""
source "$CHECKOUT/shell/rc.sh"
printf '\036STATE:%s:%s:%s\037\n' "$REMOTE_SSH_FLYLINE_STATE" "$REMOTE_SSH_FLYLINE_REASON" "$REMOTE_SSH_HISTORY_BACKEND"
builtin flyline settings --all > "$HOME/$VARIANT-settings.txt"
snapshot_status=$?
builtin flyline key list Ctrl+r > "$HOME/$VARIANT-keys.txt"
printf '\036SNAPSHOT:%s:%s\037\n' "$snapshot_status" "$?"
PS1='SETTINGS> '
printf '\036SETTINGS_READY\037\n'
""")
    session = Session([str(args.bash), "--noprofile", "--rcfile", str(rc), "-i"], env, home)
    result: dict[str, Any] = {"profile": profile, "variant": variant}
    try:
        session.expect(READY, raw=True)
        session.expect(PROMPT)
        state = re.findall(rb"\x1eSTATE:([^\x1f]*)\x1f", session.transcript)
        result["actual_state"] = state[-1].decode() if state else "[missing]"
        result["expected_state"] = (
            f"active:managed:{'atuin' if profile in ('atuin', 'nobind') else 'bash'}"
        )
        settings = (home / f"{variant}-settings.txt").read_text()
        keys = (home / f"{variant}-keys.txt").read_text()
        fields = parse_settings(settings)
        result["required_actual"] = {name: fields.get(name) for name in MANDATORY}
        result["mandatory_settings"] = all(
            fields.get(name) == value for name, value in MANDATORY.items()
        )
        bindings = json.loads(fields.get("user_keybindings", "null"))
        bound = profile in ("atuin", "skim")
        if bound:
            callbacks = (
                ("__remote_ssh_flyline_history_vi", "__remote_ssh_flyline_history_emacs")
                if profile == "atuin"
                else ("__skim_history", "__skim_history")
            )
            result["bindings_valid"] = (
                isinstance(bindings, list)
                and len(bindings) == 2
                and all(
                    callback in str(binding)
                    for callback, binding in zip(callbacks, bindings, strict=True)
                )
            )
        else:
            result["bindings_valid"] = bindings == []
        result["user_keybindings"] = bindings
        result["passed"] = (
            result["actual_state"] == result["expected_state"]
            and b"\x1eSNAPSHOT:0:0\x1f" in session.transcript
            and result["mandatory_settings"]
            and result["bindings_valid"]
        )
        for kind, content in (("settings", settings), ("keys", keys)):
            (args.output / f"{profile}-{variant}-{kind}.txt").write_text(content)
    except (RuntimeError, OSError, ValueError, IndexError) as exc:
        result.update(passed=False, error=str(exc)[:1800])
    finally:
        result["resources"] = session.close()
        (args.output / f"{profile}-{variant}-transcript.txt").write_text(
            json.dumps(session.transcript.decode(errors="replace")) + "\n"
        )
    return result


def failure_case(args: argparse.Namespace, failure: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="flyline-combined-failure-") as directory:
        home = Path(directory)
        checkout, env = fixture(args, home, "atuin")
        env["FAILURE"] = failure
        rc = home / "rc.sh"
        rc.write_text(r"""
FLYLINE_LOAD_DIR=' old "directory" '; export -n FLYLINE_LOAD_DIR
unset FLYLINE_VERSION; export FLYLINE_VERSION
before_dir="$(declare -p FLYLINE_LOAD_DIR)"
before_version="$(declare -p FLYLINE_VERSION)"
function builtin() {
  local -a argv=("$@")
  local last=$(( $# - 1 ))
  if [[ "$1:$2" == flyline:--show-animations && "$FAILURE" == global-cursor && "$*" == *'set-cursor --backend terminal'* ]]; then
    argv[last]=not-a-valid-backend
  elif [[ "$1:$2:${3:-}:${5:-}" == flyline:key:--vim-mode:bind && "$FAILURE" == vim-bind ]]; then
    argv[last]='vimInsertMode=notARealAction'
  fi
  command builtin "${argv[@]}"
}
source "$CHECKOUT/shell/rc.sh"
printf '\036STATE:%s:%s:%s\037\n' "$REMOTE_SSH_FLYLINE_STATE" "$REMOTE_SSH_FLYLINE_REASON" "$REMOTE_SSH_HISTORY_BACKEND"
[[ "$(declare -p FLYLINE_LOAD_DIR)" == "$before_dir" && "$(declare -p FLYLINE_VERSION)" == "$before_version" ]]
printf '\036ATTRIBUTES:%s\037\n' "$?"
if command builtin type -t flyline >/dev/null 2>&1; then absent=1; else absent=0; fi
printf '\036UNLOADED:%s\037\n' "$absent"
capture() { printf '\036ARG:%s\037\n' "$*"; }
PS1='SETTINGS> '
printf '\036SETTINGS_READY\037\n'
""")
        session = Session([str(args.bash), "--noprofile", "--rcfile", str(rc), "-i"], env, home)
        result: dict[str, Any] = {"failure": failure, "expected_state": "failed:settings:atuin"}
        try:
            session.expect(READY, raw=True)
            session.expect(PROMPT)
            state = re.findall(rb"\x1eSTATE:([^\x1f]*)\x1f", session.transcript)
            result["actual_state"] = state[-1].decode() if state else "[missing]"
            result["attributes_preserved"] = b"\x1eATTRIBUTES:0\x1f" in session.transcript
            result["unloaded"] = b"\x1eUNLOADED:0\x1f" in session.transcript
            result["fallback_warning"] = (
                b"Flyline initialization failed; using Readline" in session.transcript
            )
            session.send(b"capture ac")
            session.quiet(0.08)
            early = b"\x1eARG:" in session.transcript
            session.send(b"\x1b")
            session.quiet(0.15)
            session.send(b"hrbA\r")
            session.expect(b"\x1eARG:bc\x1f", raw=True)
            session.expect(PROMPT)
            result["readline_argument"] = "bc"
            result["early_execution"] = early
            result["passed"] = (
                result["actual_state"] == result["expected_state"]
                and result["attributes_preserved"]
                and result["unloaded"]
                and result["fallback_warning"]
                and not early
            )
        except (RuntimeError, OSError, IndexError) as exc:
            result.update(passed=False, error=str(exc)[:1800])
        finally:
            result["resources"] = session.close()
            (args.output / f"failure-{failure}-transcript.txt").write_text(
                json.dumps(session.transcript.decode(errors="replace")) + "\n"
            )
        return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repo", "bash", "library", "atuin", "skim", "before", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    for name in ("repo", "bash", "library", "atuin", "skim", "before", "output"):
        setattr(args, name, getattr(args, name).resolve())
    if sha(args.library) != LIBRARY_SHA:
        parser.error("Requires unchanged qualified R5 library")
    args.output.mkdir(parents=True, exist_ok=False)
    before = args.before.read_bytes()
    current = (args.repo / "shell/rc.d/29-flyline.sh").read_bytes()
    profiles = []
    for profile in ("atuin", "skim", "nobind", "no-widget"):
        with tempfile.TemporaryDirectory(prefix=f"flyline-settings-{profile}-") as directory:
            home = Path(directory)
            checkout, env = fixture(args, home, profile)
            snapshots = []
            for variant, source in (("before", before), ("current", current)):
                (checkout / "shell/rc.d/29-flyline.sh").write_bytes(source)
                snapshots.append(native_snapshot(args, checkout, home, env, variant, profile))
            settings_equal = (
                all((home / f"{v}-settings.txt").is_file() for v in ("before", "current"))
                and (home / "before-settings.txt").read_bytes()
                == (home / "current-settings.txt").read_bytes()
            )
            keys_equal = (
                all((home / f"{v}-keys.txt").is_file() for v in ("before", "current"))
                and (home / "before-keys.txt").read_bytes()
                == (home / "current-keys.txt").read_bytes()
            )
            result = {
                "profile": profile,
                "snapshots": snapshots,
                "all_settings_byte_equal": settings_equal,
                "key_list_byte_equal": keys_equal,
                "passed": all(s["passed"] for s in snapshots) and settings_equal and keys_equal,
            }
            profiles.append(result)
            print(json.dumps(result), flush=True)
    failures = []
    for failure in ("global-cursor", "vim-bind"):
        result = failure_case(args, failure)
        failures.append(result)
        print(json.dumps(result), flush=True)
    report = {
        "library_sha256": LIBRARY_SHA,
        "script_sha256": sha(Path(__file__)),
        "before_module_sha256": hashlib.sha256(before).hexdigest(),
        "current_module_sha256": hashlib.sha256(current).hexdigest(),
        "mandatory_expected": MANDATORY,
        "profiles": profiles,
        "failures": failures,
        "passed": all(p["passed"] for p in profiles) and all(f["passed"] for f in failures),
    }
    (args.output / "results.json").write_text(json.dumps(report, indent=2) + "\n")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
