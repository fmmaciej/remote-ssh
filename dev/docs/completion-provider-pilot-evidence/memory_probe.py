"""Measure macOS time(1) peak RSS for one valid static completion request."""

from __future__ import annotations

import argparse
import json
import re
import statistics
import subprocess
import tempfile
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    commands = {
        "argc": [str(root / "bin/argc"), "--argc-compgen", "bash", "", "rg", "--ver"],
        "carapace": [str(root / "bin/carapace"), "rg", "export", "rg", "--ver"],
        "native": [
            str(root / "bin/bash"),
            "--noprofile",
            "--norc",
            "-c",
            'source "$1"; COMP_WORDS=(rg --ver); COMP_CWORD=1; '
            '_rg rg --ver rg; printf "%s\\n" "${COMPREPLY[@]}"',
            "probe",
            str(root / "native/rg.bash"),
        ],
    }
    results = {}
    with tempfile.TemporaryDirectory(prefix="completion-memory-") as home:
        env = {
            "HOME": home,
            "PATH": str(root / "bin") + ":/usr/bin:/bin",
            "LANG": "en_US.UTF-8",
            "ARGC_SHELL_PATH": str(root / "bin/bash"),
            "ARGC_COMPLETIONS_ROOT": str(root / "definitions"),
            "ARGC_COMPLETIONS_PATH": str(root / "definitions/completions"),
            "ARGC_COMPGEN_DESCRIPTION": "0",
        }
        for name, command in commands.items():
            values = []
            for _ in range(6):
                proc = subprocess.run(
                    ["/usr/bin/time", "-l", *command],
                    env=env,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                assert "--version" in proc.stdout, (name, proc.stdout)
                found = re.search(r"(\d+)\s+maximum resident set size", proc.stderr)
                assert found is not None, proc.stderr
                values.append(int(found[1]) / 1024**2)
            results[name] = {
                "command": command,
                "samples_mib": values,
                "median_mib_excluding_first": statistics.median(values[1:]),
            }
    args.output.write_text(json.dumps(results, indent=2) + "\n")
    print({k: v["median_mib_excluding_first"] for k, v in results.items()})


if __name__ == "__main__":
    main()
