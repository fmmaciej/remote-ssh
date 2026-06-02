#!/usr/bin/env python3

from __future__ import annotations

import argparse
import glob
import ipaddress
import os
import shlex
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class HostRecord:
    alias: str
    hostname: str = ""
    addresses: list[str] = field(default_factory=list)
    user: str = ""
    port: str = ""

    def add_addresses(self, addresses: Iterable[str]) -> None:
        for address in addresses:
            if address and address not in self.addresses:
                self.addresses.append(address)


def parse_config(path: Path, seen_files: set[Path] | None = None) -> Iterable[str]:
    """
    Recursively parse OpenSSH config files and yield non-wildcard Host aliases.
    """
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


def parse_hosts_file(path: Path) -> dict[str, list[str]]:
    by_name: dict[str, list[str]] = {}

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return by_name

    for raw in lines:
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue

        parts = line.split()
        if len(parts) < 2:
            continue

        address = parts[0]
        try:
            ipaddress.ip_address(address)
        except ValueError:
            continue

        for name in parts[1:]:
            addresses = by_name.setdefault(name, [])
            if address not in addresses:
                addresses.append(address)

    return by_name


def is_ip_address(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
    except ValueError:
        return False
    return True


def is_standalone_hosts_address(value: str) -> bool:
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        return False

    return not (
        address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_unspecified
        or value == "255.255.255.255"
    )


def default_config_path() -> Path:
    ssh_config_env = os.environ.get("SSH_CONFIG")
    if ssh_config_env:
        return Path(os.path.expandvars(os.path.expanduser(ssh_config_env)))

    return Path.home() / ".ssh" / "config"


def expand_path(path: Path | str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(str(path))))


def resolve_ssh_host(alias: str, config_path: Path) -> dict[str, str]:
    command = ["ssh", "-G", "-F", str(config_path), alias]

    try:
        result = subprocess.run(
            command,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        return {}

    if result.returncode != 0:
        return {}

    resolved: dict[str, str] = {}
    for raw in result.stdout.splitlines():
        parts = raw.split(None, 1)
        if len(parts) != 2:
            continue

        keyword = parts[0].lower()
        value = parts[1]
        if keyword in {"hostname", "user", "port"}:
            resolved[keyword] = value

    return resolved


def address_candidates(name: str, hosts_by_name: dict[str, list[str]]) -> list[str]:
    if not name:
        return []

    if is_ip_address(name):
        return [name]

    return hosts_by_name.get(name, [])


def merge_record(records: dict[str, HostRecord], record: HostRecord) -> None:
    existing = records.get(record.alias)
    if existing is None:
        records[record.alias] = record
        return

    if not existing.hostname and record.hostname:
        existing.hostname = record.hostname
    if not existing.user and record.user:
        existing.user = record.user
    if not existing.port and record.port:
        existing.port = record.port
    existing.add_addresses(record.addresses)


def build_pick_records(
    config_path: Path,
    hosts_by_name: dict[str, list[str]],
) -> list[HostRecord]:
    records: dict[str, HostRecord] = {}
    resolved_hostnames: set[str] = set()

    if config_path.is_file():
        for alias in sorted(set(parse_config(config_path))):
            resolved = resolve_ssh_host(alias, config_path)
            hostname = resolved.get("hostname", alias)
            resolved_hostnames.add(hostname)
            record = HostRecord(
                alias=alias,
                hostname=hostname,
                user=resolved.get("user", ""),
                port=resolved.get("port", ""),
            )
            record.add_addresses(address_candidates(hostname, hosts_by_name))
            record.add_addresses(address_candidates(alias, hosts_by_name))
            merge_record(records, record)

    for alias, addresses in hosts_by_name.items():
        if alias in resolved_hostnames:
            continue

        if not any(is_standalone_hosts_address(address) for address in addresses):
            continue

        record = HostRecord(alias=alias, hostname=alias)
        record.add_addresses(addresses)
        merge_record(records, record)

    return sorted(records.values(), key=lambda record: record.alias)


def render_pick_record(record: HostRecord) -> str:
    fields = [record.alias]

    if record.hostname and record.hostname != record.alias:
        fields.append(f"hostname={record.hostname}")

    if record.addresses:
        fields.append(f"ip={','.join(record.addresses)}")

    if record.user:
        fields.append(f"user={record.user}")

    if record.port:
        fields.append(f"port={record.port}")

    return "\t".join(fields)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="List SSH host aliases.")
    parser.add_argument(
        "--format",
        choices=("names", "pick"),
        default="names",
        help="output plain aliases or tab-separated fields for ssh-pick",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="OpenSSH config path, defaulting to SSH_CONFIG or ~/.ssh/config",
    )
    parser.add_argument(
        "--hosts-file",
        type=Path,
        default=None,
        help="hosts file path, defaulting to SSH_HOSTS_FILE or /etc/hosts",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)

    config_path = expand_path(args.config) if args.config is not None else default_config_path()
    hosts_file_env = os.environ.get("SSH_HOSTS_FILE")
    hosts_file = (
        expand_path(args.hosts_file)
        if args.hosts_file is not None
        else expand_path(hosts_file_env or "/etc/hosts")
    )

    if args.format == "names":
        if not config_path.is_file():
            print(f"Brak pliku konfiguracyjnego SSH: {config_path}", file=sys.stderr)
            return 1

        for host in sorted(set(parse_config(config_path))):
            print(host)
        return 0

    hosts_by_name = parse_hosts_file(hosts_file)
    records = build_pick_records(config_path, hosts_by_name)
    if not records:
        print(f"Brak hostow SSH w: {config_path} albo {hosts_file}", file=sys.stderr)
        return 1

    for record in records:
        print(render_pick_record(record))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
