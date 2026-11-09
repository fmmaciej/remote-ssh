"""Offline native comparison: Readline, official 1.10.0 and the patched library.

Writes acceptance budgets before measurement. Does not qualify a remote host.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import random
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1] / "docs/interactive-tools-performance-evidence")
)
from benchmark import PROMPT, READY, Session, config, environment  # noqa: E402

BUDGETS = {
    "startup_median_over_readline_ms": 30,
    "startup_p95_over_readline_ms": 60,
    "single_key_median_ms": 2,
    "single_key_p95_ms": 8,
    "extra_idle_rss_mib": 12,
    "file_tab_median_ms": 50,
    "file_tab_p95_ms": 150,
    "bracketed_paste_p95_ms": 500,
    "idle_cpu_percent_of_one_core": 1,
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def describe(values: list[float]) -> dict[str, float | int]:
    ordered = sorted(values)
    return {
        "n": len(values),
        "median": statistics.median(values),
        "p95": ordered[min(len(values) - 1, int(len(values) * 0.95))],
    }


def process_cpu(pid: int) -> float:
    raw = subprocess.check_output(["/bin/ps", "-o", "time=", "-p", str(pid)], text=True).strip()
    value = 0.0
    for component in raw.split(":"):
        value = value * 60 + float(component)
    return value


def sample(case: str, home: Path, fixture: Path, args, *, long: bool) -> dict[str, Any]:
    home.mkdir(parents=True, exist_ok=True)
    for sub in ("config", "data", "state", "cache"):
        (home / sub).mkdir(exist_ok=True)
    library = args.official if case == "official" else args.patched
    setup = config(
        "bash" if case == "readline" else "flyline-minimal", Path("/usr/bin"), library, home
    )
    if case != "readline":
        setup += "flyline suggestions --use-flycomp false\nflyline history --backend bash\n"
    if case == "patched":
        setup += "flyline key --vim-mode true\n"
    rc = home / "rc.sh"
    rc.write_text(setup)
    session = Session(
        [str(args.bash), "--noprofile", "--rcfile", str(rc), "-i"],
        environment(home, Path("/usr/bin")),
        fixture,
    )
    result: dict[str, Any] = {"case": case}
    try:
        session.send(b"printf '\\036READY\\037\\n'\r")
        session.expect(READY, raw=True)
        result["startup_ms"] = (time.perf_counter() - session.started) * 1000
        session.expect(PROMPT)
        session.quiet(0.05)
        result["single_key_ms"] = []
        for i in range(3):
            token = f"NATIVE_KEY_{i}".encode()
            session.exchange(b": " + token, token)
            result["single_key_ms"].append(session.exchange(b"X", token + b"X"))
            session.clear()
        result["file_tab_ms"] = session.exchange(b"cat fixture_uni\t", b"fixture_unique.txt")
        session.clear()
        if case in ("readline", "patched"):
            session.exchange(b": VIINSERT", b"VIINSERT")
            session.send(b"\x1b")
            session.quiet(0.12)
            session.send(b"A")
            session.quiet(0.02)
            result["vi_insert_key_ms"] = session.exchange(b"X", b"VIINSERTX")
            session.clear()
        if long:
            start = time.perf_counter()
            session.send(b"\x1b[200~: " + b"x" * 4096 + b" PASTE_END\x1b[201~")
            session.expect(b"PASTE_END")
            result["bracketed_paste_ms"] = (time.perf_counter() - start) * 1000
            # A line longer than the viewport may leave Readline's prompt above
            # the emulated screen after Ctrl-U. Cancel and synchronize on actual
            # command output instead of mistaking that display limit for failure.
            session.send(b"\x03")
            session.quiet(0.03)
            session.send(b"printf '\\036CLEARED\\037\\n'\r")
            session.expect(b"\x1eCLEARED\x1f", raw=True)
            session.expect(PROMPT)
        session.quiet(0.15)
        result["idle_rss_mib"] = (
            int(
                subprocess.check_output(
                    ["/bin/ps", "-o", "rss=", "-p", str(session.pid)], text=True
                )
            )
            / 1024
        )
        before = process_cpu(session.pid)
        start = time.perf_counter()
        session.quiet(1)
        elapsed = time.perf_counter() - start
        result["idle_cpu_percent"] = (process_cpu(session.pid) - before) / elapsed * 100
        result["passed"] = True
    except (RuntimeError, OSError, subprocess.SubprocessError) as exc:
        result.update(passed=False, error=str(exc)[:600])
    finally:
        result["resources"] = session.close()
        if not result["passed"] or args.round == args.warmup:
            (args.output / f"{case}-{args.round}-{args.cache}.txt").write_text(
                json.dumps(session.transcript.decode(errors="replace")) + "\n"
            )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("bash", "official", "patched", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=10)
    parser.add_argument("--warmup", type=int, default=2)
    args = parser.parse_args()
    if args.iterations < 3 or args.warmup < 0:
        parser.error("Use at least three measured rounds and nonnegative warmup")
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "budgets.json").write_text(json.dumps(BUDGETS, indent=2) + "\n")
    samples = []
    with tempfile.TemporaryDirectory(prefix="flyline-native-bench-") as directory:
        root = Path(directory)
        fixture = root / "fixture"
        fixture.mkdir()
        (fixture / "fixture_unique.txt").touch()
        rng = random.Random(20261108)
        for round in range(args.iterations + args.warmup):
            order = ["readline", "official", "patched"]
            rng.shuffle(order)
            for case in order:
                for cache in ("fresh", "warm"):
                    args.round, args.cache = round, cache
                    home = root / case / (str(round) if cache == "fresh" else "warm")
                    result = sample(
                        case, home, fixture, args, long=args.warmup <= round < args.warmup + 2
                    )
                    result.update(round=round, cache=cache, warmup=round < args.warmup)
                    samples.append(result)
                    (args.output / "samples.json").write_text(json.dumps(samples, indent=2) + "\n")
                    print(f"round={round} {case}/{cache} passed={result['passed']}", flush=True)
                    if not result["passed"]:
                        return 1
    summaries = {}
    for case in ("readline", "official", "patched"):
        for cache in ("fresh", "warm"):
            selected = [
                s for s in samples if s["case"] == case and s["cache"] == cache and not s["warmup"]
            ]
            metrics = {}
            for name in (
                "startup_ms",
                "file_tab_ms",
                "vi_insert_key_ms",
                "idle_rss_mib",
                "idle_cpu_percent",
                "bracketed_paste_ms",
            ):
                values = [s[name] for s in selected if name in s]
                if values:
                    metrics[name] = describe(values)
            metrics["single_key_ms"] = describe([v for s in selected for v in s["single_key_ms"]])
            summaries[f"{case}/{cache}"] = metrics
    checks = {}
    for cache in ("fresh", "warm"):
        base, patch = summaries[f"readline/{cache}"], summaries[f"patched/{cache}"]
        checks[cache] = {
            "startup_median": patch["startup_ms"]["median"] - base["startup_ms"]["median"]
            <= BUDGETS["startup_median_over_readline_ms"],
            "startup_p95": patch["startup_ms"]["p95"] - base["startup_ms"]["p95"]
            <= BUDGETS["startup_p95_over_readline_ms"],
            "key_median": patch["single_key_ms"]["median"] <= BUDGETS["single_key_median_ms"],
            "key_p95": patch["single_key_ms"]["p95"] <= BUDGETS["single_key_p95_ms"],
            "vi_insert_key_p95": patch["vi_insert_key_ms"]["p95"] <= BUDGETS["single_key_p95_ms"],
            "rss": patch["idle_rss_mib"]["p95"] - base["idle_rss_mib"]["p95"]
            <= BUDGETS["extra_idle_rss_mib"],
            "file_tab_median": patch["file_tab_ms"]["median"] <= BUDGETS["file_tab_median_ms"],
            "file_tab_p95": patch["file_tab_ms"]["p95"] <= BUDGETS["file_tab_p95_ms"],
            "paste": patch["bracketed_paste_ms"]["p95"] <= BUDGETS["bracketed_paste_p95_ms"],
            "idle_cpu": patch["idle_cpu_percent"]["p95"] <= BUDGETS["idle_cpu_percent_of_one_core"],
        }
    report = {
        "platform": platform.platform(),
        "official_sha256": digest(args.official),
        "patched_sha256": digest(args.patched),
        "script_sha256": digest(Path(__file__)),
        "summaries": summaries,
        "budgets": BUDGETS,
        "checks": checks,
        "passed": all(all(c.values()) for c in checks.values()),
    }
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
