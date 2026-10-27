#!/usr/bin/env python3
"""Independent behavior probes; no runtime/test edits and no timing claims.

Run from any directory with --repo /path/to/remote-ssh --phase PHASE.
Snapshots start from the pinned commit and differ ONLY in parse/load/markers.
Each (version, shell, strict mode, case) gets a fresh process and HOME. The
binary stdout protocol records all nine settings, both ownership markers,
ownership predicates, exported declarations, raw/gated lookup statuses, and
snapshot-variable leakage. JSON retains full stdout/stderr in base64.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import tarfile
import tempfile


BASE = "c41cbc4820594de95e2035cfc5ab896e16db9e70"
CHANGED = [f"shell/config/{name}.sh" for name in ("parse", "load", "markers")]
BASHES = ["/bin/bash", "/opt/homebrew/bin/bash"]
KEYS = [
    "REMOTE_SSH_WELCOME", "REMOTE_SSH_WELCOME_BANNER", "REMOTE_SSH_WELCOME_COLOR",
    "REMOTE_SSH_WELCOME_DEBUG", "REMOTE_SSH_WELCOME_USER", "REMOTE_SSH_UPDATE_CHECK",
    "REMOTE_SSH_UPDATE_CHECK_INTERVAL", "REMOTE_SSH_ENABLE_GIT_SESSION_IDENTITY", "NO_COLOR",
]
HEADER = r'''
probe_root="$1"
probe_config="$2"
probe_bash="$3"
probe_strict="$4"
if [[ "$probe_strict" == strict ]]; then set -euo pipefail; fi
. "$probe_root/shell/config.lib.sh"
probe_keys=(REMOTE_SSH_WELCOME REMOTE_SSH_WELCOME_BANNER REMOTE_SSH_WELCOME_COLOR
  REMOTE_SSH_WELCOME_DEBUG REMOTE_SSH_WELCOME_USER REMOTE_SSH_UPDATE_CHECK
  REMOTE_SSH_UPDATE_CHECK_INTERVAL REMOTE_SSH_ENABLE_GIT_SESSION_IDENTITY NO_COLOR)
probe_dump() {
  local probe_k probe_s probe_v probe_n
  printf 'STATE\0%s\0' "$1"
  for probe_k in "${probe_keys[@]}"; do
    probe_s="REMOTE_SSH_CONFIG_SOURCE_${probe_k#REMOTE_SSH_}"
    probe_v="REMOTE_SSH_CONFIG_LOADED_VALUE_${probe_k#REMOTE_SSH_}"
    for probe_n in "$probe_k" "$probe_s" "$probe_v"; do
      printf '%s\0%s\0%s\0' "$probe_n" "${!probe_n+x}" "${!probe_n-}"
      if declare -p "$probe_n" 2>/dev/null; then :; else printf 'UNDECLARED'; fi
      printf '\0'
    done
    if remote_ssh_config_value_is_current_owned "$probe_k"; then
      printf 'owned1\0'
    else
      printf 'owned0\0'
    fi
    remote_ssh_config_marker_key "$probe_k"
    remote_ssh_config_source_var "$probe_k"
    remote_ssh_config_loaded_value_var "$probe_k"
    remote_ssh_config_source "$probe_k"
    if remote_ssh_config_loaded_value "$probe_k"; then
      printf 'loaded-status0\0'
    else
      printf 'loaded-status1\0'
    fi
  done
  if compgen -A variable __remote_ssh_config_; then
    printf 'PRIVATE-VARS-LEAKED\0'
  else
    printf 'NO-PRIVATE-VARS\0'
  fi
}
probe_lookup() {
  local probe_kind="$1" probe_wanted="$2"
  printf 'LOOKUP\0%s\0%s\0' "$probe_kind" "$probe_wanted"
  if "$probe_kind" "$probe_wanted"; then
    printf '\0status0\0'
  else
    printf '\0status1\0'
  fi
}
'''
PARSER = r'''
remote_ssh_config_load
probe_dump loaded
probe_lookup remote_ssh_config_file_value_raw "$5"
probe_lookup remote_ssh_config_file_value "$5"
probe_lookup remote_ssh_config_file_value_raw UNKNOWN_KEY
REMOTE_SSH_CONFIG=off
probe_lookup remote_ssh_config_file_value_raw "$5"
probe_lookup remote_ssh_config_file_value "$5"
probe_dump disabled-lookups-only
[[ ! -e "$HOME/executed" ]]
'''


def case(name, data=b"", script=PARSER, setup="", env=None, kind="regular", wanted=KEYS[4]):
    return dict(name=name, data=data, script=script, setup=setup, env=env or {}, kind=kind, wanted=wanted)


def parser_cases():
    # Fixed byte-level cases, then a deterministic generated mixture. Nine
    # settings per file amortize baseline subprocess cost without sharing state.
    values = [
        b"", b" ", b"\t\r\v\f", b"0", b"  1 \t", b"\"\"", b"''", b"\"", b"'",
        b"' inner \t '", b'" inner \r "', b'"mismatch\'', b'\'mismatch"',
        b"a=b=c", b"left|right", b"# value", b"a # inline", b"\\t\\n\\$HOME",
        b"$(touch $HOME/executed)", b"`touch $HOME/executed`", b"${HOME}; false && :",
        b"'$(touch $HOME/executed)'", b"$((1+2))", b"<(touch $HOME/executed)",
        b"\x01\x08\x1b[31m\x7f", b"left\x00right", b"\"left\x00right\"",
        "\u00a0left\u00a0".encode(), "\u2003left\u2003".encode(), b"\xff\xfevalue",
        b"word\rinside", b"'\v\f\r'", b"'a' 'b'", b'"a" "b"', b"\\",
        b"'*?[x]!(y)'",
    ]
    result = []
    for batch in range(4):
        data = b" # comment\r\n\nmalformed\nUNKNOWN_KEY=ignored\nexport REMOTE_SSH_WELCOME=ignored\n"
        for index, key in enumerate(KEYS):
            data += b" \t" + key.encode() + b" \t=\t" + values[batch * 9 + index] + b" \r\n"
        result.append(case(f"fixed-{batch}-final-{'lf' if batch % 2 else 'no-lf'}", data if batch % 2 else data[:-1], wanted=KEYS[batch]))
    # Last duplicate includes an empty final value and malformed/unknown lines.
    result.append(case("duplicate-last-empty", b"REMOTE_SSH_WELCOME_USER=first\nREMOTE_SSH_WELCOME_USER='second'\nREMOTE_SSH_WELCOME_USER=\nREMOTE_SSH_WELCOME_USER x=ignored\nNO_COLOR=1"))
    rng = random.Random(20261027)
    for batch in range(6):
        lines = []
        for key in KEYS:
            lines.append(key.encode() + b"=" + rng.choice(values))
            lines.append(key.encode() + b"=" + rng.choice(values))
        rng.shuffle(lines)
        result.append(case(f"generated-{batch}", b"\n".join(lines) + (b"\n" if batch % 2 else b""), wanted=KEYS[batch]))
    option_data = b"\n".join(key.encode() + b"=' space \t| \\u00a0 '" for key in KEYS) + b"\n"
    profiles = {
        "ifs-comma": "IFS=,",
        "ifs-empty": "IFS=",
        "ifs-custom": "IFS=$'e=|\\t'",
        "glob-options": "set -f; shopt -s extglob nullglob failglob nocaseglob",
        "nocasematch": "shopt -s nocasematch",
        "posix": "set -o posix",
        "allexport": "set -a",
        "modern-local-options": "shopt -s localvar_inherit localvar_unset inherit_errexit 2>/dev/null || :",
    }
    for name, setup in profiles.items():
        data = option_data
        if name == "nocasematch":
            data += b"remote_ssh_welcome_user=lower-last\n"
        result.append(case(name, data, setup=setup))
    for locale in ("en_US.UTF-8", "pl_PL.UTF-8", "C.UTF-8"):
        data = b"\n".join(key.encode() + b"=" + "\u2003'\u2003inner\u2003'\u2003".encode() for key in KEYS)
        result.append(case(f"locale-{locale}", data, env={"LC_ALL": locale}))
    return result


LIFECYCLE = r'''
remote_ssh_config_load
probe_dump first
printf 'REMOTE_SSH_WELCOME_USER=changed\nNO_COLOR=\nREMOTE_SSH_WELCOME_COLOR=\n' >"$probe_config"
remote_ssh_config_load
probe_dump changed
REMOTE_SSH_WELCOME_USER=manual
REMOTE_SSH_WELCOME_COLOR=''
NO_COLOR=''
remote_ssh_config_load
probe_dump manual-different-empty-identical
: >"$probe_config"
remote_ssh_config_load
probe_dump removed-keys
unset REMOTE_SSH_WELCOME_USER REMOTE_SSH_WELCOME_COLOR
printf 'REMOTE_SSH_WELCOME_USER=again\nNO_COLOR=\n' >"$probe_config"
remote_ssh_config_load
probe_dump again
REMOTE_SSH_CONFIG=off
remote_ssh_config_load
probe_dump disabled
REMOTE_SSH_WELCOME_USER=environment
remote_ssh_config_load
probe_dump disabled-manual
unset REMOTE_SSH_CONFIG REMOTE_SSH_WELCOME_USER
remote_ssh_config_load
probe_dump enabled-again
rm "$probe_config"
remote_ssh_config_load
probe_dump removed-file
'''
CHILD = r'''
remote_ssh_config_load
probe_dump parent
"$probe_bash" --noprofile --norc -c '
  if [[ "$3" == strict ]]; then set -euo pipefail; fi
  . "$1/shell/config.lib.sh"
  printf "child-before:%s:%s:%s:%s:%s:%s\0" "$REMOTE_SSH_WELCOME_USER" "$NO_COLOR" "$REMOTE_SSH_CONFIG_SOURCE_WELCOME_USER" "$REMOTE_SSH_CONFIG_LOADED_VALUE_WELCOME_USER" "$REMOTE_SSH_CONFIG_SOURCE_NO_COLOR" "$REMOTE_SSH_CONFIG_LOADED_VALUE_NO_COLOR"
  remote_ssh_config_value_is_current_owned REMOTE_SSH_WELCOME_USER
  remote_ssh_config_value_is_current_owned NO_COLOR
  printf "REMOTE_SSH_WELCOME_USER=child\nNO_COLOR=\n" >"$2"
  remote_ssh_config_load
  printf "child-after:%s:%s:%s:%s\0" "$REMOTE_SSH_WELCOME_USER" "$NO_COLOR" "$REMOTE_SSH_CONFIG_SOURCE_WELCOME_USER" "$REMOTE_SSH_CONFIG_LOADED_VALUE_WELCOME_USER"
' _ "$probe_root" "$probe_config" "$probe_strict"
probe_dump parent-before-reload
remote_ssh_config_load
probe_dump parent-after-reload
'''
DYNAMIC = r'''
probe_outer() {
  local key=outer-key value=outer-value wanted=outer-wanted line=outer-line file=outer-file
  local source_var=outer-source loaded_var=outer-loaded
  local -a __remote_ssh_config_snapshot_keys=(outer-key) __remote_ssh_config_snapshot_values=(outer-value)
  local -a __remote_ssh_config_snapshot_present=(outer-present)
  local __remote_ssh_config_snapshot_count=123
  remote_ssh_config_load
  probe_lookup remote_ssh_config_file_value_raw REMOTE_SSH_WELCOME_USER
  printf 'outer:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s\0' "$key" "$value" "$wanted" "$line" "$file" "$source_var" "$loaded_var" "${__remote_ssh_config_snapshot_keys[0]}" "${__remote_ssh_config_snapshot_values[0]}" "${__remote_ssh_config_snapshot_present[0]}" "$__remote_ssh_config_snapshot_count"
}
probe_outer
probe_dump after-outer
probe_local_key() {
  local REMOTE_SSH_WELCOME_USER
  unset REMOTE_SSH_WELCOME_USER
  remote_ssh_config_load
  printf 'local-key:%s:%s\0' "${REMOTE_SSH_WELCOME_USER+x}" "${REMOTE_SSH_WELCOME_USER-}"
}
probe_local_key
probe_dump after-local-key
'''


def lifecycle_cases():
    data = b"REMOTE_SSH_WELCOME_USER=first\nNO_COLOR=\nREMOTE_SSH_WELCOME_COLOR=initial\n"
    return [
        case("reload", data, script=LIFECYCLE),
        case("exported-child", b"REMOTE_SSH_WELCOME_USER=first\nNO_COLOR=\n", script=CHILD),
        case("dynamic-scope", data, script=DYNAMIC),
        case("dynamic-local-options", data, script=DYNAMIC, setup="shopt -s localvar_inherit localvar_unset 2>/dev/null || :"),
        case("preexisting-empty-and-incomplete-markers", data, env={
            "REMOTE_SSH_WELCOME_USER": "", "NO_COLOR": "",
            "REMOTE_SSH_CONFIG_SOURCE_WELCOME_USER": "config",
            "REMOTE_SSH_CONFIG_LOADED_VALUE_NO_COLOR": "",
            "REMOTE_SSH_CONFIG_SOURCE_REMOTE_SSH_WELCOME_USER": "config",
        }),
        case("inherited-current-markers", data, env={
            "REMOTE_SSH_WELCOME_USER": "first", "NO_COLOR": "",
            "REMOTE_SSH_CONFIG_SOURCE_WELCOME_USER": "config",
            "REMOTE_SSH_CONFIG_LOADED_VALUE_WELCOME_USER": "first",
            "REMOTE_SSH_CONFIG_SOURCE_NO_COLOR": "config",
            "REMOTE_SSH_CONFIG_LOADED_VALUE_NO_COLOR": "",
        }),
        case("readonly-existing-values", data, script='readonly REMOTE_SSH_WELCOME_USER=locked NO_COLOR=locked; remote_ssh_config_load; probe_dump readonly-existing'),
        case("unexported-existing-values", data, script='REMOTE_SSH_WELCOME_USER=local-value; NO_COLOR=; remote_ssh_config_load; probe_dump unexported-existing'),
    ] + [case(f"toggle-{toggle!r}", data, env={"REMOTE_SSH_CONFIG": toggle}) for toggle in ("0", "false", "no", "off", "", "FALSE", "1")]


FAILURE = r'''
REMOTE_SSH_WELCOME_USER=old
REMOTE_SSH_CONFIG_SOURCE_WELCOME_USER=config
REMOTE_SSH_CONFIG_LOADED_VALUE_WELCOME_USER=old
NO_COLOR=manual
REMOTE_SSH_CONFIG_SOURCE_NO_COLOR=config
REMOTE_SSH_CONFIG_LOADED_VALUE_NO_COLOR=old
remote_ssh_config_load
probe_dump after-failure
probe_lookup remote_ssh_config_file_value_raw REMOTE_SSH_WELCOME_USER
probe_lookup remote_ssh_config_file_value REMOTE_SSH_WELCOME_USER
'''
PARTIAL_READ = r'''
read() {
  local probe_read_dest="${!#}"
  if builtin read "$@"; then
    case "$probe_read_dest" in
      line|__remote_ssh_config_scan_line)
        if [[ "${!probe_read_dest}" == INJECT_READ_FAILURE ]]; then
          printf -v "$probe_read_dest" '%s' ''
          printf 'injected read failure\n' >&2
          return 2
        fi
        ;;
    esac
    return 0
  else
    return 1
  fi
}
'''


def failure_cases():
    result = [case(kind, script=FAILURE, kind=kind) for kind in ("missing", "empty", "self-symlink", "directory", "unreadable", "tty")]
    result.append(case("no-home-no-xdg", script=FAILURE, setup="unset HOME XDG_CONFIG_HOME"))
    result.append(case("partial-read", b"REMOTE_SSH_WELCOME_USER=prefix\nINJECT_READ_FAILURE\nNO_COLOR=suffix\n", script=FAILURE, setup=PARTIAL_READ))
    # A standalone successful raw lookup keeps errexit enabled in its body.
    result.append(case("partial-read-direct-raw", b"REMOTE_SSH_WELCOME_USER=prefix\nINJECT_READ_FAILURE\nNO_COLOR=suffix\n", script="remote_ssh_config_file_value_raw REMOTE_SSH_WELCOME_USER; printf 'SURVIVED\\0'", setup=PARTIAL_READ))
    return result


INTEGRATION = r'''
export REMOTE_SSH_WELCOME=0 REMOTE_SSH_UPDATE_CHECK=0
. "$probe_root/shell/rc.sh"
probe_dump rc-initial
"$probe_bash" "$probe_root/bin/remote-ssh" guide config
printf 'REMOTE_SSH_WELCOME_BANNER=1\nREMOTE_SSH_WELCOME_USER=\nNO_COLOR=\n' >"$probe_config"
"$probe_bash" "$probe_root/bin/remote-ssh" guide config
. "$probe_root/shell/rc.sh"
probe_dump rc-reloaded
"$probe_bash" "$probe_root/bin/remote-ssh" guide config
REMOTE_SSH_WELCOME_USER=manual
export REMOTE_SSH_CONFIG=off
. "$probe_root/shell/rc.sh"
probe_dump rc-disabled-manual
"$probe_bash" "$probe_root/bin/remote-ssh" guide config
'''


def integration_cases():
    return [
        case("actual-rc-and-guide", b"REMOTE_SSH_WELCOME_BANNER=0\nREMOTE_SSH_WELCOME_USER=\nNO_COLOR=\n", script=INTEGRATION),
        case("guide-delimiter", b"REMOTE_SSH_WELCOME_COLOR=left|right\n", script='"$probe_bash" "$probe_root/bin/remote-ssh" guide config'),
    ]


def posix_cases():
    data = b"REMOTE_SSH_WELCOME_BANNER=0\nREMOTE_SSH_WELCOME_USER=0\nNO_COLOR=\n"
    helper = '''
set -o posix
remote_ssh_config_load
probe_load_status=$?
printf 'LOAD-STATUS:%s\\0' "$probe_load_status"
probe_dump posix-after-load
'''
    startup = '''
export REMOTE_SSH_WELCOME=0 REMOTE_SSH_UPDATE_CHECK=0
. "$probe_root/shell/rc.sh"
printf 'REMOTE_SSH_WELCOME_USER=1\\n' >"$probe_config"
''' + helper
    return [
        case("helper-after-enabling-posix", data, script=helper),
        case("helper-after-real-rc-then-posix", data, script=startup),
        case("source-rc-in-posix", data, script='export REMOTE_SSH_WELCOME=0 REMOTE_SSH_UPDATE_CHECK=0; set -o posix; . "$probe_root/shell/rc.sh"; printf "RC-SURVIVED\\0"'),
        case("guide-child-of-posix-parent", data, script='set -o posix; "$probe_bash" "$probe_root/bin/remote-ssh" guide config'),
        case("guide-posixly-correct-env", data, script='export POSIXLY_CORRECT=1; "$probe_bash" "$probe_root/bin/remote-ssh" guide config'),
        case("guide-exported-posix-shellopts", data, script='set -o posix; export SHELLOPTS; "$probe_bash" "$probe_root/bin/remote-ssh" guide config'),
    ]


def posix_gate_cases():
    data = b"REMOTE_SSH_WELCOME_USER=0\nNO_COLOR=\n"
    return [
        case("disabled-helper-after-posix", data, env={"REMOTE_SSH_CONFIG": "off"}, script='set -o posix; remote_ssh_config_load; probe_load_status=$?; printf "LOAD-STATUS:%s\\0" "$probe_load_status"; probe_dump disabled-posix'),
        case("disabled-raw-gated-after-posix", data, env={"REMOTE_SSH_CONFIG": "off"}, script='set -o posix; probe_lookup remote_ssh_config_file_value_raw REMOTE_SSH_WELCOME_USER; probe_lookup remote_ssh_config_file_value REMOTE_SSH_WELCOME_USER; probe_dump raw-gated-posix'),
    ]


def snapshot(repo: Path, workspace: Path):
    archive = subprocess.check_output(["git", "archive", BASE], cwd=repo)
    baseline = workspace / "baseline"
    baseline.mkdir()
    with tarfile.open(fileobj=io.BytesIO(archive)) as stream:
        stream.extractall(baseline, filter="data")
    current = workspace / "current"
    shutil.copytree(baseline, current)
    for relative in CHANGED:
        (current / relative).write_bytes((repo / relative).read_bytes())
    return {"baseline": baseline, "current": current}


def run_case(workspace, trees, bash, strict, item):
    pair = {}
    for version, tree in trees.items():
        case_id = hashlib.sha256(item["name"].encode()).hexdigest()[:8]
        home = workspace / "runs" / f"{item['name'].replace('/', '-')}-{case_id}-{bash.replace('/', '_')}-{strict}-{version}"
        config = home / ".config/remote-ssh/config"
        config.parent.mkdir(parents=True)
        if item["kind"] != "missing":
            if item["kind"] == "directory":
                config.mkdir()
            elif item["kind"] == "self-symlink":
                config.symlink_to("config")
            elif item["kind"] == "tty":
                config.symlink_to("/dev/tty")
            else:
                config.write_bytes(item["data"])
                if item["kind"] == "unreadable":
                    config.chmod(0)
        bindir = home / "bin"
        bindir.mkdir()
        (bindir / "bash").symlink_to(bash)
        env = {"HOME": str(home), "XDG_CONFIG_HOME": str(home / ".config"), "XDG_STATE_HOME": str(home / ".state"), "PATH": f"{bindir}:/usr/bin:/bin", "LC_ALL": "C", "TERM": "dumb", "TZ": "UTC"} | item["env"]
        script = HEADER + "\n" + item["setup"] + "\n" + item["script"]
        result = subprocess.run([bash, "--noprofile", "--norc", "-c", script, "_", str(tree), str(config), bash, strict, item["wanted"]], env=env, capture_output=True, timeout=30)
        stdout = result.stdout.replace(str(tree).encode(), b"<TREE>").replace(str(home).encode(), b"<HOME>")
        stderr = result.stderr.replace(str(tree).encode(), b"<TREE>").replace(str(home).encode(), b"<HOME>")
        pair[version] = {"status": result.returncode, "stdout_b64": base64.b64encode(stdout).decode(), "stderr_b64": base64.b64encode(stderr).decode()}
        # Populated parser fixtures must actually have produced exported config
        # ownership; comparing two empty/no-op executions is insufficient.
        if item["script"] == PARSER and item["name"] not in {
            "preexisting-empty-and-incomplete-markers", "inherited-current-markers"
        } and not item["name"].startswith("toggle-"):
            expected_keys = [KEYS[4], KEYS[8]] if item["name"] == "duplicate-last-empty" else KEYS
            for key in expected_keys:
                marker = f"REMOTE_SSH_CONFIG_SOURCE_{key.removeprefix('REMOTE_SSH_')}\0x\0config\0".encode()
                if marker not in stdout:
                    pair[version]["populated_state_verified"] = False
                    break
            else:
                pair[version]["populated_state_verified"] = True
    return {
        "name": item["name"], "bash": bash, "strict": strict,
        "input_b64": base64.b64encode(item["data"]).decode(),
        "setup": item["setup"], "kind": item["kind"], "env_overrides": item["env"],
        "stdout_status_equal": all(pair["baseline"][key] == pair["current"][key] for key in ("status", "stdout_b64")),
        "stderr_equal": pair["baseline"]["stderr_b64"] == pair["current"]["stderr_b64"],
        "existing_bash32_posix_initialization_failure": item["name"] == "posix" and bash == "/bin/bash",
        "results": pair,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--phase", choices=("parser", "lifecycle", "failure", "integration", "posix", "posix_gate"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--snapshot-evidence", type=Path, help="Reuse frozen source trees from an earlier evidence JSON, with fresh processes/HOMEs")
    args = parser.parse_args()
    workspace = Path(tempfile.mkdtemp(prefix=f"config-reaudit-{args.phase}-", dir="/private/tmp"))
    if args.snapshot_evidence:
        prior = json.loads(args.snapshot_evidence.read_text())
        trees = {version: Path(prior.get("source_trees", {}).get(version, str(Path(prior["workspace"]) / version))) for version in ("baseline", "current")}
    else:
        trees = snapshot(args.repo, workspace)
    cases = globals()[args.phase + "_cases"]()
    records = []
    for item in cases:
        for bash in BASHES:
            for strict in ("normal", "strict"):
                record = run_case(workspace, trees, bash, strict, item)
                records.append(record)
                print(f"{args.phase}:{item['name']}:{bash}:{strict}:state={record['stdout_status_equal']}:stderr={record['stderr_equal']}", flush=True)
    payload = {
        "baseline_commit": BASE, "phase": args.phase, "workspace": str(workspace),
        "source_trees": {version: str(tree) for version, tree in trees.items()},
        "shell_versions": {bash: subprocess.check_output([bash, "--version"], text=True).splitlines()[0] for bash in BASHES},
        "source_sha256": {version: {path: hashlib.sha256((tree / path).read_bytes()).hexdigest() for path in CHANGED} for version, tree in trees.items()},
        "pair_count": len(records),
        "state_status_differences": sum(not record["stdout_status_equal"] for record in records),
        "stderr_differences": sum(not record["stderr_equal"] for record in records),
        "records": records,
    }
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({key: value for key, value in payload.items() if key != "records"}), flush=True)


if __name__ == "__main__":
    main()
