#!/usr/bin/env python3
"""Validate every final R1 sample and recompute statistics independently."""

from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import statistics

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "welcome-measurements"
MARKER = "__WELCOME_FIRST_COMMAND_READY__"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stats(values: list[float]) -> dict:
    values = sorted(values)
    quartiles = statistics.quantiles(values, n=4, method="inclusive")
    median = statistics.median(values)
    return {"median": median, "p95": values[18], "min": values[0], "max": values[-1],
            "iqr": quartiles[2] - quartiles[0],
            "mad": statistics.median(abs(x - median) for x in values)}


def main() -> None:
    raw = DATA / "paired-r1.jsonl"
    rows = [json.loads(line) for line in raw.read_text().splitlines()]
    expected_order = []
    for batch in (1, 2):
        cells = [(bash, fixture, workload) for bash in ("3.2", "5.3")
                 for fixture in ("healthy", "actionable") for workload in ("isolated", "pty")]
        if batch == 1:
            cells += [(bash, "healthy", workload) for bash in ("3.2", "5.3")
                      for workload in ("bash-baseline", "remote-ssh-min")]
        for bash, fixture, workload in cells:
            for index in range(23):
                versions = ("candidate", "baseline") if index % 2 else ("baseline", "candidate")
                for version in versions:
                    expected_order.append((batch, bash, fixture, workload, index - 3, version))
    actual_order = [(r["batch"], r["bash"], r["fixture"], r["workload"], r["index"], r["version"])
                    for r in rows]
    assert actual_order == expected_order and len(rows) == 920
    assert len({r["sample_id"] for r in rows}) == 920
    groups = defaultdict(list)
    sizes = Counter()
    for row in rows:
        assert row["returncode"] == 0 and row["timed_out"] is False
        assert row["ready_ms"] > 0 and row["total_ms"] >= row["ready_ms"]
        assert row["warmup"] == (row["index"] < 0)
        assert row["stderr"] == "" and row["complete_output_asserted"] is True
        payload = row["output_tail"].encode()
        expected = DATA / "screens" / f"{row['bash']}-{row['fixture']}-{row['workload']}.txt"
        assert payload == expected.read_bytes()
        assert len(payload) == row["output_bytes"] < 128 * 1024
        assert hashlib.sha256(payload).hexdigest() == row["output_sha256"]
        assert payload.count(MARKER.encode()) == 1
        key = (row["batch"], row["bash"], row["fixture"], row["workload"], row["version"])
        groups[key].append(row)
        sizes["warmup" if row["warmup"] else "measured"] += 1
    comparisons = []
    published = json.loads((DATA / "paired-r1-summary.json").read_text())
    for key, entries in groups.items():
        assert len(entries) == 23
        measured = [r for r in entries if not r["warmup"]]
        assert len(measured) == 20
        if key[-1] != "baseline":
            continue
        other = [r for r in groups[key[:-1] + ("candidate",)] if not r["warmup"]]
        comparison = dict(zip(("batch", "bash", "fixture", "workload"), key[:-1], strict=True))
        comparison["n_per_version"] = 20
        comparison["principal"] = key[3] in {"isolated", "pty"}
        for measure in ("ready_ms", "total_ms"):
            baseline_stats = stats([r[measure] for r in measured])
            candidate_stats = stats([r[measure] for r in other])
            paired = [next(q[measure] for q in other if q["index"] == r["index"]) - r[measure]
                      for r in measured]
            delta = candidate_stats["median"] - baseline_stats["median"]
            comparison[measure] = {"baseline": baseline_stats, "candidate": candidate_stats,
                                   "delta_ms": delta, "delta_percent": delta / baseline_stats["median"] * 100,
                                   "p95_delta_ms": candidate_stats["p95"] - baseline_stats["p95"],
                                   "paired_delta_median": statistics.median(paired),
                                   "paired_candidate_lower_count": sum(x < 0 for x in paired)}
            for version, recomputed in (("baseline", baseline_stats), ("candidate", candidate_stats)):
                item = next(r for r in published if all(r[k] == comparison[k]
                            for k in ("batch", "bash", "fixture", "workload")) and r["version"] == version)
                assert item["n"] == 20
                assert all(item[measure][k] == recomputed[k] for k in ("median", "p95", "min", "max"))
        comparisons.append(comparison)
    assert len(comparisons) == 20
    principal = [r for r in comparisons if r["principal"]]
    assert len(principal) == 16 and all(r["ready_ms"]["delta_ms"] < 0 for r in principal)
    metadata = json.loads((DATA / "paired-r1.metadata.json").read_text())
    frozen = json.loads((DATA / "candidate-r1-frozen.json").read_text())
    assert all(metadata[k] == frozen[f"{k}_runtime_fingerprint"] for k in ("baseline", "candidate"))
    assert metadata["harness_sha256"] == sha(DATA / "harness.py")
    assert metadata["fixtures_sha256"] == sha(DATA / "fixtures.json")
    trace_dir = DATA / "r1-trace"
    trace = json.loads((trace_dir / "execution-trace.json").read_text())
    assert trace["runtime_fingerprint"] == metadata["candidate"]["aggregate"]
    trace_checks = []
    for row in trace["records"]:
        assert row["returncode"] == 0
        paths = row["executions"]
        assert len(paths) == (2 if row["route"] == "worker-and-user" else 4)
        assert paths[-1].endswith("/50-trace-user.sh")
        if row["route"] == "worker-and-user":
            assert paths[0].endswith("/welcome/bundled-runner.sh")
            raw_trace = trace_dir / row["stderr_path"]
            text = raw_trace.read_text()
            counts = {"library_loads": len(re.findall(r"^\++ \. [^\n]*welcome\.lib\.sh$", text, re.M)),
                      "captures": len(re.findall(r"^\++ remote_ssh_welcome_run_module ", text, re.M)),
                      "dispatches": len(re.findall(r"^\++ remote_ssh_welcome_bundled_render ", text, re.M)),
                      "cleanup_calls": len(re.findall(r"^\++ remote_ssh_welcome_remove_temp_file ", text, re.M))}
            assert counts == {"library_loads": 1, "captures": 3, "dispatches": 3, "cleanup_calls": 3}
            trace_checks.append({"bash": row["bash"], "counts": counts, "sha256": sha(raw_trace)})
        else:
            assert [Path(p).name for p in paths[:-1]] == ["00-remote-ssh.sh", "10-hw.sh", "20-sw.sh"]
    smoke = json.loads((DATA / "r1-detached-smoke.metadata.json").read_text())
    assert smoke["command"] == ["just", "smoke"] and smoke["returncode"] == 0
    assert smoke["start_new_session"] is True and smoke["stdin"] == "/dev/null"
    assert smoke["raw_log_sha256"] == sha(DATA / "r1-detached-smoke.log")
    assert smoke["driver_sha256"] == sha(DATA / "run-verified-checks.py")
    assert smoke["runtime_test_freeze_sha256"] == sha(DATA / "r1-runtime-tests-final-freeze.json")
    assert "862 passed, 58 skipped in 310.60s" in (DATA / "r1-detached-smoke.log").read_text()
    result = {"status": "PASS", "records": len(rows), "sample_counts": dict(sizes),
              "all_complete_screens_hashes_statuses_timeouts_verified": True,
              "exact_3_warmups_20_measured_alternating_order_verified": True,
              "all_16_principal_ready_medians_lower": True,
              "published_statistics_independently_recomputed": True,
              "source_fingerprint": metadata["candidate"]["aggregate"],
              "raw_jsonl_sha256": sha(raw), "trace_checks": trace_checks,
              "smoke": smoke, "comparisons": comparisons}
    (HERE / "r1-final-evidence-review.json").write_text(json.dumps(result, indent=2) + "\n")
    print("PASS 920 records, 20 comparison cells, full outputs/order/status/source/log checks")
    for row in comparisons:
        ready = row["ready_ms"]
        print(row["batch"], row["bash"], row["fixture"], row["workload"],
              f"ready delta {ready['delta_ms']:.3f} ms ({ready['delta_percent']:.2f}%), "
              f"p95 delta {ready['p95_delta_ms']:.3f} ms")


if __name__ == "__main__":
    main()
