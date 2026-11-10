# Increment 01 — T1/T2 verified foundation

Cycle: `managed-tool-lifecycle-implementation-20261110`, repair round 0.
Implementer/integration owner: `/root/managed_lifecycle_implementer`.
Basis: `../baseline-1/baseline.json`, SPEC-MANAGED-TOOL-LIFECYCLE 0.3
(`62a53a9ae528dba9ca1d0943c014c557490bec897d638b998902ca16fe56ffbb`),
PLAN-MANAGED-TOOL-LIFECYCLE 0.2
(`e7d504fe7c5a69a400c9ccae549c4fcb0225dcb980c105ae5e45f4c89a5e7c23`).
Exact source and frozen snapshot bytes were checked before and after implementation.

T1 and the private T2 foundation are implemented and verified at this checkpoint.
Public lifecycle integration remains pending T3–T7. This is the implementer's
verification, not independent audit or a claim that all specification AC pass.

## Changes

Thirteen source/test files were published through the approved hash-guarded
publisher. [Final hashes](source-hashes.json) give the exact evaluated bytes.

- `tools/lib/common/release.sh`: A identity parsing independent of health; B exact
  selector repair with a missing leaf permitted; C live recursive-deletion proof
  with all parents nonsymlinked for every layout. The old validator still requires
  a current definition. Retired saved-context validation keeps the same live C
  proof. Complete marker producer status and literal-target reads fail closed.
- `tools/lib/install-tool/defs.sh` and `tools/defs/nvim.sh`: optional required bundle
  path metadata, including `share/nvim/runtime`; pins, assets and checksums unchanged.
- `tools/lib/managed.lib.sh` and six private modules: strict NUL pair-bound slots,
  complete direct-child inventory, full active-install adoption including alias-only
  nu and all three layouts, saved metadata/claims, atomic per-tool membership,
  ordered journal outcomes, prior-journal recovery gate, read-only generation/ticket
  fencing and dependency-free bakery locks inside their roots.
- Three new pytest files exercise actual isolated filesystem transitions, both Bash
  runtimes, corruption, foreign/permission boundaries, I/O failures, signals and races.

The lock runner registers a blocked external utility's exact PID in all held
roots before arming and execing it. A live registered utility remains busy after
owner SIGKILL. This corrects the owner-PID-only gap without changing the approved
requirements. The delayed-mv test kills and reaps the owner, verifies both roots
and read-only reports stay blocked, releases the old utility, then permits a new
writer. T3–T7 must use the same runner for publication/deletion and T5 Git mutation.

Prune-oriented claims distinguish ordinary current-pair inactive releases from
other-pair claims and pending evidence. Prune can later keep its existing inactive
release contract while protecting every pending final/stage receipt and foreign
slot claim. No prune facade or recovery-on-prune was introduced in this increment.

## Reconciliation with concurrent version work

The original code basis was `15bcb79cee2d1959074d4c70e164d0cae75ee8e2`.
The separate tool-version session completed and committed its work as
`9a223dcca76072eb9035316d25abf972902d3289` while this increment was staged.
Implementation integrates against that current HEAD. No Git mutation was performed
by this implementer. [Preservation evidence](preservation.json) verifies all 26
initially recorded tracked changes, including deleted fixtures; nvim differs only
by the required metadata line. The final existing link-state tests use the new
pins and were re-read, retained and verified without lifecycle edits.

The nvim hunk was held while that session was active, then recreated from current
bytes before guarded publication. No old snapshot replaced a shared source file.
The frozen specification/plan and coordinator-owned execution/events were untouched.

## Actual verification

All tests use isolated temporary HOME/prefix/bin and offline local transports.
Bash versions were `/bin/bash` 3.2.57 and Homebrew Bash 5.3.20; exact version lines
and per-file syntax commands appear in [source hashes](source-hashes.json) and
[static checks](static-checks.json).

| Check | Actual result |
| --- | --- |
| Before lifecycle publication: release ownership + link state + install library | 115 passed, 26 failed in 81.93s; old literal pin expectations during the separate version update. [Observed baseline](baseline-observation.json). |
| Latest isolated publishable foundation overlay | 118 passed in 73.56s. [Raw log](publishable-overlay-test.log). |
| First merged-repository focused run: new foundation + release ownership/link state/library/check/assets | 320 passed, 2 failed in 156.23s. Both regressions were restricted-PATH checks because the complete marker producer resolved `cat` through that PATH. [Raw log](repository-focused-test.log). |
| Corrected merged repository: check + release ownership + link state | 117 passed in 62.42s. The marker producer now uses Bash `command -p cat`, preserving complete status and restricted-PATH diagnostics. [Raw log](repository-regression-test.log). |
| Final merged repository: state + recovery + concurrency | 118 passed in 73.23s, including final pending foreign-slot claims. [Raw log](repository-foundation-final.log). |
| Every changed shell file individually under Bash 3.2 and Bash 5.3 syntax checks; shellcheck; new-test Ruff without cache; git diff --check | All passed. [Exact argv, status and output](static-checks.json). |
| Exact frozen source/snapshot hashes, final published hashes and preservation | Passed. [Hashes](source-hashes.json), [preservation](preservation.json). |

The final runs specifically cover three-layout A/B/C separation after missing
payload/parents and marker/leaf/parent replacement; alias-only old-version adoption;
new partial tools never becoming members; prior successes and failed/not-run tails;
completed-on-disk uninstall tombstones before unrelated batches; retained membership
and unchanged journals for protected substitutions; failing state rename; strict
NUL roundtrip with newline/delimiter paths; corrupt/duplicate/copied/symlinked state;
prefix writable with a read-only parent/bin; complete producer/readlink failures;
pending final releases in another slot; report generation fences; TERM/SIGKILL;
choosing/dead tickets; four simultaneous writers; and lingering external mv ownership.

Ruff's first direct source invocation was blocked from creating its cache in the
external checkout. It was rerun using the approved escalation path with `--no-cache`
and passed; the final no-cache static check also passed. No failed or skipped check
is represented as successful.

## Remaining scope and limits

[Private interface contract](interfaces.md) documents schema field order, caller
protocols and integration obligations. T3–T7 still require staging/manifest receipt
production, complete consent/collision preflight, actual install/uninstall engines,
all public facade routing, fresh-code update continuation, reports, prune integration,
bootstrap and user documentation. The foundation intentionally blocks refresh-phase
journals until T5 provides the continuation protocol.

Public commands retain their previous behavior in this intermediate worktree.
No partial new CLI is exposed. Full smoke is deferred until final T7 integration
as instructed. Live asset checks, downloads, SSH hosts, real user installations,
user/global configuration, native ABI qualification and real Navi/skim integration
were not run in this foundation checkpoint. The new report/migration tests never
execute payloads or load libraries. Independent implementation audit remains pending
after complete integration. No specification/plan blocker remains at this checkpoint.

Next: coordinator accepts this bounded checkpoint and assigns the dependent T3–T7
work to the same sole technical integration owner.
