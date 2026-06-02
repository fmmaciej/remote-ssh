#!/usr/bin/env python3

from __future__ import annotations

import glob
import ipaddress
import os
import shlex
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

SOURCE_SSH_CONFIG = ".ssh/config"
SOURCE_BSSH_CONFIG = ".config/bssh/config.yaml"


@dataclass
class FindRecord:
    alias: str
    address: str
    user: str
    source: str
    port: str
    connect_kind: str
    connect_target: str


@dataclass
class YamlLine:
    indent: int
    content: str


def clean_field(value: str) -> str:
    return value.replace("\t", " ").replace("\n", " ").strip()


def render_record(record: FindRecord) -> str:
    return "\t".join(
        clean_field(field)
        for field in (
            record.alias,
            record.address,
            record.user,
            record.source,
            record.port,
            record.connect_kind,
            record.connect_target,
        )
    )


def expand_path(path: Path | str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(str(path))))


def is_ip_address(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
    except ValueError:
        return False
    return True


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


def display_address(hostname: str, hosts_by_name: dict[str, list[str]]) -> str:
    if is_ip_address(hostname):
        return hostname

    addresses = hosts_by_name.get(hostname)
    if addresses:
        return addresses[0]

    return hostname


def default_ssh_config_path() -> Path:
    for key in ("SSH_FIND_SSH_CONFIG", "SSH_CONFIG"):
        value = os.environ.get(key)
        if value:
            return expand_path(value)

    return Path.home() / ".ssh" / "config"


def default_bssh_config_path() -> Path:
    value = os.environ.get("SSH_FIND_BSSH_CONFIG") or os.environ.get("BSSH_CONFIG")
    if value:
        return expand_path(value)

    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config_home:
        return expand_path(xdg_config_home) / "bssh" / "config.yaml"

    return Path.home() / ".config" / "bssh" / "config.yaml"


def default_hosts_file_path() -> Path:
    return expand_path(os.environ.get("SSH_HOSTS_FILE") or "/etc/hosts")


def parse_ssh_config(path: Path, seen_files: set[Path] | None = None) -> Iterable[str]:
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
                    yield from parse_ssh_config(Path(match), seen_files)

        elif keyword == "host":
            for host in args:
                if any(c in host for c in "*?%!"):
                    continue
                if host:
                    yield host


def resolve_ssh_host(alias: str, config_path: Path) -> dict[str, str]:
    try:
        result = subprocess.run(
            ["ssh", "-G", "-F", str(config_path), alias],
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
        if keyword in {"hostname", "user", "port"}:
            resolved[keyword] = parts[1]

    return resolved


def build_ssh_config_records(
    config_path: Path,
    hosts_by_name: dict[str, list[str]],
) -> list[FindRecord]:
    if not config_path.is_file():
        return []

    records: list[FindRecord] = []
    for alias in sorted(set(parse_ssh_config(config_path))):
        resolved = resolve_ssh_host(alias, config_path)
        hostname = resolved.get("hostname", alias)
        records.append(
            FindRecord(
                alias=alias,
                address=display_address(hostname, hosts_by_name),
                user=resolved.get("user", ""),
                source=SOURCE_SSH_CONFIG,
                port=resolved.get("port", ""),
                connect_kind="ssh-config",
                connect_target=alias,
            )
        )

    return records


def strip_yaml_comment(raw: str) -> str:
    quote = ""
    result: list[str] = []

    for index, char in enumerate(raw):
        if quote:
            result.append(char)
            if char == quote:
                quote = ""
            continue

        if char in {"'", '"'}:
            quote = char
            result.append(char)
            continue

        if char == "#" and (index == 0 or raw[index - 1].isspace()):
            break

        result.append(char)

    return "".join(result).rstrip()


def strip_yaml_scalar(value: str) -> str:
    value = value.strip()

    while value.startswith("&"):
        parts = value.split(None, 1)
        value = parts[1].strip() if len(parts) == 2 else ""

    if value.startswith("*"):
        return ""

    if value in {"", "~", "null", "Null", "NULL"}:
        return ""

    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]

    return value


def strip_yaml_key(value: str) -> str:
    return strip_yaml_scalar(value).strip()


def split_yaml_key_value(content: str) -> tuple[str, str] | None:
    for index, char in enumerate(content):
        if char != ":":
            continue
        if index + 1 < len(content) and not content[index + 1].isspace():
            continue

        key = strip_yaml_key(content[:index])
        if not key:
            return None
        return key, strip_yaml_scalar(content[index + 1 :])

    return None


def read_yaml_lines(path: Path) -> list[YamlLine]:
    try:
        raw_lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []

    lines: list[YamlLine] = []
    for raw in raw_lines:
        without_comment = strip_yaml_comment(raw)
        if not without_comment.strip():
            continue

        content = without_comment.strip()
        if content in {"---", "..."}:
            continue

        indent = len(without_comment) - len(without_comment.lstrip(" "))
        lines.append(YamlLine(indent=indent, content=content))

    return lines


def top_level_block(lines: list[YamlLine], key: str) -> tuple[int, list[YamlLine]] | None:
    for index, line in enumerate(lines):
        if line.indent != 0:
            continue

        parsed = split_yaml_key_value(line.content)
        if parsed is None or parsed[0] != key:
            continue

        block: list[YamlLine] = []
        for child in lines[index + 1 :]:
            if child.indent <= line.indent:
                break
            block.append(child)

        return line.indent, block

    return None


def parse_key_values(lines: list[YamlLine], allowed: set[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    child_indent = min((line.indent for line in lines), default=None)
    if child_indent is None:
        return values

    for line in lines:
        if line.indent != child_indent:
            continue

        parsed = split_yaml_key_value(line.content)
        if parsed is None:
            continue

        key, value = parsed
        if key in allowed:
            values[key] = value

    return values


def parse_node_string(value: str) -> dict[str, str]:
    value = strip_yaml_scalar(value)
    if not value:
        return {}

    user = ""
    host_port = value
    if "@" in host_port:
        user, host_port = host_port.split("@", 1)

    host = host_port
    port = ""
    if host_port.startswith("[") and "]:" in host_port:
        host, port = host_port.rsplit(":", 1)
        host = host.strip("[]")
    elif host_port.count(":") == 1:
        possible_host, possible_port = host_port.rsplit(":", 1)
        if possible_port.isdigit():
            host = possible_host
            port = possible_port

    node = {"host": host}
    if user:
        node["user"] = user
    if port:
        node["port"] = port
    return node


def find_child_blocks(lines: list[YamlLine], parent_indent: int) -> list[tuple[str, list[YamlLine]]]:
    child_indent = min(
        (
            line.indent
            for line in lines
            if line.indent > parent_indent and not line.content.startswith("-")
        ),
        default=None,
    )
    if child_indent is None:
        return []

    blocks: list[tuple[str, list[YamlLine]]] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        parsed = split_yaml_key_value(line.content)
        if line.indent != child_indent or parsed is None:
            index += 1
            continue

        name = parsed[0]
        block: list[YamlLine] = []
        index += 1
        while index < len(lines) and lines[index].indent > child_indent:
            block.append(lines[index])
            index += 1

        blocks.append((name, block))

    return blocks


def extract_nodes_blocks(cluster_lines: list[YamlLine]) -> tuple[list[list[YamlLine]], list[YamlLine]]:
    nodes_blocks: list[list[YamlLine]] = []
    non_node_lines: list[YamlLine] = []

    index = 0
    while index < len(cluster_lines):
        line = cluster_lines[index]
        parsed = split_yaml_key_value(line.content)
        if parsed is None or parsed[0] != "nodes":
            non_node_lines.append(line)
            index += 1
            continue

        nodes_indent = line.indent
        block: list[YamlLine] = []
        index += 1
        while index < len(cluster_lines) and cluster_lines[index].indent > nodes_indent:
            block.append(cluster_lines[index])
            index += 1
        nodes_blocks.append(block)

    return nodes_blocks, non_node_lines


def parse_nodes_block(lines: list[YamlLine]) -> list[dict[str, str]]:
    nodes: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    current_indent = -1

    def flush_current() -> None:
        nonlocal current
        if current:
            nodes.append(current)
        current = None

    for line in lines:
        if line.content.startswith("-"):
            flush_current()
            current_indent = line.indent
            item = line.content[1:].strip()

            if not item or item.startswith("<<"):
                current = {}
                continue

            if item.startswith("*"):
                current = None
                continue

            parsed = split_yaml_key_value(item)
            if parsed is None:
                node = parse_node_string(item)
                if node:
                    nodes.append(node)
                current = None
                continue

            key, value = parsed
            current = {} if key == "<<" else {key: value}
            continue

        if current is None or line.indent <= current_indent:
            continue

        parsed = split_yaml_key_value(line.content)
        if parsed is None:
            continue

        key, value = parsed
        if key == "<<":
            continue

        current[key] = value

    flush_current()
    return nodes


def bssh_node_record(
    node: dict[str, str],
    defaults: dict[str, str],
    cluster_values: dict[str, str],
    hosts_by_name: dict[str, list[str]],
) -> FindRecord | None:
    normalized = {key.lower(): value for key, value in node.items()}
    host = normalized.get("host") or normalized.get("hostname")
    if not host:
        return None

    alias = normalized.get("name") or normalized.get("alias") or host
    user = normalized.get("user") or cluster_values.get("user") or defaults.get("user", "")
    port = normalized.get("port") or cluster_values.get("port") or defaults.get("port", "")

    return FindRecord(
        alias=alias,
        address=display_address(host, hosts_by_name),
        user=user,
        source=SOURCE_BSSH_CONFIG,
        port=port,
        connect_kind="direct",
        connect_target=host,
    )


def build_bssh_records(path: Path, hosts_by_name: dict[str, list[str]]) -> list[FindRecord]:
    if not path.is_file():
        return []

    lines = read_yaml_lines(path)
    defaults_block = top_level_block(lines, "defaults")
    defaults = parse_key_values(defaults_block[1], {"user", "port"}) if defaults_block else {}

    clusters_block = top_level_block(lines, "clusters")
    if clusters_block is None:
        return []

    records: list[FindRecord] = []
    for _cluster_name, cluster_lines in find_child_blocks(clusters_block[1], clusters_block[0]):
        nodes_blocks, non_node_lines = extract_nodes_blocks(cluster_lines)
        cluster_values = parse_key_values(non_node_lines, {"user", "port"})

        for nodes_block in nodes_blocks:
            for node in parse_nodes_block(nodes_block):
                record = bssh_node_record(node, defaults, cluster_values, hosts_by_name)
                if record is not None:
                    records.append(record)

    return records


def main() -> int:
    hosts_by_name = parse_hosts_file(default_hosts_file_path())
    records = [
        *build_ssh_config_records(default_ssh_config_path(), hosts_by_name),
        *build_bssh_records(default_bssh_config_path(), hosts_by_name),
    ]

    for record in sorted(records, key=lambda item: (item.alias, item.source, item.address)):
        print(render_record(record))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
