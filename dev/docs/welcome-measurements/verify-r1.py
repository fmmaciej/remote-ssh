"""Read-only final source, mode and frozen-input checkpoint; never changes runtime."""

from __future__ import annotations

import argparse
import json
import runpy
import stat
from datetime import UTC, datetime

from harness import HERE, digest, fingerprint


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase")
    args = parser.parse_args()
    namespace = runpy.run_path(
        str(HERE / "materialize-r1.py"), run_name="r1_materialization_helpers"
    )
    frozen = json.loads((HERE / "candidate-r1-frozen.json").read_text())
    frozen_inputs = namespace["frozen_inputs"]()
    assert frozen_inputs == frozen["frozen_inputs"]
    for name, tree in (("baseline", namespace["BASELINE"]), ("candidate", namespace["CANDIDATE"])):
        assert namespace["manifest"](tree) == frozen[f"{name}_complete_manifest"]
        assert fingerprint(tree) == frozen[f"{name}_runtime_fingerprint"]
    for row in frozen["overlay"]:
        path = namespace["REPO"] / row["path"]
        assert not path.is_symlink()
        assert digest(path.read_bytes()) == row["sha256"]
        assert oct(stat.S_IMODE(path.stat().st_mode)) == row["mode"]
    r0 = json.loads((HERE / "r1-rejected-r0-accounting.json").read_text())
    for path, expected_hash in r0["preserved_artifact_sha256"].items():
        assert digest((HERE / path).read_bytes()) == expected_hash, path
    for path, expected_hash in frozen_inputs.items():
        assert digest((HERE / "r1-trace" / path).read_bytes()) == expected_hash, path
    assert (HERE / "r1-trace" / "trace.py").read_text() == (HERE / "trace.py").read_text().replace(
        "remote-ssh-welcome-candidate-r0", "remote-ssh-welcome-candidate-r1"
    )
    result = {
        "phase": args.phase,
        "checked_at": datetime.now(UTC).isoformat(),
        "baseline_aggregate": frozen["baseline_runtime_fingerprint"]["aggregate"],
        "candidate_aggregate": frozen["candidate_runtime_fingerprint"]["aggregate"],
        "source_modes_and_full_tree_manifests": "unchanged",
        "reviewed_working_seven_paths": "unchanged",
        "frozen_harness_fixtures_bench_and_12_screens": "unchanged",
        "preserved_R0_artifacts": "unchanged",
        "r1_trace_inputs": "byte-identical; driver changes only candidate path",
    }
    path = HERE / f"r1-checkpoint-{args.phase}.json"
    assert not path.exists(), "do not overwrite prior checkpoints"
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
