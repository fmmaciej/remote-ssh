from __future__ import annotations

import json
from pathlib import Path

from bench.model import BenchConfigError, ReferenceScenario
from bench.scenarios import MEASURED_SCENARIO_DESCRIPTIONS

REFERENCE_FILE_NAME = "shell_startup_references.json"
LOCAL_REFERENCE_FILE_NAME = "shell_startup_references.local.json"


def reference_file_paths(current_repo: Path) -> tuple[Path, Path]:
    config_dir = current_repo / "dev" / "config"
    return config_dir / REFERENCE_FILE_NAME, config_dir / LOCAL_REFERENCE_FILE_NAME


def parse_nonnegative_float(path: Path, index: int, key: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise BenchConfigError(f"{path}: reference #{index} has invalid {key}; expected number")
    result = float(value)
    if result < 0:
        raise BenchConfigError(f"{path}: reference #{index} has invalid {key}; expected >= 0")
    return result


def parse_reference_record(path: Path, index: int, record: object) -> ReferenceScenario:
    if not isinstance(record, dict):
        raise BenchConfigError(f"{path}: reference #{index} must be an object")

    raw_name = record.get("name")
    if not isinstance(raw_name, str) or not raw_name.strip():
        raise BenchConfigError(f"{path}: reference #{index} has invalid name")
    name = raw_name.strip()
    if name in MEASURED_SCENARIO_DESCRIPTIONS:
        raise BenchConfigError(f"{path}: reference {name!r} conflicts with a measured scenario")

    raw_description = record.get("description")
    if not isinstance(raw_description, str) or not raw_description.strip():
        raise BenchConfigError(f"{path}: reference {name!r} has invalid description")

    return ReferenceScenario(
        name=name,
        description=raw_description.strip(),
        ready_ms=parse_nonnegative_float(path, index, "ready_ms", record.get("ready_ms")),
        total_ms=parse_nonnegative_float(path, index, "total_ms", record.get("total_ms")),
    )


def load_reference_file(path: Path, *, required: bool) -> tuple[ReferenceScenario, ...]:
    if not path.exists():
        if required:
            raise BenchConfigError(f"missing reference file: {path}")
        return ()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BenchConfigError(f"{path}: invalid JSON: {exc.msg}") from exc

    if not isinstance(data, dict):
        raise BenchConfigError(f"{path}: root value must be an object")
    raw_references = data.get("references")
    if not isinstance(raw_references, list):
        raise BenchConfigError(f"{path}: expected references list")

    references: list[ReferenceScenario] = []
    seen: set[str] = set()
    for index, record in enumerate(raw_references):
        reference = parse_reference_record(path, index, record)
        if reference.name in seen:
            raise BenchConfigError(f"{path}: duplicate reference {reference.name!r}")
        seen.add(reference.name)
        references.append(reference)
    return tuple(references)


def load_reference_scenarios(current_repo: Path) -> tuple[ReferenceScenario, ...]:
    default_path, local_path = reference_file_paths(current_repo)
    merged: dict[str, ReferenceScenario] = {}
    order: list[str] = []

    for path, required in ((default_path, True), (local_path, False)):
        for reference in load_reference_file(path, required=required):
            if reference.name not in merged:
                order.append(reference.name)
            merged[reference.name] = reference

    return tuple(merged[name] for name in order)
