"""Read-only R0 implementation audit fingerprint and evidence checks."""

import difflib
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
IMPL = ROOT / "dev/docs/shell-command-implementation-evidence"
COORD = ROOT / "dev/docs/shell-command-coordinator-evidence"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


protected = json.loads((ROOT / "dev/docs/shell-command-planning-evidence/protected-before-implementation.json").read_text())
candidate = json.loads((IMPL / "final-master-close-source-hashes.json").read_text())["sha256"]
baseline = json.loads((IMPL / "baseline.json").read_text())["sha256"]
checks = {
    "plan_sha256": digest(ROOT / "dev/docs/shell-command-implementation-plan.md"),
    "plan_audit_sha256": digest(ROOT / "dev/docs/shell-command-plan-audit.md"),
    "protected_count": len(protected["sha256"]),
    "protected_mismatches": [p for p, h in protected["sha256"].items() if digest(ROOT / p) != h],
    "candidate_count": len(candidate),
    "candidate_mismatches": [p for p, h in candidate.items() if digest(ROOT / p) != h],
    "scope_matches_candidate": set(candidate) == set(protected["owned_source_paths"]),
    "baseline_copy_mismatches": [],
    "baseline_outside_scope_changes": [],
    "runs": {},
}
feature_diff = ""
for path in candidate:
    old_path = IMPL / "baseline" / path
    if path in baseline and digest(old_path) != baseline[path]:
        checks["baseline_copy_mismatches"].append(path)
    before = old_path.read_text().splitlines(keepends=True) if old_path.is_file() else []
    after = (ROOT / path).read_text().splitlines(keepends=True)
    feature_diff += "".join(difflib.unified_diff(before, after, fromfile="baseline/" + path, tofile="candidate/" + path))
checks["feature_diff_matches_frozen"] = feature_diff == (IMPL / "final-master-close-source.diff").read_text()
for path, old_hash in baseline.items():
    if path not in candidate and digest(ROOT / path) != old_hash:
        checks["baseline_outside_scope_changes"].append(path)
old_bin = (IMPL / "baseline/bin/remote-ssh").read_text()
new_bin = (ROOT / "bin/remote-ssh").read_text()
checks["bootstrap_byte_preserved"] = old_bin.split("remote_ssh_usage()", 1)[0] == new_bin.split("remote_ssh_usage()", 1)[0]
for name in ("focused-final", "smoke"):
    path = COORD / (name + "-result.json")
    if not path.is_file():
        checks["runs"][name] = {"complete": False}
        continue
    result = json.loads(path.read_text())
    summary = {key: value for key, value in result.items() if not key.startswith("source_hashes")}
    expected = protected["sha256"] | candidate
    summary.update(
        complete=True,
        raw_before_equals_frozen=result["source_hashes_before"] == expected,
        raw_after_equals_frozen=result["source_hashes_after"] == expected,
        log_sha256=digest(COORD / (name + ".log")),
        result_sha256=digest(path),
    )
    checks["runs"][name] = summary
(HERE / "independent-evidence-check.json").write_text(json.dumps(checks, indent=2) + "\n")
print(json.dumps(checks, indent=2))
