"""Pinned archive + seven explicit runtime paths, with a complete materialization gate."""

from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import stat
import subprocess
import tarfile
from pathlib import Path

from harness import BASE_SHA, HERE, digest, fingerprint

REPO = HERE.parents[2]
BASELINE = Path("/private/tmp/remote-ssh-welcome-baseline-r1")
CANDIDATE = Path("/private/tmp/remote-ssh-welcome-candidate-r1")
ALLOWLIST = {
    "shell/welcome.lib.sh": 0o644,
    "shell/welcome/runner.sh": 0o644,
    "shell/welcome/bundled.sh": 0o644,
    "shell/welcome/bundled-runner.sh": 0o755,
    "shell/welcome.d/00-remote-ssh.sh": 0o755,
    "shell/welcome.d/10-hw.sh": 0o755,
    "shell/welcome.d/20-sw.sh": 0o755,
}


def manifest(root: Path) -> list[dict]:
    rows = []
    for path in sorted(root.rglob("*")):
        mode = path.lstat().st_mode
        row = {"path": str(path.relative_to(root)), "mode": oct(stat.S_IMODE(mode))}
        if stat.S_ISLNK(mode):
            row.update({"kind": "symlink", "target": os.readlink(path)})
        elif stat.S_ISDIR(mode):
            row["kind"] = "directory"
        elif stat.S_ISREG(mode):
            row.update({"kind": "file", "sha256": digest(path.read_bytes())})
        else:
            row["kind"] = "other"
        rows.append(row)
    return rows


def differences(left: list[dict], right: list[dict]) -> list[dict]:
    a = {r["path"]: r for r in left}
    b = {r["path"]: r for r in right}
    return [
        {"path": path, "baseline": a.get(path), "candidate": b.get(path)}
        for path in sorted(a.keys() | b.keys())
        if a.get(path) != b.get(path)
    ]


def frozen_inputs() -> dict:
    metadata = json.loads((HERE / "baseline-before-runtime.metadata.json").read_text())
    expected = {
        "harness.py": metadata["harness_sha256"],
        "fixtures.json": metadata["fixtures_sha256"],
        **metadata["frozen_bench"],
    }
    for line in (HERE / "baseline-screens.jsonl").read_text().splitlines():
        row = json.loads(line)
        expected[f"screens/{row['bash']}-{row['fixture']}-{row['workload']}.txt"] = row[
            "output_sha256"
        ]
    assert len([key for key in expected if key.startswith("screens/")]) == 12
    for path, expected_hash in expected.items():
        assert digest((HERE / path).read_bytes()) == expected_hash, path
    return expected


def main() -> None:
    frozen = frozen_inputs()
    preserved_names = [
        "candidate-r0-frozen.json",
        "candidate-r0-runtime.patch",
        "paired-r0-attempt-1.jsonl",
        "paired-r0-attempt-1.metadata.json",
        "paired-r0-attempt-1.log",
        "execution-trace.json",
        "trace-review.json",
        "trace.py",
        "focused-root-unsandboxed.log",
    ]
    preserved_names.extend(str(p.relative_to(HERE)) for p in HERE.glob("trace-*.txt"))
    preserved = {name: digest((HERE / name).read_bytes()) for name in preserved_names}
    assert len((HERE / "paired-r0-attempt-1.jsonl").read_text().splitlines()) == 139
    accounting = {
        "attempt": "R0 first outside-sandbox paired run",
        "accepted_for_performance": False,
        "successful_retained_records": 139,
        "rejected_sample": {
            "bash": "3.2",
            "fixture": "actionable",
            "workload": "pty",
            "version": "candidate",
            "batch": 1,
            "warmup": True,
            "index": -3,
            "ready_ms": None,
            "total_ms": None,
            "timing_availability": "unavailable: frozen sample() asserted before returning/writing its record",
            "screen_log": "paired-r0-attempt-1.log",
            "previous_checks_passed": [
                "returncode=0",
                "timeout=false",
                "ready marker present",
                "output below 128 KiB",
            ],
        },
        "preserved_artifact_sha256": preserved,
    }
    (HERE / "r1-rejected-r0-accounting.json").write_text(json.dumps(accounting, indent=2) + "\n")

    old_base = json.loads((HERE / "paired-r0-attempt-1.metadata.json").read_text())["baseline"][
        "files"
    ]
    old_candidate = json.loads((HERE / "candidate-r0-frozen.json").read_text())["fingerprint"][
        "files"
    ]
    old_delta = differences(old_base, old_candidate)
    unauthorized = [row for row in old_delta if row["path"] not in ALLOWLIST]
    assert [row["path"] for row in unauthorized] == ["dots/git/user.local", "tools/defs/atuin.sh"]

    assert not BASELINE.exists() and not CANDIDATE.exists(), (
        "do not replace retained evidence trees"
    )
    archive = subprocess.check_output(["git", "archive", "--format=tar", BASE_SHA], cwd=REPO)
    for target in (BASELINE, CANDIDATE):
        target.mkdir()
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            tar.extractall(target, filter="data")
    baseline_manifest = manifest(BASELINE)
    existing_baseline = Path("/private/tmp/remote-ssh-welcome-baseline-39226a2")
    assert manifest(existing_baseline) == baseline_manifest, (
        "the earlier baseline differs from fresh pinned archive"
    )

    sources = []
    old_sources = {r["path"]: r for r in old_candidate}
    for path, expected_mode in ALLOWLIST.items():
        source = REPO / path
        assert stat.S_IMODE(source.stat().st_mode) == expected_mode, path
        assert not source.is_symlink()
        if path != "shell/welcome/bundled-runner.sh":
            assert digest(source.read_bytes()) == old_sources[path]["sha256"], path
        shutil.copy2(source, CANDIDATE / path)
        (CANDIDATE / path).chmod(expected_mode)
        assert (CANDIDATE / path).read_bytes() == source.read_bytes()
        sources.append(
            {"path": path, "sha256": digest(source.read_bytes()), "mode": oct(expected_mode)}
        )

    candidate_manifest = manifest(CANDIDATE)
    delta = differences(baseline_manifest, candidate_manifest)
    assert {row["path"] for row in delta} == set(ALLOWLIST)
    for tree in (BASELINE, CANDIDATE):
        assert not (tree / "dots/git/user.local").exists()
        assert stat.S_IMODE((tree / "tools/defs/atuin.sh").stat().st_mode) == 0o644
    assert fingerprint(BASELINE)["files"] == old_base
    gate = {
        "baseline_sha": BASE_SHA,
        "archive_sha256": hashlib.sha256(archive).hexdigest(),
        "archive_command": ["git", "archive", "--format=tar", BASE_SHA],
        "baseline_path": str(BASELINE),
        "candidate_path": str(CANDIDATE),
        "overlay": sources,
        "r0_gate_red": {"unauthorized_differences": unauthorized},
        "r1_gate_green": {
            "only_authorized_seven_path_delta": delta,
            "all_other_paths_kinds_links_bytes_modes_identical": True,
        },
        "baseline_complete_manifest": baseline_manifest,
        "candidate_complete_manifest": candidate_manifest,
        "baseline_runtime_fingerprint": fingerprint(BASELINE),
        "candidate_runtime_fingerprint": fingerprint(CANDIDATE),
        "frozen_inputs": frozen,
        "workspace_private_files": "untouched; never read or copied by this materializer",
        "working_seven_path_source_verified": True,
    }
    (HERE / "candidate-r1-frozen.json").write_text(json.dumps(gate, indent=2) + "\n")
    (HERE / "candidate-r1-runtime.patch").write_text(
        subprocess.check_output(["git", "diff", "--", *ALLOWLIST], cwd=REPO, text=True)
    )
    assert frozen_inputs() == frozen
    assert {name: digest((HERE / name).read_bytes()) for name in preserved_names} == preserved
    print("R0 gate RED: unauthorized private config and Atuin definition mode")
    print("R1 gate GREEN: exactly seven authorized source/mode differences")
    print("R1 candidate runtime aggregate:", gate["candidate_runtime_fingerprint"]["aggregate"])
    print("Frozen timed harness, fixtures, benchmark sources and 12 screens: unchanged")


if __name__ == "__main__":
    main()
