# Flyline integration repair R1

Date: 2026-11-09

Status: Repair 01 implemented. Changed-source startup gate passes; full checks pass; final SDD acceptance is tracked in execution/audit history.

Cycle: `flyline-repair-20261109-r1`; initial implementation round 0.

**Round 0 finding (preserved):** two valid cold Atuin startup gates failed. Their source, samples and audit remain frozen; the changed-source repair and current acceptance state are recorded below.

The [accepted R5 repair contract](flyline-implementation-plan.md#post-audit-repair-plan)
was executed in order F3 → F1 → F2 → F4. Its exact accepted bytes and required
records remain in the [SDD baseline manifest](flyline-integration-repair-r1-evidence/history/flyline-repair-20261109-r1/baseline-1/baseline.json).
The [execution state](flyline-integration-repair-r1-evidence/history/flyline-repair-20261109-r1/execution.md)
and [events](flyline-integration-repair-r1-evidence/history/flyline-repair-20261109-r1/events.md)
identify separate planner, implementer and auditor responsibilities.

<!-- repair01:start -->
## Repair 01 — current result

Changed-source startup gate passes; full checks pass; final SDD acceptance is tracked in execution/audit history.

Supported initialization batching preserves every effective setting and binding;
all four native settings profiles and both real combined-call rollback/Readline
cases pass. Focused tests: `151 passed, 26 skipped in 41.32s`. Full smoke pytest: `1555 passed, 56 skipped in 458.65s (0:07:38)`.
The single changed-source eight-scenario gate is **PASS**
under the original 30/60 ms limits. Detailed source, semantic, timing and check
evidence is in the [repair-01 result](flyline-integration-repair-r1-evidence/repair-01/result.md).

Round 0's two valid failures remain preserved below. Completion still requires
independent round-1 audit Pass; this result does not waive any accepted gate.

<!-- repair01:end -->

## Changes and preserved behavior

- F3: uninstall validates requested names first and inspects `.active` only
  for explicit library selections or automatic discovery with library definitions.
  Invalid required library directories abort before link, release or expected-tools
  mutation; binary/bundle-only operations preserve unrelated `.active` paths.
- F1: immediately before managed editor resolution, a current Atuin marker with
  any selected backend other than managed `atuin` excludes Flyline. Late OS/host
  owners retain their bindings/callbacks. Managed Atuin and `ATUIN_NOBIND` remain supported.
- F2: exact entries from read-only `builtin enable -a` detect disabled external
  Flyline alongside the existing enabled/function/alias exclusions, with no
  enable, settings or unload action for external editors.
- F4: failed load or successful unload after settings failure restores each
  marker's independent set/unset state, scalar value and export attribute,
  including exported-but-unset declarations. Successful activation and failed
  unload retain the managed markers while the builtin remains loaded.

Runtime changes are confined to two Bash modules. No module-23 change, new runtime
process dependency, per-command hook, source pin change or native rebuild was needed.
The optional editor remains disabled by default and selected once per Bash process.

## Round 0 regression-first evidence (preserved)

Each meaningful red run failed for its audited cause before the corresponding fix.

| Finding | Initial test result | Evidence |
| --- | --- | --- |
| F3 | `12 failed, 26 passed, 37 deselected in 10.71s` | [F3-red.log](flyline-integration-repair-r1-evidence/F3-red.log) |
| F1 | `4 failed, 4 passed, 26 deselected in 2.92s` | [F1-red.log](flyline-integration-repair-r1-evidence/F1-red.log) |
| F2 | `1 failed, 11 passed, 34 deselected in 0.38s` | [F2-red.log](flyline-integration-repair-r1-evidence/F2-red.log) |
| F4 | `12 failed, 14 passed, 26 skipped, 46 deselected in 1.27s` | [F4-red.log](flyline-integration-repair-r1-evidence/F4-red.log) |

The affected suite reports `147 passed, 26 skipped in 38.75s` with explicit `/bin/bash` 3.2 and
Homebrew Bash 5.3.20 selection. Native mutation tests intentionally skip Bash 3.2;
its CLI behavior and guarded editor fallback run in the matrix. [Focused result](flyline-integration-repair-r1-evidence/focused-final-green.log).
Related full-rc, Atuin and history-backend tests report `108 passed in 31.33s`.
[Related result](flyline-integration-repair-r1-evidence/related-green.log).

The late-hook tests exercise real full-rc OS/host hooks, both Atuin toggles,
actual repeated `rcrc` alias expansion, later binding edits and a fresh nested
Bash. Function/alias exclusions use actual shell definitions. Rollback cases
compare declarations and child environments independently for each variable.
The library matrix includes unreadable directories where permissions permit,
invalid mixed/automatic selections, valid mixed uninstall and format-1 releases.

## Round 0 native local gates (preserved)

The [new ownership probe](../flyline/ownership.py) uses the actual managed installer,
real R5 library, real Atuin and disposable PTYs. It accepts explicit `--repo`,
`--bash`, `--library`, `--atuin`, `--output` paths, performs no downloads and fails
on wrong state or timeout. All 32 cases pass: OS/host late
Atuin with both toggles, externally disabled builtin, managed Bash/Atuin/NOBIND,
and all 24 variable-state/failure-stage cases. Each native settings rollback also
executes Readline vi editing from `ac` to actual argument `bc`.
[Ownership results](flyline-integration-repair-r1-evidence/native-ownership-rerun-1/results.json).

The first ownership run retained correct ownership decisions and passed the other
28 cases, but its four late-hook callback comparisons failed because the fixture
sourced bash-preexec's `declare -a` statements inside a hook function. Those arrays
were local to that function. The corrected fixture loads the external preexec
library at rc top level before actual late Atuin initialization and preserves the
same exact binding/callback comparisons. [Initial run, preserved](flyline-integration-repair-r1-evidence/native-ownership/results.json).
This correction changed only the developer probe.

The existing lifecycle gate passes 4 load/unload/Readline cases.
[Lifecycle results](flyline-integration-repair-r1-evidence/native-lifecycle/results.json).
Managed history passes Bash native, skim and Atuin, including editable selection,
cancellation, Up/k, persistence, Atuin status/duration and reload behavior.
[History results](flyline-integration-repair-r1-evidence/native-history/results.json).

The R5 library SHA-256 remains
`ac989a041026f49df1d3b544290ee3e67b497a0d3f82fe4785cd3c106e431d57`.
The explicitly supplied skim fixture was provisioned locally from the existing
pinned definition after checksum verification; the probe scripts themselves stay
offline. [Exact input paths, versions and hashes](flyline-integration-repair-r1-evidence/native-inputs.json).

## Round 0 startup measurements (preserved)

The bounded paired guard-only diagnostic used three alternating before/current rounds of 100 iterations. Median cost was 2.320 ms before and 6.170 ms after (increment 3.850 ms). It covers the added ownership checks and both attribute snapshots, stops before native loading, and is diagnostic evidence rather than startup acceptance. [Results](flyline-integration-repair-r1-evidence/guard-diagnostic/results.json), [exact diagnostic source](flyline-integration-repair-r1-evidence/guard-diagnostic.py).

One separately declared enabled-editor diagnostic alternated 20 frozen-before/current pairs with two warmups per variant. Before median/p95: 290.40/331.06 ms; current: 297.22/317.38 ms. Median signed paired current-minus-before delta: 2.63 ms. Both use the same native payload/inputs and runtime trees differing only in the Flyline integration module. This narrows attribution but is not an on/off acceptance test and cannot identify the native/host cause by itself. [Declaration and all raw paired samples](flyline-integration-repair-r1-evidence/paired-startup-diagnostic/results.json), [exact source](flyline-integration-repair-r1-evidence/paired-startup-diagnostic.py).

Both valid eight-scenario measurements fail the required cold Atuin startup budget. The initial run has 47.69 ms median overhead (>30 ms), with p95 overhead 59.53 ms. The exactly-once predeclared unchanged confirmation has 47.29 ms median overhead (>30 ms) and 93.35 ms p95 overhead (>60 ms). All 320 measured state-valid samples are retained. No samples were dropped or pooled, and neither failure is invalidated. No further full startup run or budget change was made. [Predeclared single confirmation](flyline-integration-repair-r1-evidence/startup-confirmation-declaration.json). [Initial failed dataset](flyline-integration-repair-r1-evidence/startup/results.json).

Initial results:

| Atuin/cache scenario | Median overhead | p95 overhead | Result |
| --- | --- | --- | --- |
| bash, fresh HOME | 2.97 ms | -20.52 ms | pass |
| bash, warm HOME | 21.84 ms | -34.62 ms | pass |
| atuin, fresh HOME | 47.69 ms | 59.53 ms | FAIL |
| atuin, warm HOME | 20.57 ms | -8.50 ms | pass |

Confirmation results (required gate still unmet):

The established 30 ms median / 60 ms p95 incremental limits were written to
[budgets.json](flyline-integration-repair-r1-evidence/startup-confirmation-1/budgets.json)
before sampling.

| Atuin/cache scenario | Median overhead | p95 overhead | Result |
| --- | --- | --- | --- |
| bash, fresh HOME | 21.83 ms | 18.29 ms | pass |
| bash, warm HOME | 20.15 ms | 4.69 ms | pass |
| atuin, fresh HOME | 47.29 ms | 93.35 ms | FAIL |
| atuin, warm HOME | 26.49 ms | 32.62 ms | pass |

[Samples and statistics](flyline-integration-repair-r1-evidence/startup-confirmation-1/results.json).

## Round 0 static checks and limits (preserved)

`just smoke`, `git diff --check` and bounded local Markdown links pass.
`just smoke` includes the full pytest recipe dependency as well as static checks;
its final-source pytest result is `1551 passed, 56 skipped in 448.80s (0:07:28)`.
[Smoke](flyline-integration-repair-r1-evidence/smoke-rerun-1.log),
[diff check](flyline-integration-repair-r1-evidence/diff-check.log),
[link results](flyline-integration-repair-r1-evidence/local-links.json).
The initial smoke run failed on an unquoted automatic tool-list substitution (SC2046); a Bash 3.2-safe checked array collection corrected it before the successful smoke rerun. [Initial smoke, preserved](flyline-integration-repair-r1-evidence/smoke.log). Command metadata accompanies each log. Source fingerprints identify the final
files and preserve the prior worktree boundary. Historical evidence remains intact.

Validation is local macOS arm64 only. Linux, SSH hosts and other architectures
remain unverified. No live asset checker, user startup-file edits, Release
publication, production manifest promotion, staging, commits or pushes were run.
The initial integration remains unpublished under the user's existing decision;
this record documents the accepted post-audit repair implementation; final SDD acceptance is tracked in its execution and audit history.
