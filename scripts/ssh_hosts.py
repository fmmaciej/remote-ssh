#!/usr/bin/env python3

from __future__ import annotations

import glob
import os
import shlex
import sys
from collections.abc import Iterable
from pathlib import Path


def parse_config(path: Path, seen_files: set[Path] | None = None) -> Iterable[str]:
    if seen_files is None:
        seen_files = set()

    try:
        path = path.resolve()
    except FileNotFoundError:
        return

    if path in seen_files:
        return

    seen_files.add(path)

    if not path.is_file():
        return

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return

    basedir = path.parent

    for raw in lines:
        try:
            parts = shlex.split(raw, comments=True)
        except ValueError:
            continue

        if not parts:
            continue

        keyword = parts[0].lower()
        args = parts[1:]

        if keyword == "include":
            for pattern in args:
                expanded = os.path.expandvars(os.path.expanduser(pattern))
                if not os.path.isabs(expanded):
                    expanded = str(basedir / expanded)

                for match in sorted(glob.glob(expanded)):
                    yield from parse_config(Path(match), seen_files)

        elif keyword == "host":
            for host in args:
                if any(c in host for c in "*?%!"):
                    continue

                if host:
                    yield host


def default_config_path() -> Path:
    ssh_config_env = os.environ.get("SSH_CONFIG")
    if ssh_config_env:
        return Path(os.path.expandvars(os.path.expanduser(ssh_config_env)))

    return Path.home() / ".ssh" / "config"


def main() -> int:
    config_path = default_config_path()

    if not config_path.is_file():
        print(f"Brak pliku konfiguracyjnego SSH: {config_path}", file=sys.stderr)
        return 1

    for host in sorted(set(parse_config(config_path))):
        print(host)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
