#!/usr/bin/env python3

import glob
import os
import shlex
import sys
from collections.abc import Iterable
from pathlib import Path

SEEN_FILES: set[Path] = set()

def parse_config(path: Path) -> Iterable[str]:
    """
    Rekurencyjnie parsuje pliki OpenSSH config, zwraca nazwy hostów.
    """
    global SEEN_FILES

    try:
        path = path.resolve()

    except FileNotFoundError:
        return

    if path in SEEN_FILES:
        return

    SEEN_FILES.add(path)

    if not path.is_file():
        return

    try:
        with path.open("r", encoding="utf-8") as f:
            lines = f.readlines()

    except OSError:
        return

    basedir = path.parent

    for raw in lines:
        # ucinamy komentarz (# ...) i whitespace
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue

        try:
            parts = shlex.split(line)

        except ValueError:
            # jakaś pokręcona linia - olewamy
            continue

        if not parts:
            continue

        keyword = parts[0].lower()
        args = parts[1:]

        if keyword == "include":
            for pattern in args:
                expanded = os.path.expanduser(pattern)

                # jeśli ścieżka względna -> względem pliku, który includuje
                if not os.path.isabs(expanded):
                    expanded = str(basedir / expanded)

                # glob (np. config.d/*.conf)
                for match in glob.glob(expanded):
                    yield from parse_config(Path(match))

        elif keyword == "host":
            for h in args:
                # olewamy wildcardy typu "Host *", "Host *.example.com" itp.
                if any(c in h for c in "*?%!"):
                    continue

                if not h:
                    continue

                yield h


def main() -> int:
    ssh_config_env = os.environ.get("SSH_CONFIG")

    if ssh_config_env:
        config_path = Path(os.path.expanduser(ssh_config_env))

    else:
        config_path = Path.home() / ".ssh" / "config"

    if not config_path.is_file():
        print(f"Brak pliku konfiguracyjnego SSH: {config_path}", file=sys.stderr)
        return 1

    hosts = sorted(set(parse_config(config_path)))
    for host in hosts:
        print(host)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
