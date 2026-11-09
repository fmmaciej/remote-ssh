# Repair 01 — initialization batching result

Date: 2026-11-09

Status: Changed-source startup gate passes; full checks pass; final SDD acceptance is tracked in execution/audit history.

Cycle `flyline-repair-20261109-r1`, repair round 1. Basis and requirements remain
[the accepted R5 manifest](../history/flyline-repair-20261109-r1/baseline-1/baseline.json)
and [repair-01 plan](../history/flyline-repair-20261109-r1/repair-01-plan.md).
Final SDD acceptance is tracked in the [execution record](../history/flyline-repair-20261109-r1/execution.md).
The two valid round-0 startup failures remain retained and unmet for their old
source; this changed-source result does not erase or reinterpret those runs.

## Implementation

Only the Flyline Bash integration and its tests/native settings probe changed:

- The tutorial-disable call remains first. Existing global flags and the
  immediately following terminal-cursor setter share one supported invocation,
  preserving the native setting-write order.
- Explicit Vim enable shares the first conditional history binding where
  bindings are requested. The second Emacs binding and both callback/action
  strings remain unchanged. NOBIND/no-widget paths still explicitly enable Vim.
- Direct read-only builtin function/alias queries replace captured `type -t`;
  exact enabled/disabled builtin inspection remains. No external owner is changed.
- F4's declaration snapshots and set/value/export restoration remain unchanged.
  No `@a` transformation was introduced. No uninstall or native change was made.

Bound Atuin/skim profiles use six native settings invocations instead of eight;
unbound profiles use five instead of six. Invocation reduction is a source-level
fact, not an inferred speedup. The acceptance measurement below establishes the
actual timing result on this host.

## Functional and native results

The affected Bash 3.2/Homebrew Bash matrix reports `151 passed, 26 skipped in 41.32s`.
[Focused tests](focused.log). This includes combined-call failures stopping
further configuration, successful unload, exact exported/unset rollback, and
system Bash's graceful skip. Existing F1–F4 contracts remain covered.

The new [native effective-settings gate](../../../flyline/settings.py) compares
all actual `flyline settings --all` output and Ctrl-R key-list output byte for
byte between audited round-0 and repaired modules for Atuin, skim, NOBIND and
no-widget profiles. Every profile passes, alongside twelve independently
asserted effective values and the actual two-or-zero history bindings.
[Settings results](settings/results.json), with both snapshots and transcripts.

The same profile HOME is reused only to keep default path-valued settings equal.
Each variant execs a fresh Bash and loads R5 anew. At pinned commit
`d037c075ed30a61080873985ea2621d743ddfc64`,
[src/settings.rs](https://github.com/fmmaciej/flyline/blob/d037c075ed30a61080873985ea2621d743ddfc64/src/settings.rs#L469)
uses a process-local LazyLock initialized from defaults, and
[src/bash_builtin.rs](https://github.com/fmmaciej/flyline/blob/d037c075ed30a61080873985ea2621d743ddfc64/src/bash_builtin.rs#L383)
explicitly resets settings during each library load. The setters mutate that
in-memory state and do not persist configuration. A previous variant cannot
supply omitted settings to the next process.

Two real R5 combined-call failures also pass: invalid cursor backend and invalid
first binding action. Both restore exact quoted/unexported and exported-but-unset
markers, unload the builtin, emit the fallback warning, and execute actual
Readline vi editing from `ac` to argument `bc` without premature execution.
These are in the same [native report](settings/results.json).

Ownership remains 32/32,
lifecycle 4/4, and managed
Bash/skim/Atuin history all pass:
[ownership](ownership/results.json), [lifecycle](lifecycle/results.json),
[history](history/results.json).

## Exactly one changed-source startup gate

The [declaration](startup-declaration.json) pins changed source and inputs before
sampling; the existing harness writes [original budgets](startup/budgets.json)
before collecting eight scenarios, twenty measured rounds and two warmups each.
No tests run concurrently. No samples are dropped or pooled, no threshold changes
occur, and no unchanged confirmation is run in this repair round.

| Backend/cache | Off median / p95 | On median / p95 | Median overhead | p95 overhead | Budget |
| --- | --- | --- | --- | --- | --- |
| bash, fresh HOME | 236.26 / 267.38 ms | 248.83 / 255.11 ms | 12.57 ms | -12.27 ms | pass |
| bash, warm HOME | 175.03 / 197.78 ms | 183.73 / 194.13 ms | 8.70 ms | -3.65 ms | pass |
| atuin, fresh HOME | 268.80 / 388.18 ms | 286.31 / 295.46 ms | 17.51 ms | -92.72 ms | pass |
| atuin, warm HOME | 199.53 / 205.61 ms | 225.02 / 250.38 ms | 25.49 ms | 44.77 ms | pass |

Off cold Atuin has high tail latency in this run. Negative p95 differences reflect
those measured off tails; neither a stable causal speedup nor a native root cause
is established from this single timing run. All absolute statistics and samples
remain visible. [All samples and statistics](startup/results.json). Overall gate:
**PASS**.

The [initial round-0 gate](../startup/results.json) and its
[single predeclared confirmation](../startup-confirmation-1/results.json) remain
unchanged, including cold Atuin overheads of 47.69/59.53 ms and 47.29/93.35 ms
(median/p95). Earlier diagnostics narrow attribution without proving a native
Rust defect or invalidating those failures.

## Full checks and limits

Full smoke pytest result: `1555 passed, 56 skipped in 458.65s (0:07:38)`. [Full smoke](smoke.log); [Diff check](diff-check.log); [Local links](local-links.json).
The final source fingerprints accompany this result. Independent re-audit is
required before completion, even when all local checks pass.

R5 library SHA remains
`ac989a041026f49df1d3b544290ee3e67b497a0d3f82fe4785cd3c106e431d57`.
All validation is local macOS arm64; Bash 3.2 covers management and graceful
skipping. No source pin/native bytes/build, budget, release, production definition,
SSH/Linux run, live asset checker, user startup files, staging, commit or push changed.
