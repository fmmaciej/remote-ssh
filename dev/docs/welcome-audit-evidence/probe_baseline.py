#!/usr/bin/env python3
"""Independent, untimed welcome contract probes; no worktree runtime writes."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile

PINNED = "39226a2d9074acf08279e7c3edde6a51cc2a629c"
REPO = Path(__file__).resolve().parents[3]
BASHES = [Path("/bin/bash"), Path("/opt/homebrew/bin/bash").resolve()]


def executable(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    path.chmod(0o755)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tree", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="welcome-independent-audit-") as temporary:
        root = Path(temporary)
        tree = args.tree.resolve() if args.tree else root / "baseline"
        if not args.tree:
            tree.mkdir()
            archive = subprocess.check_output(["git", "archive", PINNED], cwd=REPO)
            with tarfile.open(fileobj=io.BytesIO(archive)) as packed:
                packed.extractall(tree, filter="data")
        for bash in BASHES:
            suite = root / ("bash32" if bash == Path("/bin/bash") else "bash53")
            home, shims, temp = suite / "home", suite / "bin", suite / "tmp"
            for directory in (home, shims, temp):
                directory.mkdir(parents=True)
            (shims / "bash").symlink_to(bash)
            executable(shims / "hostname", "#!/bin/sh\ncase \"$1\" in -I) printf '203.0.113.9\\n';; *) printf 'audit-host\\n';; esac\n")
            executable(shims / "ssh-add", "#!/bin/sh\nprintf '256 SHA256:audit key\\n'\n")
            for command in ("bssh", "python3", "ssh", "fzf"):
                executable(shims / command, "#!/bin/sh\nexit 0\n")
            config = home / ".config" / "remote-ssh"
            config.mkdir(parents=True)
            (config / "expected-tools").write_text("rg\nfd\n")
            for tool in ("rg", "fd"):
                definition = (tree / "tools" / "defs" / f"{tool}.sh").read_text()
                match = re.search(r'^VERSION="([^"]+)"', definition, re.MULTILINE)
                assert match
                release = home / "opt" / f"{tool}-{match[1]}"
                executable(release / tool, "#!/bin/sh\nexit 0\n")
                (release / ".remote-ssh-release").write_text(
                    f"format=1\ntool={tool}\nversion={match[1]}\nlayout=binary\nexecutable={tool}\n"
                )
                (shims / tool).symlink_to(release / tool)
            state = home / "state"
            state.mkdir()
            cache = state / "update-check"
            cache.write_text("checked_at=1\nchecked_at_text=2026-10-28 audit\nstatus=current\n")
            env = {
                "HOME": str(home), "XDG_CONFIG_HOME": str(home / ".config"),
                "XDG_STATE_HOME": str(home / ".local" / "state"),
                "PATH": f"{shims}:/usr/bin:/bin", "TMPDIR": str(temp),
                "LC_ALL": "C", "TERM": "xterm-256color",
                "REMOTE_ENV_DIR": str(tree), "REMOTE_SSH_WELCOME_BANNER": "0",
                "REMOTE_SSH_WELCOME_COLOR": "0", "REMOTE_SSH_WELCOME_USER": "0",
                "REMOTE_SSH_UPDATE_CHECK_STATE_DIR": str(state),
                "REMOTE_SSH_GIT_SESSION_IDENTITY_STATUS": "ok",
                "SSH_AUTH_SOCK": str(home / "agent.sock"),
                "INSTALL_PREFIX": str(home / "opt"), "INSTALL_BIN_DIR": str(shims),
            }
            version = subprocess.check_output([str(bash), "--version"], env=env).decode().splitlines()[0]

            def run(name: str, script: str, *, overrides: dict[str, str] | None = None,
                    input_text: str = "", expected: str | None = None) -> dict[str, object]:
                process = subprocess.run(
                    [str(bash), "--noprofile", "--norc", "-c", script, "_", str(tree)],
                    env=env | (overrides or {}), cwd=home, input=input_text.encode(),
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True,
                    timeout=10, check=False,
                )
                output, error = process.stdout.decode(), process.stderr.decode()
                record: dict[str, object] = {
                    "name": name, "bash": str(bash), "version": version,
                    "script": script, "returncode": process.returncode,
                    "stdout": output, "stderr": error,
                    "stdout_sha256": hashlib.sha256(process.stdout).hexdigest(),
                    "checks": [],
                }
                records.append(record)
                assert process.returncode == 0, record
                if expected is not None:
                    assert output == expected, record
                return record

            base_call = '. "$1/shell/welcome.lib.sh"; remote_ssh_welcome_run'
            healthy = run("populated-healthy", base_call)
            assert "tools:   2 checked / 2 ok\n" in str(healthy["stdout"])
            assert "scripts: 4 checked / 4 ok\n" in str(healthy["stdout"])
            assert "sw:      ssh-agent ok / git config ok\n" in str(healthy["stdout"])
            assert "next:" not in str(healthy["stdout"])
            assert not healthy["stderr"]
            healthy["checks"] = ["actual populated providers", "no next", "quiet stderr"]
            (shims / "fd").unlink()
            (shims / "bssh").unlink()
            cache.write_text("checked_at=1\nchecked_at_text=2026-10-28 audit\nstatus=update-available\n")
            actionable = run("populated-actionable", base_call,
                             overrides={"REMOTE_SSH_GIT_SESSION_IDENTITY_STATUS": "missing"})
            assert "tools:   2 checked / 1 ok\n" in str(actionable["stdout"])
            assert "scripts: 4 checked / 3 ok\n" in str(actionable["stdout"])
            assert str(actionable["stdout"]).endswith("\nnext:    remote-ssh doctor\n"), actionable
            assert not actionable["stderr"]
            actionable["checks"] = ["actual missing-tool/requirement/update/Git issues", "one final doctor"]
            strict = run("populated-actionable-strict", "set -euo pipefail; " + base_call,
                         overrides={"REMOTE_SSH_GIT_SESSION_IDENTITY_STATUS": "missing"})
            if bash == Path("/bin/bash"):
                assert "REMOTE_SSH_WELCOME_ISSUES[@]: unbound variable" in str(strict["stderr"]), strict
                assert "next:" not in str(strict["stdout"]), strict
                strict["checks"] = ["known baseline Bash 3.2 nounset issue-array limitation", "outer returncode remains zero"]
            else:
                assert strict["stdout"] == actionable["stdout"], strict
                assert not strict["stderr"], strict
                strict["checks"] = ["direct strict call matches ordinary populated output"]

            custom_shell = suite / "custom-shell"
            bundled = custom_shell / "welcome.d"
            bundled.mkdir(parents=True)
            inherited = suite / "inherited-issues"
            inherited.write_text("original\n")
            executable(bundled / "00-replay", "#!/bin/sh\nif read value; then printf 'BAD-stdin\\n'; else printf 'eof\\n'; fi\nprintf ' \\\\hello\\rX\\n\\nlast'\nprintf 'module-stderr\\n' >&2\nif test \"${AUDIT_EMIT_ISSUES:-1}\" = 1; then printf 'update\\nupdate\\nmystery\\n' >>\"$REMOTE_SSH_WELCOME_ISSUES_FILE\"; fi\nexit 7\n")
            executable(bundled / "10-after", "#!/bin/sh\nprintf 'sibling\\n'\n")
            external_script = '''set -eo pipefail
. "$1/shell/welcome.lib.sh"
REMOTE_SSH_WELCOME_ISSUES=(inherited)
remote_ssh_welcome_run
read -r untouched
printf 'after=%s\\n' "$untouched"
printf 'file=%s array=%s\\n' "${REMOTE_SSH_WELCOME_ISSUES_FILE-unset}" "${REMOTE_SSH_WELCOME_ISSUES-unset}"
'''
            external_env = {"REMOTE_SHELL_DIR": str(custom_shell), "REMOTE_SSH_UPDATE_CHECK": "0",
                            "REMOTE_SSH_WELCOME_ISSUES_FILE": str(inherited)}
            expected = "eof\n \\hello\rX\n\nlast\nsibling\n\nnext:    remote-ssh update\nafter=untouched\nfile=unset array=unset\n"
            replay = run("external-replay-failure-cleanup", external_script,
                         overrides=external_env, input_text="untouched\n", expected=expected)
            assert inherited.read_text() == "original\n"
            assert not list(temp.iterdir())
            assert not replay["stderr"]
            replay["checks"] = ["stdin EOF and caller input retained", "exact CR/backslash/blank/no-LF replay", "failure continuation", "deduplicated issues", "cleanup", "inherited file untouched"]
            debug = run("external-debug", external_script,
                        overrides=external_env | {"REMOTE_SSH_WELCOME_DEBUG": "1"},
                        input_text="untouched\n", expected=expected)
            assert "module-stderr\n" in str(debug["stderr"])
            assert "(exit 7)" in str(debug["stderr"])
            assert "ignoring unknown issue: mystery" in str(debug["stderr"])
            debug["checks"] = ["debug stderr", "failure diagnostic", "unknown issue diagnostic"]
            strict_external = run("external-replay-failure-cleanup-strict-noissues",
                                  external_script.replace("set -eo pipefail", "set -euo pipefail"),
                                  overrides=external_env | {"AUDIT_EMIT_ISSUES": "0"},
                                  input_text="untouched\n",
                                  expected=expected.replace("\nnext:    remote-ssh update\n", ""))
            assert not strict_external["stderr"], strict_external
            strict_external["checks"] = ["direct strict call", "exact stdout and caller input", "failure continuation"]

            for module in bundled.iterdir():
                module.unlink()
            executable(bundled / "00-options", '''#!/usr/bin/env bash
case $- in *e*) e=on;; *) e=off;; esac
if shopt -q nullglob; then n=on; else n=off; fi
printf 'module e=%s n=%s\\n' "$e" "$n"
''')
            option_script = '''set -e
shopt -u nullglob
. "$1/shell/welcome.lib.sh"
export SHELLOPTS
remote_ssh_welcome_run
case $- in *e*) e=on;; *) e=off;; esac
if shopt -q nullglob; then n=on; else n=off; fi
printf 'caller e=%s n=%s\\n' "$e" "$n"
declare -p SHELLOPTS
'''
            options = run("exported-SHELLOPTS-scope", option_script, overrides=external_env)
            assert str(options["stdout"]).startswith("module e=off n=off\ncaller e=on n=off\n")
            assert "declare -rx SHELLOPTS=" in str(options["stdout"])
            options["checks"] = ["external capture set +e", "caller errexit/nullglob retained", "export attribute retained"]
            if bash != Path("/bin/bash"):
                bashopts = run("exported-BASHOPTS-scope", option_script.replace("export SHELLOPTS", "export SHELLOPTS BASHOPTS"), overrides=external_env)
                assert str(bashopts["stdout"]).startswith("module e=off n=on\ncaller e=on n=off\n")
                bashopts["checks"] = ["external original nullglob-on scope", "caller options retained"]

            private_env = env.copy()
            private_env.pop("REMOTE_SSH_WELCOME_BANNER")
            private_env.pop("REMOTE_SSH_WELCOME_COLOR")
            saved_env = env
            env = private_env
            private = run("private-inbound-state", '''. "$1/shell/welcome.lib.sh"
REMOTE_SSH_WELCOME_BANNER=0
NO_COLOR=1
COLUMNS=20
REMOTE_SSH_STATUS_LIB_LOADED=1
hostname() { printf 'PRIVATE\\n'; }
remote_ssh_welcome_run
''')
            assert "Remote-SSH\n" in str(private["stdout"])
            assert "\x1b[32m" in str(private["stdout"])
            assert "host:    audit-host / 203.0.113.9\n" in str(private["stdout"])
            assert "tools:   2 checked / 1 ok\n" in str(private["stdout"])
            private["checks"] = ["fresh executable hides nonexported banner/color/columns/provider/status flag"]
            env = saved_env
            hook = suite / "startup-hook"
            hook_log = suite / "hook-log"
            hook.write_text('printf "hook\\n" >>"$AUDIT_HOOK_LOG"\n')
            hook_case = run("nonempty-BASH_ENV", f'. "$1/shell/welcome.lib.sh"; export BASH_ENV="{hook}"; remote_ssh_welcome_run',
                            overrides={"AUDIT_HOOK_LOG": str(hook_log)})
            assert hook_log.read_text().splitlines() == ["hook"] * 3
            hook_case["checks"] = ["once-per-bundled-executable startup hook (three)"]

        result = {"baseline": PINNED, "tree": "pinned git archive" if not args.tree else str(tree),
                  "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  "records": records, "status": "PASS"}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n")
        print(f"PASS {len(records)} untimed probes; output: {args.output}")


if __name__ == "__main__":
    main()
