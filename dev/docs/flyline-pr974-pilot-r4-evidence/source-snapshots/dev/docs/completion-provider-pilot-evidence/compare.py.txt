"""Compare Bash completion providers in isolated developer PTYs; no downloads."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import random
import re
import shlex
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1] / "interactive-tools-performance-evidence")
)
from benchmark import PROMPT, Session, environment  # noqa: E402

CASES = [
    ("rg-version", ["rg", "--ver"], {"--version"}),
    ("rg-color", ["rg", "--color", "a"], {"always", "auto"}),
    ("rg-type", ["rg", "--type", "py"], {"py"}),
    ("rg-file", ["rg", "--file", "fixture_uni"], {"fixture_unique.txt"}),
    ("rg-space", ["rg", "--file", "fixture space/ma"], {"fixture space/match.txt"}),
    ("fd-color-option", ["fd", "--col"], {"--color"}),
    ("fd-color-value", ["fd", "--color", "a"], {"always", "auto"}),
    ("git-subcommand", ["git", "swi"], {"switch"}),
    ("git-switch-option", ["git", "switch", "--det"], {"--detach"}),
    ("git-branches", ["git", "switch", "bench-"], {"bench-alpha", "bench-beta"}),
    ("git-modified-file", ["git", "restore", "fixture_uni"], {"fixture_unique.txt"}),
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def describe(values: list[float]) -> dict[str, Any]:
    ordered = sorted(values)
    return {
        "n": len(values),
        "median": statistics.median(values),
        "min": min(values),
        "max": max(values),
        "p95": ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))],
    }


def initialization(provider: str, root: Path) -> str:
    quote = shlex.quote
    if provider.startswith("argc"):
        definitions = root / "definitions"
        return (
            f"export ARGC_COMPLETIONS_ROOT={quote(str(definitions))}\n"
            f"export ARGC_COMPLETIONS_PATH={quote(str(definitions / 'completions/macos'))}:"
            f"{quote(str(definitions / 'completions'))}\n"
            "export ARGC_COMPGEN_DESCRIPTION=0\n"
            "source <(argc --argc-completions bash git rg fd)\n"
        )
    if provider == "carapace":
        return "\n".join(f"source <(carapace {cmd} bash)" for cmd in ("git", "rg", "fd")) + "\n"
    if provider == "native":
        return (
            "\n".join(
                f"source {quote(str(root / 'native' / (cmd + '.bash')))}"
                for cmd in ("git", "rg", "fd")
            )
            + "\n"
        )
    return ""


def rcfile(provider: str, root: Path) -> str:
    setup = ["PS1='BMARK> '", "set -o vi", initialization(provider, root)]
    setup += ["bench_words() {", 'case "$1" in']
    for index, (_, words, _) in enumerate(CASES):
        line = " ".join(w.replace("\\", "\\\\").replace(" ", "\\ ") for w in words)
        setup.append(
            f"{index}) COMP_WORDS=({' '.join(shlex.quote(w) for w in words)}); "
            f"COMP_CWORD={len(words) - 1}; COMP_LINE={shlex.quote(line)};;"
        )
    setup += ["esac", "}"]
    setup.append(r"""
bench_query() {
    local query_id=$1 spec callback current previous start finish result fallback=0
    bench_words "$query_id"
    COMP_POINT=${#COMP_LINE}; COMP_TYPE=9; COMP_KEY=9
    current=${COMP_WORDS[COMP_CWORD]}; previous=${COMP_WORDS[COMP_CWORD-1]}
    spec=$(complete -p "${COMP_WORDS[0]}") || return 51
    [[ "$spec" =~ -F[[:space:]]+([^[:space:]]+) ]] || return 52
    callback=${BASH_REMATCH[1]}
    COMPREPLY=()
    # Callback-only probe: compopt requires a genuine Readline completion context.
    # Candidate generation is measured here; real Tab controls below keep compopt.
    compopt() { :; }
    start=${EPOCHREALTIME/./}
    "$callback" "${COMP_WORDS[0]}" "$current" "$previous"
    result=$?
    if ((${#COMPREPLY[@]} == 0)) && [[ "$spec" == *' -o default '* || "$spec" == *' -o bashdefault '* ]]; then
        mapfile -t COMPREPLY < <(compgen -f -- "$current")
        fallback=1
    fi
    finish=${EPOCHREALTIME/./}
    unset -f compopt
    printf '\036QUERY:%s:%s:%s:%s\000' "$query_id" "$((finish-start))" "$result" "$fallback"
    ((${#COMPREPLY[@]})) && printf '%s\000' "${COMPREPLY[@]}"
    printf '\037\n'
}
pilot_capture() { printf '\036ARG:%s\037\n' "$1"; }
""")
    return "\n".join(setup)


def normalize(candidate: str) -> str:
    # Preserve the original candidate as evidence; normalize only comparison spelling.
    candidate = candidate.rstrip().split("\t", 1)[0]
    try:
        parts = shlex.split(candidate)
    except ValueError:
        return candidate
    return parts[0] if len(parts) == 1 else candidate


def request(session: Session, index: int) -> dict[str, Any]:
    offset = len(session.transcript)
    session.pending.clear()
    session.send(f"bench_query {index}\r".encode())
    session.expect(b"\x1f", raw=True)
    session.expect(PROMPT)
    chunk = bytes(session.transcript[offset:])
    match = re.search(rb"\x1eQUERY:(\d+):(\d+):(\d+):(\d+)\x00(.*?)\x1f", chunk, re.S)
    if match is None:
        raise RuntimeError(f"invalid query frame: {chunk[-1500:]!r}")
    candidates = [s.decode() for s in match[5].split(b"\x00") if s]
    normalized = {normalize(s) for s in candidates}
    expected = CASES[index][2]
    return {
        "case": CASES[index][0],
        "ms": int(match[2]) / 1000,
        "callback_exit": int(match[3]),
        "file_fallback": bool(int(match[4])),
        "candidates": candidates,
        "missing": sorted(expected - normalized),
        "passed": expected <= normalized,
    }


def controls(session: Session) -> dict[str, Any]:
    # Manual callback probes must not leak their globals into real Readline calls.
    session.pending.clear()
    session.send(
        b"unset COMPREPLY COMP_LINE COMP_POINT COMP_CWORD COMP_WORDS COMP_KEY COMP_TYPE; printf '\\036CLEAN\\037\\n'\r"
    )
    session.expect(b"\x1eCLEAN\x1f", raw=True)
    session.expect(PROMPT)
    tabs = []
    for text, expected in (
        (b"rg --ver\t", ["rg", "--version"]),
        (b"fd --max-dep\t", ["fd", "--max-depth"]),
        (b"git switch bench-a\t", ["git", "switch", "bench-alpha"]),
        (b"rg --file fixture_uni\t", ["rg", "--file", "fixture_unique.txt"]),
        (b"rg --file fixture\\ space/ma\t", ["rg", "--file", "fixture space/match.txt"]),
    ):
        session.pending.clear()
        start = time.perf_counter()
        session.send(text)
        passed = False
        observed = ""
        while time.perf_counter() - start < 2:
            session.read(0.005)
            observed = "".join(session.screen.rows[session.screen.row]).rstrip()
            if not observed.startswith(PROMPT.decode()):
                continue
            try:
                actual = shlex.split(observed[len(PROMPT) :])
            except ValueError:
                continue
            if actual == expected:
                passed = True
                break
        tabs.append(
            {
                "input": text.decode(),
                "passed": passed,
                "observed": observed,
                "ms": (time.perf_counter() - start) * 1000,
            }
        )
        session.clear()
    session.pending.clear()
    offset = len(session.transcript)
    session.send(b"pilot_capture ac")
    session.quiet(0.1)
    session.send(b"\x1b")
    session.quiet(0.15)
    session.send(b"hrbA")
    session.quiet(0.1)
    session.send(b"\r")
    session.expect(b"\x1f", raw=True)
    session.expect(PROMPT)
    match = re.search(rb"\x1eARG:([^\x1f]*)\x1f", session.transcript[offset:])
    vi_actual = match[1].decode() if match else "[no argument]"
    return {"tabs": tabs, "vi_actual": vi_actual, "vi_passed": vi_actual == "bc"}


def sample(
    provider: str, index: int, args: argparse.Namespace, base: Path, fixture: Path
) -> dict[str, Any]:
    home = base / provider / str(index)
    home.mkdir(parents=True)
    for name in ("config", "data", "state", "cache"):
        (home / name).mkdir()
    rc = home / "rc.sh"
    rc.write_text(rcfile(provider, args.root))
    env = environment(home, args.root / "bin")
    if provider == "argc-gnu":
        env["PATH"] = str(args.root / "gnu-bin") + ":" + env["PATH"]
    env.update(
        {"GIT_CONFIG_NOSYSTEM": "1", "GIT_TERMINAL_PROMPT": "0", "ARGC_SHELL_PATH": str(args.bash)}
    )
    session = Session([str(args.bash), "--noprofile", "--rcfile", str(rc), "-i"], env, fixture)
    result: dict[str, Any] = {"provider": provider, "round": index, "warmup": index < args.warmup}
    try:
        session.send(b"printf '\\036READY\\037\\n'\r")
        session.expect(b"\x1eREADY\x1f", raw=True)
        result["startup_ms"] = (time.perf_counter() - session.started) * 1000
        session.expect(PROMPT)
        session.quiet(0.03)
        rss = subprocess.check_output(["/bin/ps", "-o", "rss=", "-p", str(session.pid)], text=True)
        result["rss_mib"] = int(rss.strip()) / 1024
        result["key_ms"] = []
        for _ in range(3):
            session.exchange(b": BENCH", b"BENCH")
            result["key_ms"].append(session.exchange(b"X", b"BENCHX"))
            session.clear()
        queries = list(range(len(CASES)))
        random.Random(20261108 + index).shuffle(queries)
        result["queries"] = [request(session, q) for q in queries] if provider != "baseline" else []
        if provider != "baseline" and index == args.warmup:
            result["controls"] = controls(session)
        result["ok"] = True
    except (RuntimeError, subprocess.SubprocessError) as error:
        result.update({"ok": False, "error": str(error)})
    finally:
        result.update(session.close())
        if index == args.warmup or not result["ok"]:
            (args.output / f"{provider}-transcript.txt").write_text(
                json.dumps(session.transcript.decode(errors="replace")) + "\n"
            )
    return result


def fixture_repository(directory: Path, env: dict[str, str]) -> None:
    directory.mkdir()
    (directory / "fixture_unique.txt").touch()
    (directory / "fixture space").mkdir()
    (directory / "fixture space/match.txt").touch()
    for command in (
        ["git", "init", "-q"],
        ["git", "config", "user.name", "Benchmark"],
        ["git", "config", "user.email", "benchmark@example.invalid"],
        ["git", "add", "."],
        ["git", "-c", "commit.gpgsign=false", "commit", "--allow-empty", "-qm", "fixture"],
        ["git", "branch", "bench-alpha"],
        ["git", "branch", "bench-beta"],
    ):
        subprocess.run(command, cwd=directory, env=env, check=True, capture_output=True)
    (directory / "fixture_unique.txt").write_text("modified\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bash", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=15)
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument(
        "--providers", nargs="+", choices=("baseline", "native", "argc", "argc-gnu", "carapace")
    )
    args = parser.parse_args()
    args.bash = args.bash.resolve(strict=True)
    args.root = args.root.resolve(strict=True)
    if args.iterations < 1 or args.warmup < 0:
        parser.error("invalid iteration counts")
    args.output.mkdir(parents=True, exist_ok=True)
    providers = args.providers or ["baseline", "native", "argc", "argc-gnu", "carapace"]
    samples = []
    with tempfile.TemporaryDirectory(prefix="completion-provider-pilot-") as temp:
        base = Path(temp)
        home = base / "fixture-home"
        home.mkdir()
        env = environment(home, args.root / "bin")
        env.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_TERMINAL_PROMPT": "0"})
        fixture = base / "fixture"
        fixture_repository(fixture, env)
        rng = random.Random(20261108)
        for index in range(args.iterations + args.warmup):
            order = providers[:]
            rng.shuffle(order)
            for provider in order:
                result = sample(provider, index, args, base, fixture)
                samples.append(result)
                (args.output / "samples.json").write_text(json.dumps(samples, indent=2) + "\n")
                print(f"round={index} {provider} ok={result['ok']}", flush=True)
                if not result["ok"]:
                    raise RuntimeError(result["error"])
    summaries = {}
    for provider in providers:
        chosen = [s for s in samples if s["provider"] == provider and not s["warmup"]]
        summaries[provider] = {
            "startup_ms": describe([s["startup_ms"] for s in chosen]),
            "rss_mib": describe([s["rss_mib"] for s in chosen]),
            "key_ms": describe([v for s in chosen for v in s["key_ms"]]),
            "queries": {},
        }
        for name, _, _ in CASES:
            queries = [q for s in chosen for q in s["queries"] if q["case"] == name]
            if queries:
                summaries[provider]["queries"][name] = {
                    "ms": describe([q["ms"] for q in queries]),
                    "passes": sum(q["passed"] for q in queries),
                    "example": queries[0],
                }
    report = {
        "host": platform.platform(),
        "python": platform.python_version(),
        "iterations": args.iterations,
        "warmup": args.warmup,
        "script_sha256": digest(Path(__file__)),
        "pty_helper_sha256": digest(
            Path(__file__).resolve().parents[1]
            / "interactive-tools-performance-evidence/benchmark.py"
        ),
        "summaries": summaries,
    }
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Saved {args.output / 'report.json'}", flush=True)


if __name__ == "__main__":
    main()
