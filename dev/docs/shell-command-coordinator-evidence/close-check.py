"""Final coordinator fingerprint and evidence closure; no product mutations."""
import hashlib
import json
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[3]
folder = Path(__file__).resolve().parent

def digest(path):
    return hashlib.sha256((root / path).read_bytes()).hexdigest()

protected = json.loads((root / "dev/docs/shell-command-planning-evidence/protected-before-implementation.json").read_text())["sha256"]
candidate = json.loads((root / "dev/docs/shell-command-implementation-evidence/final-master-close-source-hashes.json").read_text())["sha256"]
checks = {}
for name, expected in (("protected", protected), ("candidate", candidate)):
    checks[name] = dict(count=len(expected), mismatches=[p for p, h in expected.items() if digest(p) != h])
checks["plan_sha256"] = digest("dev/docs/shell-command-implementation-plan.md")
checks["plan_audit_sha256"] = digest("dev/docs/shell-command-plan-audit.md")
checks["implementation_audit_sha256"] = digest("dev/docs/shell-command-implementation-audit.md")
checks["runs"] = {}
for name in ("focused-final", "smoke"):
    result = json.loads((folder / (name + "-result.json")).read_text())
    checks["runs"][name] = {key: result[key] for key in ("exit_code", "timed_out", "hashes_match", "survivors")}
checks["diff_check_exit_code"] = subprocess.run(["git", "diff", "--check"], cwd=root, check=False).returncode
(folder / "closure-check.json").write_text(json.dumps(checks, indent=2)+"\n")
print(json.dumps(checks, indent=2))
assert not any(checks[name]["mismatches"] for name in ("protected", "candidate"))
assert checks["diff_check_exit_code"] == 0
