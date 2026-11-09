"""Offline native gate for Flyline ownership and exact activation rollback.

Requires explicitly supplied local R5 artifacts and Atuin. All installs, history,
configuration and late hooks belong to disposable HOME/checkouts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import managed

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1] / "docs/interactive-tools-performance-evidence")
)
from benchmark import Session, environment  # noqa: E402

READY = b"\x1eOWNERSHIP_READY\x1f"
PROMPT = b"OWNERSHIP> "
SHA256 = "ac989a041026f49df1d3b544290ee3e67b497a0d3f82fe4785cd3c106e431d57"

INSTRUMENT = r"""
source "$CHECKOUT/shell/rc.d/29-flyline.sh"
original="$(declare -f remote_flyline_library)"
eval "${original/remote_flyline_library/__ownership_library}"
remote_flyline_library() {
  printf '\036RESOLVER\037\n' >&2
  __ownership_library
}
function builtin() {
  case "$1:$2" in
    enable:-f) printf '\036MANAGED_LOAD\037\n' >&2 ;;
    enable:-d) printf '\036MANAGED_UNLOAD\037\n' >&2 ;;
    flyline:*) printf '\036MANAGED_SETTING\037\n' >&2 ;;
  esac
  command builtin "$@"
}
"""

SNAPSHOT = r"""
printf '\036STATE:%s:%s:%s\037\n' "$REMOTE_SSH_FLYLINE_STATE" "$REMOTE_SSH_FLYLINE_REASON" "$REMOTE_SSH_HISTORY_BACKEND"
printf '\036BUILTINS_BEGIN\037\n'
command builtin enable -a
printf '\036BUILTINS_END\037\n'
"""


def shell_case(name: str, variable: str = "", state: str = "", failure: str = "") -> str:
    setup = ""
    checks = ""
    if name == "external-disabled":
        setup = r"""
builtin enable -f "$LIBRARY" flyline || exit 61
builtin enable -n flyline || exit 62
"""
    elif name.startswith("rollback-"):
        setup = r"""
unset FLYLINE_LOAD_DIR FLYLINE_VERSION
case "$VARIABLE_STATE" in
  exported-unset) export "$VARIABLE" ;;
  empty|exported-empty) printf -v "$VARIABLE" '%s' '' ;;
  value|exported-value) printf -v "$VARIABLE" '%s' ' old "quoted" value \ $ * ' ;;
esac
case "$VARIABLE_STATE" in exported-empty|exported-value) export "$VARIABLE";; esac
before="$(declare -p "$VARIABLE" 2>/dev/null)"; before_exists=$?
before_env="$(env | grep '^FLYLINE_' || :)"
"""
        if failure == "load":
            setup += 'remote_flyline_library() { printf "%s" "$HOME/absent-library.dylib"; }\n'
        else:
            setup += r"""
remote_flyline_settings() {
  FLYLINE_LOAD_DIR=changed-dir; export FLYLINE_LOAD_DIR
  FLYLINE_VERSION=changed-version; export FLYLINE_VERSION
  return 1
}
"""
        checks = r"""
after="$(declare -p "$VARIABLE" 2>/dev/null)"; after_exists=$?
after_env="$(env | grep '^FLYLINE_' || :)"
printf '\036BEFORE:%s:%s\037\n' "$before_exists" "$before"
printf '\036AFTER:%s:%s\037\n' "$after_exists" "$after"
[[ "$before_exists:$before" == "$after_exists:$after" && "$before_env" == "$after_env" ]]
attribute_status=$?
printf '\036ATTRIBUTES:%s\037\n' "$attribute_status"
"""
    elif name.startswith("late-"):
        # Source this at top level, like a user's existing preexec library.
        # Sourcing its declare -a statements inside remote_source_file would
        # make callback arrays local to that hook instead of external state.
        setup = 'source "$CHECKOUT/tools/vendors/bash-preexec.sh"\n'
        checks = r"""
printf '\036EXTERNAL_MARKER:%s\037\n' "${__atuin_initialized:-missing}"
[[ "$(bind -m vi-insert -s)" == "$(< "$HOME/external-bindings")" &&
   "$(declare -p preexec_functions precmd_functions)" == "$(< "$HOME/external-callbacks")" &&
   "${__atuin_initialized:-}" == true ]]
printf '\036EXTERNAL_INTACT:%s\037\n' "$?"
"""
    # Instrument only our managed runtime operations. External initial load is
    # deliberately performed before installing the instrumentation wrapper.
    if name == "external-disabled":
        script = setup + INSTRUMENT
    else:
        script = INSTRUMENT + setup
    return (
        script
        + 'source "$CHECKOUT/shell/rc.sh"\n'
        + SNAPSHOT
        + checks
        + r"""
capture() { printf '\036ARG:%s\037\n' "$*"; }
PS1='OWNERSHIP> '
printf '\036OWNERSHIP_READY\037\n'
"""
    )


def run_case(args: argparse.Namespace, spec: dict[str, str]) -> dict[str, Any]:
    name = spec["case"]
    result: dict[str, Any] = {"case": name, "expected": spec}
    with tempfile.TemporaryDirectory(prefix="flyline-ownership-") as directory:
        home = Path(directory)
        for sub in ("config", "data", "state", "cache", "bin"):
            (home / sub).mkdir()
        (home / "bin/bash").symlink_to(args.bash.resolve())
        positive_atuin = name in ("managed-atuin", "managed-nobind")
        if positive_atuin:
            (home / "bin/atuin").symlink_to(args.atuin.resolve())
        env = environment(home, home / "bin")
        env.update(
            REMOTE_SSH_ENABLE_ATUIN="1" if positive_atuin else spec.get("toggle", "0"),
            VARIABLE=spec.get("variable", ""),
            VARIABLE_STATE=spec.get("state", ""),
            FLYLINE_VERSION="stale-inherited",
            FLYLINE_LOAD_DIR="/stale-inherited",
        )
        if name == "managed-nobind":
            env["ATUIN_NOBIND"] = "1"
        checkout = managed.install(args.repo, args.bash, args.library, home, env)
        env.update(CHECKOUT=str(checkout), LIBRARY=str(args.library.resolve()))
        if name.startswith("late-"):
            hook = spec["hook"]
            basename = (
                platform.system().lower()
                if hook == "os"
                else subprocess.check_output(["hostname", "-s"], text=True).strip()
            )
            path = checkout / "shell/rc.d" / f"{hook}.d" / f"{basename}.sh"
            path.parent.mkdir(exist_ok=True)
            path.write_text(
                f'ln -s {shlex.quote(str(args.atuin.resolve()))} "$HOME/bin/atuin"\n'
                'eval "$(atuin init bash --disable-up-arrow --disable-ctrl-r --disable-ai)"\n'
                "atuin-bind -m vi-insert '\\C-r' atuin-search-viins\n"
                'bind -m vi-insert -s > "$HOME/external-bindings"\n'
                'declare -p preexec_functions precmd_functions > "$HOME/external-callbacks"\n'
            )
        rc = home / "rc.sh"
        rc.write_text(
            shell_case(
                name, spec.get("variable", ""), spec.get("state", ""), spec.get("failure", "")
            )
        )
        session = Session([str(args.bash), "--noprofile", "--rcfile", str(rc), "-i"], env, home)
        try:
            session.expect(READY, raw=True)
            session.expect(PROMPT)
            transcript = bytes(session.transcript)
            states = re.findall(rb"\x1eSTATE:([^\x1f]*)\x1f", transcript)
            actual = states[-1].decode() if states else "[missing state]"
            result["actual"] = actual
            result["passed"] = actual == spec["expected_state"]
            if name.startswith("late-") or name == "external-disabled":
                result["managed_calls"] = [
                    token
                    for token in ("RESOLVER", "MANAGED_LOAD", "MANAGED_SETTING", "MANAGED_UNLOAD")
                    if b"\x1e" + token.encode() + b"\x1f" in transcript
                ]
                result["passed"] &= not result["managed_calls"]
                if name.startswith("late-"):
                    result["external_intact"] = b"\x1eEXTERNAL_INTACT:0\x1f" in transcript
                    result["passed"] &= result["external_intact"]
                else:
                    block = transcript.split(b"\x1eBUILTINS_BEGIN\x1f", 1)[1].split(
                        b"\x1eBUILTINS_END\x1f", 1
                    )[0]
                    result["disabled_entry_preserved"] = (
                        "enable -n flyline" in block.decode().splitlines()
                    )
                    result["duplicate_load_warning"] = (
                        b"dynamic builtin already loaded" in transcript
                    )
                    result["passed"] &= (
                        result["disabled_entry_preserved"] and not result["duplicate_load_warning"]
                    )
            elif name.startswith("rollback-"):
                result["attributes_preserved"] = b"\x1eATTRIBUTES:0\x1f" in transcript
                result["passed"] &= result["attributes_preserved"]
                if spec["failure"] == "settings":
                    start = len(session.transcript)
                    session.send(b"capture ac")
                    session.quiet(0.08)
                    session.send(b"\x1b")
                    session.quiet(0.15)
                    session.send(b"hrbA\r")
                    session.expect(b"\x1eARG:bc\x1f", raw=True)
                    session.expect(PROMPT)
                    found = re.findall(rb"\x1eARG:([^\x1f]*)\x1f", session.transcript[start:])
                    result["readline_argument"] = found[-1].decode() if found else "[missing]"
                    result["passed"] &= result["readline_argument"] == "bc"
            else:
                result["actual_managed_load"] = b"\x1eMANAGED_LOAD\x1f" in transcript
                result["actual_settings"] = b"\x1eMANAGED_SETTING\x1f" in transcript
                result["passed"] &= result["actual_managed_load"] and result["actual_settings"]
        except (RuntimeError, OSError, IndexError) as exc:
            result.update(passed=False, error=str(exc)[:1500])
        finally:
            result["resources"] = session.close()
            (args.output / f"{name}.txt").write_text(
                json.dumps(session.transcript.decode(errors="replace")) + "\n"
            )
            (args.output / f"{name}-install.txt").write_text((home / "install.log").read_text())
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repo", "bash", "library", "atuin", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    for name in ("repo", "bash", "library", "atuin", "output"):
        setattr(args, name, getattr(args, name).resolve())
    if hashlib.sha256(args.library.read_bytes()).hexdigest() != SHA256:
        parser.error("This repair gate requires the unchanged qualified R5 library")
    args.output.mkdir(parents=True, exist_ok=False)
    cases: list[dict[str, str]] = [
        {
            "case": f"late-{hook}-{toggle}",
            "hook": hook,
            "toggle": toggle,
            "expected_state": "skipped:external:bash",
        }
        for hook in ("os", "host")
        for toggle in ("0", "1")
    ]
    cases += [
        {"case": "external-disabled", "expected_state": "skipped:external:bash"},
        {"case": "managed-bash", "expected_state": "active:managed:bash"},
        {"case": "managed-atuin", "expected_state": "active:managed:atuin"},
        {"case": "managed-nobind", "expected_state": "active:managed:atuin"},
    ]
    cases += [
        {
            "case": f"rollback-{variable}-{state}-{failure}",
            "variable": variable,
            "state": state,
            "failure": failure,
            "expected_state": f"failed:{failure}:bash",
        }
        for variable in ("FLYLINE_LOAD_DIR", "FLYLINE_VERSION")
        for state in (
            "unset",
            "exported-unset",
            "empty",
            "exported-empty",
            "value",
            "exported-value",
        )
        for failure in ("load", "settings")
    ]
    results = []
    for spec in cases:
        try:
            result = run_case(args, spec)
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
            result = {"case": spec["case"], "expected": spec, "passed": False, "error": str(exc)}
        results.append(result)
        print(json.dumps(result), flush=True)
    report = {
        "library_sha256": SHA256,
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "bash_version": subprocess.check_output(
            [str(args.bash), "--version"], text=True
        ).splitlines()[0],
        "atuin_version": subprocess.check_output([str(args.atuin), "--version"], text=True).strip(),
        "results": results,
        "passed": all(r["passed"] for r in results),
    }
    (args.output / "results.json").write_text(json.dumps(report, indent=2) + "\n")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
