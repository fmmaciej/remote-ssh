from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from bench.model import ScenarioResult


def percentile_nearest_rank(values: Sequence[float], percentile: float) -> float:
    if not values:
        raise ValueError("values must not be empty")
    ordered = sorted(values)
    rank = math.ceil((percentile / 100) * len(ordered))
    index = min(max(rank - 1, 0), len(ordered) - 1)
    return ordered[index]


def series_stats(values: Sequence[float]) -> dict[str, float] | None:
    if not values:
        return None
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        median = ordered[midpoint]
    else:
        median = (ordered[midpoint - 1] + ordered[midpoint]) / 2
    return {
        "median": median,
        "p95": percentile_nearest_rank(ordered, 95),
        "min": ordered[0],
        "max": ordered[-1],
    }


def summarize_result(
    result: ScenarioResult,
    baseline_ready_median: float | None,
) -> dict[str, Any]:
    ok_samples = [sample for sample in result.samples if sample.ok]
    ready_values = [sample.ready_ms for sample in ok_samples if sample.ready_ms is not None]
    total_values = [sample.total_ms for sample in ok_samples]
    ready_stats = series_stats(ready_values)
    total_stats = series_stats(total_values)
    ready_median = None if ready_stats is None else ready_stats["median"]
    ratio = None
    delta = None
    slower_percent = None
    if baseline_ready_median and ready_median is not None:
        ratio = ready_median / baseline_ready_median
        delta = ready_median - baseline_ready_median
        slower_percent = (ratio - 1) * 100

    return {
        "iterations": len(result.samples),
        "failed": len(result.samples) - len(ok_samples),
        "ready_ms": ready_stats,
        "total_ms": total_stats,
        "ratio_ready_vs_baseline": ratio,
        "delta_ready_ms_vs_baseline": delta,
        "slower_ready_percent_vs_baseline": slower_percent,
    }


def baseline_ready_median(results: Sequence[ScenarioResult]) -> float | None:
    for result in results:
        if result.name != "bash-baseline":
            continue
        summary = summarize_result(result, None)
        ready_stats = summary["ready_ms"]
        if ready_stats is None:
            return None
        return ready_stats["median"]
    return None


def fmt_ms(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.1f}"


def fmt_ratio(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.2f}x"


def fmt_percent(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:+.0f}%"
