"""Capture independent Bash contexts through a dedicated xtrace descriptor."""

from __future__ import annotations

import hashlib
import io
import json
import re
import subprocess
import tarfile
import tempfile
from pathlib import Path

import paired_measure as paired


def main() -> None:
    archive = subprocess.check_output(["git", "archive", "--format=tar", "HEAD"], cwd=paired.REPO)
    result = {
        "method": "Bash 5.3 xtrace to FD 9; stderr suppression does not hide child contexts",
        "scope": "distinct Bash PIDs observed while sourcing config.lib.sh, loading nine keys, and checking values/markers; not a count of all kernel processes",
        "fixture_sha256": hashlib.sha256(paired.FIXTURE).hexdigest(),
        "variants": {},
    }
    with tempfile.TemporaryDirectory(prefix="config-independent-trace-") as temporary:
        root = Path(temporary)
        for variant in ("before", "after"):
            tree = root / variant
            tree.mkdir()
            with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
                bundle.extractall(tree, filter="data")
            if variant == "after":
                for relative in paired.CHANGED:
                    (tree / relative).write_bytes((paired.REPO / relative).read_bytes())
            env = paired.environment(root / "env" / variant, paired.BASHES[1], paired.FIXTURE)
            trace_file = paired.OUTPUT / f"subshell-trace-{variant}.txt"
            command = "exec 9>\"$2\"\nBASH_XTRACEFD=9\nPS4='+pid=${BASHPID} sub=${BASH_SUBSHELL} '\nset -x\n"
            command += '. "$1/shell/config.lib.sh"\nremote_ssh_config_load\n'
            command += paired.check_script(paired.EXPECTED, set(paired.EXPECTED), True)
            command += "\nset +x\n"
            completed = subprocess.run(
                [
                    paired.BASHES[1],
                    "--noprofile",
                    "--norc",
                    "-c",
                    command,
                    "_",
                    str(tree),
                    str(trace_file),
                ],
                env=env,
                cwd=tree,
                capture_output=True,
                check=True,
                timeout=30,
            )
            if completed.stdout or completed.stderr:
                raise RuntimeError(f"Unexpected output: {completed!r}")
            trace = trace_file.read_bytes()
            contexts = re.findall(rb"^\++pid=(\d+) sub=(\d+) ", trace, flags=re.M)
            result["variants"][variant] = {
                "distinct_bash_pids": len({pid for pid, _ in contexts}),
                "max_subshell_depth": max(int(depth) for _, depth in contexts),
                "traced_commands": len(contexts),
                "runtime_sha256": {
                    relative: hashlib.sha256((tree / relative).read_bytes()).hexdigest()
                    for relative in paired.CHANGED
                },
            }
    (paired.OUTPUT / "subshell-trace-results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
