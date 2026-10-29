#!/usr/bin/env python3
"""Read-only runtime snapshot comparison; never prints private file contents."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import stat

RUNTIME_DIRS = ("shell", "lib", "tools", "bin", "dots", "scripts")
AUTHORIZED = {
    "shell/welcome.lib.sh", "shell/welcome/runner.sh", "shell/welcome/bundled.sh",
    "shell/welcome/bundled-runner.sh", "shell/welcome.d/00-remote-ssh.sh",
    "shell/welcome.d/10-hw.sh", "shell/welcome.d/20-sw.sh",
}


def manifest(tree: Path, all_paths: bool = False) -> dict:
    files = {}
    for directory in (("",) if all_paths else RUNTIME_DIRS):
        for path in sorted((tree / directory).rglob("*")):
            if "__pycache__" in path.parts and not all_paths:
                continue
            info = path.lstat()
            if stat.S_ISREG(info.st_mode):
                entry = {"type": "file", "mode": oct(stat.S_IMODE(info.st_mode)),
                         "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            elif stat.S_ISLNK(info.st_mode):
                entry = {"type": "symlink", "mode": oct(stat.S_IMODE(info.st_mode)),
                         "target": str(path.readlink())}
            elif all_paths and stat.S_ISDIR(info.st_mode):
                entry = {"type": "directory", "mode": oct(stat.S_IMODE(info.st_mode))}
            else:
                continue
            files[str(path.relative_to(tree))] = entry
    return {"aggregate": hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest(),
            "files": files}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--all-paths", action="store_true")
    args = parser.parse_args()
    before, after = manifest(args.baseline, args.all_paths), manifest(args.candidate, args.all_paths)
    differences = []
    for path in sorted(before["files"].keys() | after["files"].keys()):
        a, b = before["files"].get(path), after["files"].get(path)
        if a != b:
            differences.append({"path": path, "authorized_path": path in AUTHORIZED,
                                "baseline": a, "candidate": b})
    result = {"baseline_path": str(args.baseline), "candidate_path": str(args.candidate),
              "scope": "complete tree" if args.all_paths else "runtime directories",
              "baseline": before, "candidate": after, "differences": differences,
              "unauthorized_differences": [d for d in differences if not d["authorized_path"]]}
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"differences": len(differences),
                      "unauthorized_differences": result["unauthorized_differences"]}, indent=2))


if __name__ == "__main__":
    main()
