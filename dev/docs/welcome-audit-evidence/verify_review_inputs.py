#!/usr/bin/env python3
"""Independent read-only verification of reviewed R1 source and fixed inputs."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import subprocess

from review_snapshots import RUNTIME_DIRS, manifest

REPO = Path(__file__).resolve().parents[3]
EVIDENCE = REPO / "dev" / "docs" / "welcome-measurements"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def runtime_fingerprint(tree: Path) -> dict:
    rows = []
    for dirname in RUNTIME_DIRS:
        for path in sorted((tree / dirname).rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                rows.append({"path": str(path.relative_to(tree)),
                             "mode": oct(path.stat().st_mode & 0o777), "sha256": sha(path)})
    return {"aggregate": hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest(),
            "files": rows}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    frozen = json.loads((EVIDENCE / "candidate-r1-frozen.json").read_text())
    baseline, candidate = Path(frozen["baseline_path"]), Path(frozen["candidate_path"])
    for name, tree in (("baseline", baseline), ("candidate", candidate)):
        expected = {}
        for row in frozen[f"{name}_complete_manifest"]:
            entry = {k: v for k, v in row.items() if k not in {"path", "kind"}}
            entry["type"] = row["kind"]
            expected[row["path"]] = entry
        assert manifest(tree, all_paths=True)["files"] == expected, name
        assert runtime_fingerprint(tree) == frozen[f"{name}_runtime_fingerprint"], name
    archive = subprocess.check_output(["git", "archive", "--format=tar", frozen["baseline_sha"]],
                                      cwd=REPO)
    archive_hash = hashlib.sha256(archive).hexdigest()
    assert archive_hash == frozen["archive_sha256"]
    fixed = json.loads((EVIDENCE / "baseline-before-runtime.metadata.json").read_text())
    expected_inputs = {"harness.py": fixed["harness_sha256"],
                       "fixtures.json": fixed["fixtures_sha256"], **fixed["frozen_bench"]}
    for line in (EVIDENCE / "baseline-screens.jsonl").read_text().splitlines():
        row = json.loads(line)
        expected_inputs[f"screens/{row['bash']}-{row['fixture']}-{row['workload']}.txt"] = row["output_sha256"]
    assert expected_inputs == frozen["frozen_inputs"]
    assert all(sha(EVIDENCE / path) == expected for path, expected in expected_inputs.items())
    final = json.loads((EVIDENCE / "r1-runtime-tests-final-freeze.json").read_text())
    for row in final["runtime_and_test_source"]:
        actual = REPO / row["path"]
        assert sha(actual) == row["sha256"] and oct(actual.stat().st_mode & 0o777) == row["mode"]
    accounting = json.loads((EVIDENCE / "r1-rejected-r0-accounting.json").read_text())
    assert all(sha(EVIDENCE / path) == expected
               for path, expected in accounting["preserved_artifact_sha256"].items())
    result = {"status": "PASS", "phase": args.phase, "checked_at": datetime.now(UTC).isoformat(),
              "candidate_runtime_aggregate": frozen["candidate_runtime_fingerprint"]["aggregate"],
              "baseline_runtime_aggregate": frozen["baseline_runtime_fingerprint"]["aggregate"],
              "fresh_pinned_archive_sha256": archive_hash,
              "complete_physical_trees_match_frozen_manifests": True,
              "reviewed_working_runtime_and_test_hashes_modes_match": True,
              "fixed_harness_fixture_bench_12_screens_match_original": True,
              "R0_rejected_artifacts_retained_unchanged": True}
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
