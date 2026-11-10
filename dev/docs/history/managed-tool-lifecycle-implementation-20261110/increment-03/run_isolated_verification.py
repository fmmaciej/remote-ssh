"""Offline audit/test entrypoint. Never inherits ambient application variables.

Example: python run_isolated_verification.py --repo /public/checkout \
  --output /private/tmp/lifecycle-audit --label audit --timeout 3000 pytest \
  tests/test_managed_reports.py tests/test_managed_prune.py
For the complete required suite choose mode smoke with no test paths.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import subprocess
import time
from pathlib import Path


def public_environment(home: Path) -> dict[str, str]:
    env = {
        "PATH": "/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin",
        "LANG": "C", "LC_ALL": "C", "TZ": "UTC", "HOME": str(home),
        "XDG_CONFIG_HOME": str(home / ".config"),
        "XDG_CACHE_HOME": str(home / ".cache"),
        "XDG_STATE_HOME": str(home / ".local/state"),
        "XDG_DATA_HOME": str(home / ".local/share"),
        "INSTALL_PREFIX": str(home / ".local/opt"),
        "INSTALL_BIN_DIR": str(home / ".local/bin"),
        "BASH_ENV": "", "ENV": "", "GIT_CONFIG_GLOBAL": str(home / ".gitconfig"),
        "GIT_CONFIG_NOSYSTEM": "1", "REMOTE_SSH_ENABLE_GIT_SESSION_IDENTITY": "0",
        "PYTHONDONTWRITEBYTECODE": "1", "UV_OFFLINE": "1", "UV_NO_ENV_FILE": "1",
        "UV_PYTHON_DOWNLOADS": "never", "UV_CACHE_DIR": "/private/tmp/remote-ssh-uv-cache",
    }
    home.mkdir(parents=True, exist_ok=False)
    for name in ("XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_STATE_HOME", "XDG_DATA_HOME"):
        Path(env[name]).mkdir(parents=True, exist_ok=True)
    return env


def source_subject(repo: Path, env: dict[str, str]) -> dict[str, str | None]:
    # Only tracked public changes and explicitly owned public runtime/test inputs.
    names = subprocess.check_output(
        ["git", "-c", "core.fsmonitor=false", "-C", str(repo), "diff", "--name-only", "-z"],
        env=env,
    ).decode().split("\0")
    names += [path.relative_to(repo).as_posix() for directory in (
        "tools/lib/managed", "tools/lib/commands/check"
    ) for path in (repo / directory).glob("*.sh")]
    names += [path.relative_to(repo).as_posix() for path in (repo / "dev/tests").glob("test_managed*.py")]
    names += ["tools/lib/managed.lib.sh", "tools/lib/commands/list.sh", "dev/tests/managed_fixture.py"]
    return {name: hashlib.sha256((repo / name).read_bytes()).hexdigest()
            if (repo / name).is_file() else None for name in sorted(set(names)) if name}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--timeout", type=int, default=3000)
    parser.add_argument("mode", choices=("pytest", "smoke"))
    parser.add_argument("tests", nargs="*")
    args = parser.parse_args()
    if not args.label.replace("-", "").isalnum() or not 1 <= args.timeout <= 7200:
        parser.error("label must be plain alphanumeric/hyphen and timeout1..7200")
    repo, output = args.repo.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    log = output / (args.label + ".log")
    xml = output / (args.label + ".xml")
    result_path = output / (args.label + "-result.json")
    for path in (log, xml, result_path):
        if path.exists():
            parser.error("refusing to overwrite earlier verification evidence")
    env = public_environment(output / (args.label + "-home"))
    if args.mode == "smoke":
        if args.tests:
            parser.error("smoke does not accept test paths")
        env["PYTEST_ADDOPTS"] = "--junitxml=" + str(xml) + " -ra"
        command = ["just", "smoke"]
    else:
        command = ["uv", "run", "--offline", "--project", str(repo / "dev"), "pytest", "-q",
                   "-p", "no:cacheprovider", "--junitxml=" + str(xml), *args.tests]
    subject = source_subject(repo, env)
    (output / (args.label + "-source-hashes.json")).write_text(json.dumps(subject, indent=2))
    started = time.monotonic()
    code, timed_out = 124, False
    with log.open("x") as stream:
        try:
            process = subprocess.Popen(command, cwd=repo / "dev", env=env, stdout=stream,
                                       stderr=subprocess.STDOUT, start_new_session=True)
            try:
                code = process.wait(timeout=args.timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=5)
        except OSError:
            raise
    unchanged = source_subject(repo, env) == subject
    result_path.write_text(json.dumps({
        "command": command, "cwd": str(repo / "dev"), "returncode": code,
        "timeout": args.timeout, "timed_out": timed_out,
        "elapsed_seconds": time.monotonic() - started, "source_unchanged": unchanged,
        "environment_provenance": "fixed allowlist; no ambient values, dotenv or startup env; synthetic HOME/XDG/Git context",
        "environment_keys": sorted(env), "native_capability": "No optional private native path inherited; explicit unavailable tests remain skipped",
    }, indent=2))
    print(json.dumps({"label": args.label, "returncode": code, "source_unchanged": unchanged}))
    raise SystemExit(code)


if __name__ == "__main__":
    main()
