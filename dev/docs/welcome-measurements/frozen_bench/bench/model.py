from __future__ import annotations

from dataclasses import dataclass


class BenchConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class Sample:
    ready_ms: float | None
    total_ms: float
    returncode: int | None
    timed_out: bool
    output_tail: str

    @property
    def ok(self) -> bool:
        return self.ready_ms is not None and self.returncode == 0 and not self.timed_out


@dataclass(frozen=True)
class ScenarioResult:
    name: str
    description: str
    samples: tuple[Sample, ...]
    source: str = "measured"


@dataclass(frozen=True)
class ReferenceScenario:
    name: str
    description: str
    ready_ms: float
    total_ms: float
