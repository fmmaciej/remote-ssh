from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from bench.model import Sample, ScenarioResult
from bench.stats import baseline_ready_median, fmt_ms, fmt_percent, fmt_ratio, summarize_result


def sample_to_json(sample: Sample) -> dict[str, Any]:
    data: dict[str, Any] = {
        "ready_ms": sample.ready_ms,
        "total_ms": sample.total_ms,
        "returncode": sample.returncode,
        "timed_out": sample.timed_out,
    }
    if not sample.ok:
        data["output_tail"] = sample.output_tail
    return data


def result_to_json(result: ScenarioResult, baseline_median: float | None) -> dict[str, Any]:
    return {
        "name": result.name,
        "description": result.description,
        "source": result.source,
        "samples": [sample_to_json(sample) for sample in result.samples],
        "summary": summarize_result(result, baseline_median),
    }


def report_json(
    results: Sequence[ScenarioResult],
    current_repo: Path,
    iterations: int,
    warmup: int,
    timeout_seconds: float,
) -> dict[str, Any]:
    baseline_median = baseline_ready_median(results)
    return {
        "repo": str(current_repo),
        "iterations": iterations,
        "warmup": warmup,
        "timeout_seconds": timeout_seconds,
        "scenarios": [result_to_json(result, baseline_median) for result in results],
    }


def print_table(results: Sequence[ScenarioResult], baseline_median: float | None) -> None:
    print("Shell startup benchmark (local PTY)")
    print()
    print(
        "Scenario              n  fail  ready med  ready p95  ready min  "
        "ready max  delta   ratio  slower  total med"
    )
    print(
        "-------------------- -- ----- ---------- ---------- ---------- "
        "---------- ------- ------ ------- ---------"
    )
    for result in results:
        summary = summarize_result(result, baseline_median)
        ready_stats = summary["ready_ms"] or {}
        total_stats = summary["total_ms"] or {}
        print(
            f"{result.name:<20} "
            f"{summary['iterations']:>2} "
            f"{summary['failed']:>5} "
            f"{fmt_ms(ready_stats.get('median')):>10} "
            f"{fmt_ms(ready_stats.get('p95')):>10} "
            f"{fmt_ms(ready_stats.get('min')):>10} "
            f"{fmt_ms(ready_stats.get('max')):>10} "
            f"{fmt_ms(summary['delta_ready_ms_vs_baseline']):>7} "
            f"{fmt_ratio(summary['ratio_ready_vs_baseline']):>6} "
            f"{fmt_percent(summary['slower_ready_percent_vs_baseline']):>7} "
            f"{fmt_ms(total_stats.get('median')):>9}"
        )
