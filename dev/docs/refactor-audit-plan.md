# Refactor Audit Plan

Created: 2026-06-01

This is the working plan for staged refactor-oriented audits of the runtime and
developer command code. The first cycle covers only:

- `bin/`
- `lib/`
- `scripts/`
- `shell/`
- `tools/`

Other repository areas, including `docs/`, `dots/`, and broad `dev/tests/`
review, are intentionally deferred unless an audited area directly depends on
them.

## Ground Rules

- Audit first, refactor later.
- Keep runtime portability as a hard constraint.
- Treat `tools/vendors/bash-preexec.sh` as vendored code; review only the
  integration boundary.
- Do not introduce new runtime dependencies.
- Prefer small, test-backed refactors after each audit finding is understood.
- Use `just smoke` as the default verification for normal follow-up changes.
- Do not run `just test-assets-live` unless explicitly requested.

## Report Format

Each audit stage should produce a short report with:

- Findings: concrete issues with file and line references.
- Refactor candidates: suggested changes without applying them yet.
- Risk: low, medium, or high.
- Test coverage needed: tests to add or preserve before refactoring.
- Suggested order: safest sequence for follow-up changes.

## Stages

### Stage 0: Map And Criteria

Status: done ([report](refactor-audit-stage-0.md))

Goal: establish the dependency map and review criteria before changing code.

Review:

- Source/load graph: which modules source which other modules.
- Public entrypoints: `bin/remote-ssh`, `tools/install-tool.sh`,
  `tools/generate-def.sh`, and helper commands in `bin/`.
- Runtime versus developer-only boundaries.
- Places where runtime code may accidentally require heavier dependencies.
- Largest files and functions as candidates for future splitting.

Output:

- Module map.
- Refactor criteria.
- Initial risk list.

### Stage 1: Shell Runtime

Status: done ([report](refactor-audit-stage-1.md))

Scope:

- `shell/rc.sh`
- `shell/rc.d/`
- `shell/config*`
- `shell/update-check*`
- `shell/welcome*`
- root `lib/`

Review:

- Startup cost and login-time work.
- Opt-out guards and cheap hook behavior.
- Hidden dependencies outside the minimal runtime tool set.
- Duplication between `shell/` and `tools/lib/` helpers.
- Stability and clarity of welcome, config, and update-check module APIs.

### Stage 2: Public CLI And Commands

Status: done ([report](refactor-audit-stage-2.md))

Scope:

- `bin/remote-ssh`
- `tools/lib/commands.lib.sh`
- `tools/lib/commands/`

Review:

- Routing and usage/help consistency.
- Repeated argument parsing patterns.
- Repeated confirm, list, and report patterns.
- Facade files versus private command modules.
- Function naming and exit behavior consistency.
- Ensure informational flows such as `update check` do not mutate the checkout.

### Stage 3: Install Core

Status: done ([report](refactor-audit-stage-3.md))

Scope:

- `tools/lib/install/`
- `tools/lib/install-tool/`
- `tools/lib/common/`
- `tools/install-tool.sh`
- The contract with `tools/defs/`

Review:

- Atomic install behavior and symlink rollback.
- Pinned version enforcement.
- Platform and asset selection.
- Checksum, archive, and raw executable handling.
- Duplication between install, check, doctor, prune, and uninstall behavior.
- Tests needed before changing install semantics.

### Stage 4: Developer And Helper Scripts

Status: done ([report](refactor-audit-stage-4.md))

Scope:

- `scripts/ci_run.sh`
- `scripts/helm_chart_diff.sh`
- `scripts/ssh_hosts.py`
- `tools/generate-def.sh`
- `tools/lib/generate-def/`

Review:

- Large scripts that should be split.
- Functions that mix CLI parsing, IO, and domain logic.
- Generator contract with exact tool definitions.
- User-facing helper behavior that should be covered by subprocess tests.
- Developer-only dependencies that must not leak into the runtime path.

## Proposed Order

1. Stage 0: Map And Criteria.
2. Stage 1: Shell Runtime.
3. Stage 2: Public CLI And Commands.
4. Stage 3: Install Core.
5. Stage 4: Developer And Helper Scripts.
