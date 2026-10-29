"""Independent read-only fingerprints and in-memory semantic assertion probes."""

import ast
import difflib
import hashlib
import json
import shlex
import subprocess
import tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_manifest(path, nested=False):
    expected = json.loads(path.read_text())
    if nested:
        expected = expected["sha256"]
    actual = {name: digest(ROOT / name) for name in expected}
    return {"count": len(expected), "mismatches": [n for n in expected if expected[n] != actual[n]], "actual": actual}


manifest = ROOT / "dev/docs/install-cli-implementation-evidence/r1/final/source-hashes.json"
r0 = json.loads((ROOT / "dev/docs/install-cli-implementation-evidence/final-source-hashes.json").read_text())
r1 = json.loads(manifest.read_text())
before_path = ROOT / "dev/docs/install-cli-implementation-evidence/r1/test_guide.before.py"
current_path = ROOT / "dev/tests/test_guide.py"
before = before_path.read_text()
current = current_path.read_text()
name = "test_remote_ssh_guide_supports_post_install_section"


def function_parts(source):
    node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == name)
    lines = source.splitlines(keepends=True)
    return "".join(lines[: node.lineno - 1]), "".join(lines[node.lineno - 1 : node.end_lineno]), "".join(lines[node.end_lineno :])


old_prefix, _, old_suffix = function_parts(before)
prefix, function_source, suffix = function_parts(current)
assert prefix == old_prefix and suffix == old_suffix
assert digest(before_path) == "d1fe47c4973a78812aa4f6ff56558d33311216dc171bea58a88664fcdf6e83d2"
assert all(r1[n] == h for n, h in r0.items())
format_baseline = (ROOT / "dev/docs/install-cli-implementation-evidence/r1/final/preexisting-format-diff.log").read_text().split("1 file would be reformatted")[0].rstrip()
format_current = (ROOT / "dev/docs/install-cli-implementation-evidence/r1/final/current-format-diff.log").read_text().split("1 file would be reformatted")[0].rstrip()
assert format_baseline == format_current
pre_format = current.replace(
    '    capture_env = {\n        key: value for key, value in isolated_env.env.items() if key not in ("BASH_ENV", "ENV")\n    }',
    '    capture_env = {key: value for key, value in isolated_env.env.items() if key not in ("BASH_ENV", "ENV")}',
    1,
)
initial_manifest = json.loads((ROOT / "dev/docs/install-cli-implementation-evidence/r1/source-hashes.json").read_text())
assert hashlib.sha256(pre_format.encode()).hexdigest() == initial_manifest["dev/tests/test_guide.py"]

def assert_ok(result):
    assert result.returncode == 0, result.stderr


results = []
with tempfile.TemporaryDirectory(prefix="install-cli-r1-audit-") as temporary:
    env = {"HOME": temporary, "PATH": "/usr/bin:/bin", "BASH_ENV": "/must/be/excluded", "ENV": "/must/be/excluded"}
    isolated = SimpleNamespace(env=env)
    for shell in ("/bin/bash", "/opt/homebrew/bin/bash"):
        if not Path(shell).exists():
            continue
        for unusual in (False, True):
            repo = Path(temporary) / ("repo space ' $ ; &" if unusual else "repo")
            expected = str(repo / "shell/rc.sh")
            command = "bash --rcfile " + shlex.quote(expected) + " -i"
            headings = '\n'.join(("Interactive usage", "SSH configuration", "VS Code Remote-SSH terminal profile", "Optional Git and SSH setup", '\"terminal.integrated.defaultProfile.linux\": \"bash + remote-ssh\"'))
            cases = {
                "valid-shell-quoted": (headings + "\n  " + command, True),
                "missing-interactive": (headings + "\n" + command.removesuffix(" -i"), False),
                "wrong-rcfile": (headings + "\nbash --rcfile /wrong/rc.sh -i", False),
                "extra-argument": (headings + "\n" + command + " extra", False),
                "duplicate-command": (headings + "\n" + command + "\n" + command, False),
                "new-marker": (headings + "\n" + command + "\n@INTERACTIVE_COMMAND@", False),
                "old-marker": (headings + "\n" + command + "\n@INSTALL_DIR@", False),
                "missing-heading": (headings.replace("Interactive usage", "") + "\n" + command, False),
            }
            if unusual:
                cases["split-rcfile"] = (headings + "\nbash --rcfile " + expected + " -i", False)
            else:
                cases["valid-unquoted"] = (headings + "\nbash --rcfile " + expected + " -i", True)
                cases["valid-doublequoted"] = (headings + '\nbash --rcfile "' + expected + '" -i', True)
            for label, (output, should_pass) in cases.items():
                commands_seen = []

                def run_cmd(args, *, env):
                    assert "BASH_ENV" not in env and "ENV" not in env
                    commands_seen.append(args)
                    return subprocess.run([shell, *args[1:]], env=env, text=True, capture_output=True, timeout=5)

                context = {
                    "run_remote_ssh": lambda *args, **kwargs: subprocess.CompletedProcess([], 0, output, ""),
                    "run_cmd": run_cmd,
                    "assert_ok": assert_ok,
                }
                exec(compile("from __future__ import annotations\n" + function_source, str(current_path), "exec"), context)
                passed = True
                try:
                    context[name](repo, isolated)
                except AssertionError:
                    passed = False
                assert passed == should_pass, (shell, unusual, label, passed)
                results.append({"bash": shell, "unusual_path": unusual, "case": label, "expected_pass": should_pass, "observed_pass": passed})

immutable_names = (
    "install-cli-implementation-plan.md", "install-cli-plan-audit.md",
    "install-cli-implementation-addendum.md", "install-cli-addendum-audit.md",
    "install-cli-repair-plan.md", "install-cli-implementation-audit.md",
)
preserved_names = (
    "install-cli-implementation-evidence/smoke-final.log",
    "install-cli-implementation-evidence/smoke-final-result.json",
    "install-cli-implementation-evidence/final-source-hashes.json",
    "install-cli-implementation-audit-evidence/guide-reproduction.json",
    "install-cli-coordinator-evidence/r0-audit-snapshot.md",
)
report = {
    "r1_manifest_sha256": digest(manifest),
    "sources": check_manifest(manifest),
    "protected": check_manifest(ROOT / "dev/docs/install-cli-planning-evidence/protected-before-implementation.json", True),
    "all_12_r0_sources_unchanged_in_r1": all(r1[n] == h for n, h in r0.items()),
    "only_repaired_function_changed": prefix == old_prefix and suffix == old_suffix,
    "baseline_and_final_formatter_hunks_identical": format_baseline == format_current,
    "finalization_only_formats_capture_env_comprehension": hashlib.sha256(pre_format.encode()).hexdigest() == initial_manifest["dev/tests/test_guide.py"],
    "pre_repair_guide_sha256": digest(before_path),
    "immutable_artifacts": {n: digest(ROOT / "dev/docs" / n) for n in immutable_names},
    "retained_r0_evidence": {n: digest(ROOT / "dev/docs" / n) for n in preserved_names},
    "r0_audit_matches_preserved_snapshot": (ROOT / "dev/docs/install-cli-implementation-audit.md").read_bytes() == (ROOT / "dev/docs/install-cli-coordinator-evidence/r0-audit-snapshot.md").read_bytes(),
    "semantic_probes": results,
}
assert not report["sources"]["mismatches"] and not report["protected"]["mismatches"]
(OUT / "independent-checks.json").write_text(json.dumps(report, indent=2) + "\n")
(OUT / "independent-repair.diff").write_text("".join(difflib.unified_diff(before.splitlines(True), current.splitlines(True), fromfile="pre-R1/test_guide.py", tofile="R1/test_guide.py")))
print(json.dumps({"sources": report["sources"]["count"], "protected": report["protected"]["count"], "semantic_probes": len(results), "all_matched": True}))
