# Developer Tooling

`dev/` contains optional local tooling used to maintain this repository. Nothing
here is required on remote hosts, and developer dependencies must stay isolated
from runtime shell code.

Python developer tooling targets Python 3.13.

## Quick Start

```bash
cd dev
uv sync
just smoke
```

From the repository root, the top-level `justfile` delegates common developer
commands to `dev/justfile`:

```bash
just smoke
just lint
just fmt
```

## Sections

- [Start](docs/start.md): required local tools, `uv sync`, and pre-commit hooks.
- [Commands](docs/commands.md): root and `dev/` `just` recipes.
- [Checks](docs/checks.md): smoke, lint, type checks, pytest, and test guidance.
  Includes the [navi/skim contract and offline acceptance tests](docs/checks.md#navi-and-skim).
- [Live Assets](docs/live-assets.md): optional GitHub Releases validation.
- [Shell Startup Benchmark](docs/bench-shell.md): local PTY benchmark for
  remote-ssh shell startup cost.
- [Config Loader Optimization](docs/config-loader-implementation-record.md):
  implementation, verification, and measurements, with the
  [accepted plan](docs/config-loader-implementation-plan.md) and
  [initial implementation audit](docs/config-loader-implementation-audit.md),
  [fresh behavior re-audit](docs/config-loader-independent-reaudit.md), and
  [independent performance verification](docs/config-loader-reaudit-performance.md).
- [Welcome Optimization](docs/welcome-implementation-record.md): implementation
  and measurements following the [accepted plan](docs/welcome-implementation-plan.md),
  with the [independent implementation audit](docs/welcome-implementation-audit.md).
- [Audit Fix Plan](docs/audit-fix-plan.md): correctness fixes and regression
  coverage in delivery order.
- [Archive Extraction Plan](docs/archive-extraction-plan.md): validation,
  isolated extraction, and installer failure regressions; not scheduled.
- [Flyline Integration Plan](docs/flyline-implementation-plan.md): latest stable
  1.10.0 plus a pinned port of Vim PR #974, native macOS/Linux builds, and optional
  editor activation. The earlier [1.9.0 pilot](docs/flyline-pilot-record.md)
  remains historical. The [patched candidate pilot](docs/flyline-pr974-pilot-record.md)
  records the historical R4 vi/history/completion/terminal gates and measurements.
  The [fork migration](docs/flyline-fork-integration-record.md) moves source/builds
  to `fmmaciej/flyline`, keeping its master unchanged. Library management and
  opt-in activation are implemented; Release publication is deferred by user.
  Linux/SSH remain unverified.
  The [integration audit and commit proposal](docs/flyline-integration-audit.md)
  preserves the original four findings and proposed commit boundaries.
  The [completed repair record](docs/flyline-integration-repair-r1-record.md)
  records their implementation, local qualification and independent SDD Pass.
  The [post-audit repair plan](docs/flyline-implementation-plan.md#post-audit-repair-plan)
  preserves the accepted scope and completion gates.
- [Flyline R5 release promotion](docs/flyline-release-promotion-plan.md):
  accepted generator artifact-version override and production definition plan;
  implementation in progress.
- [Interactive Tool Performance](docs/interactive-tools-performance.md): local
  ble.sh/Flyline/zsh editor measurements, vi controls, and separate
  Carapace/flycomp completion timings.
- [Completion Provider Pilot](docs/completion-provider-pilot.md): argc, Carapace,
  and native Bash completions; repeated timings, dependency checks, quoting,
  candidate coverage, and vi controls.
- [Carapace Integration Plan](docs/carapace-implementation-plan.md): one optional
  on-demand provider for Readline and the planned Flyline integration; planned,
  not implemented.
- [Deferred Shell Simplification](todo-bench.md): startup measurements and
  simplification ideas to revisit after the correctness fixes.

## Notes

- No global Python developer tools are required beyond `uv`.
- Python scripts in this repository should use the standard library unless a
  dependency is explicitly isolated in developer tooling.
- Runtime install paths are documented in
  [Install Flow](../docs/install.md#installed-paths).
