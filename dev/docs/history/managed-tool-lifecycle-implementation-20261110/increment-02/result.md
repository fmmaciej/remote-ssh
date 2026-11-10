# Increment02 — verified T3/T4/T5 checkpoint

Cycle `managed-tool-lifecycle-implementation-20261110`, repair round 0.
Sole implementer/integration owner: `/root/managed_lifecycle_implementer`.
Basis remains SPEC-MANAGED-TOOL-LIFECYCLE 0.3 and PLAN-MANAGED-TOOL-LIFECYCLE 0.2
from `../baseline-1/baseline.json`. Current source HEAD is
`9a223dcca76072eb9035316d25abf972902d3289`; no actual-checkout Git mutations were run.

T3–T5 are implemented and integrated: real single-engine staged install,
consent/preflight/additive install and explicit uninstall, automatic membership,
prior-journal recovery and same-PID fresh-code update. T6/T7 routing, reports,
prune and final documentation/regressions remain pending. This is an implementer
checkpoint, not independent audit or a claim that all specification AC pass.

## Behavior and safety

Twenty-nine source/test files changed in this increment. [Exact final hashes](source-hashes.json)
and [interfaces](interfaces.md) identify the implementation and remaining consumer
obligations. Existing pinned versions/assets/checksums, private Navi adapter and
fzf definition were preserved; the earlier one-line nvim metadata remains.

The engine validates all selected paths and metadata before consent, stages in a
child, verifies checksum/extraction/library qualification and records a complete
typed manifest before guarded release publication. Every alias is part of health
and publication; pinned complete installs reuse existing payload without download.
Completion and membership share an atomic generation. The low-level script uses
the same lifecycle and confirmation rather than bypassing state.

Uninstall previews selectors, all own releases, management changes and protected
scope before confirmation. Full selection preflight protects foreign substitutions.
It removes every proven selected active/inactive release with C revalidation.
Completed on-disk removal is reconciled before unrelated work. Recognized partial
recursive removal retains member/protected remainder and permits safe later repair;
no receipt or partial classifier permits recursive deletion without live C.

Update adopts/reconciles before refresh, records old/target OIDs and performs Git
mutations through the registered-child lease. It protects managed data and
untracked obstructions, execs fresh private code with the same PID/tickets and
repairs only the saved managed set. Empty-set update is project-only; retired and
unsupported members remain protected. No bare install or public continuation flag
was introduced. Informational update-check behavior remains separate.

## Actual verification

Both `/bin/bash` 3.2.57 and Homebrew Bash 5.3.20 were exercised, including env-bash
children. All assets/transports were local fixtures; Git mutation happened only in
disposable temporary fixture repositories with explicit REMOTE_ENV_DIR.

| Actual run | Result |
| --- | --- |
| Staged initial engine | 2 failed, 6 passed; synthetic bundle used invalid root `.`. Corrected fixture root and reran: 8 passed. |
| Staged public install and uninstall | 30 passed and 22 passed. |
| Staged basic update, fresh code and six-tool adoption | 8 passed. |
| Staged public signal/fault matrix | 24 passed; expanded receipt/reuse/update matrix 34 passed; simultaneous public writers 2 passed. |
| Staged foundation plus CLI/TTY/profile/read-only-library regressions | 184 passed. |
| Migrated existing payload matrix | 228 passed, 8 failed from old automatic/no-selection uninstall diagnostic expectations. Corrected to usage while retaining all unchanged-data assertions. |
| Actual-source managed foundation/engine/CLI/update/fault suite | **232 passed in 810.93s**. [Log](actual-managed-test.log). |
| Actual-source binary/bundle/library/download-failure payload suite | **236 passed in 446.18s**. [Log](actual-payload-test.log). |
| Staged reset overlap plus ordinary update | Initial missing pytest import, then Bash3 process-substitution/case parse failure: 7 failed/7 passed. Producer moved to a separate portable function before actual publication. Corrected run: **14 passed in 132.51s**. |
| Final affected actual-source update/Git-fault/pair/library/config-copy checks | **38 passed in 271.69s**. [Log](actual-final-focused-test.log). |
| Final narrow uninstall preview/own-scope check | **4 passed in 31.21s**. [Log](actual-preview-test.log). |
| Per-file syntax on both Bash versions, shellcheck, project-config Ruff without cache, diff check and final source/basis/preservation hashes | Passed. [Exact commands/results](static-checks.json). |

Tests cover refusal/no-TTY/default-deny and TTY yes; noargs/unknown/profile/support
nonmutation; additive membership and alias repair; bundle required data/manifest;
library qualification flow and read-only bin; retired uninstall; all own releases
and newline aliases; full-selection foreign protection; checksum/selection/archive/
probe failures; actual TERM/SIGKILL publication/removal/reset checkpoints; partial
recursive rm and safe retained-member repair; failed unlink/state rename; completed
uninstall then unrelated install/update without resurrection; completed install
recovery retaining exact repair receipts; reuse-goal crash; two writers; pair/XDG
isolation; first six-tool adoption before fresh rg retirement; untracked and
managed-data reset collisions. Generic new CLI helpers are bounded at 120 seconds.

Earlier failed logs and diagnostic runs are retained beside the passing logs.
One intermediate test-isolation edit repeated the same REMOTE_ENV_DIR dictionary
key; it was removed after Ruff reported it. Final project-config Ruff also caught
an import-spacing issue, now corrected. Neither changed runtime behavior or masks
a failed functional assertion. Full managed/payload suites were not redundantly
repeated after the narrow final guard/help/hint/preview changes; affected actual
cases and static checks were run instead.

## Provenance correction

A broad overlay/fixture copy mistakenly read and copied ignored actual
`dots/git/user.local` into local task scratch. Its contents were never opened by
the model, printed or published; the original configuration was not edited.
This was avoidable. The user was informed by the coordinator (event9).

[Original correction metadata](overlay-provenance-correction.json) records deletion
of two exact overlay copies and sixteen task fixture copies using only ownership
metadata/public code. Copy construction now whitelists tracked/owned source and
excludes local/env/credential paths; an unreadable synthetic-config test verifies
the new fixture does not read or copy them.

The later audit recognized that T1's original library helper could also copy it.
[Bounded follow-up](t1-copy-provenance-followup.json) checked only known task run IDs
702, 713, 724, 726 and 730 with exact library fixture/public-source ownership.
Known T1 directories 702/713 were already absent; no matching remaining eligible
copy was found. Other sessions and unknown run IDs were not enumerated; absence
outside that bounded scope is not claimed. Passing T1 overlay logs without a run
ID were not used to justify broader deletion.

Four unexecuted legacy broad dots-copy sites remain explicitly listed in the
interfaces as mandatory fixes before T6/T7 broader actual-source regressions.
No configuration contents enter these evidence artifacts.

## Limits and next action

No network/live asset checks, source builds, real host installs, SSH operations,
user/global configuration edits or Git add/commit/reset/push in the actual checkout
were performed. Controlled library probe fixtures verify protocol, not native ABI.
Full smoke is deferred until T7 as instructed. No independent audit has occurred.

Coordinator should assign T6/T7 to this same integration owner, including those
legacy fixture-copy fixes, final report/routing/prune/bootstrap/documentation work
and one final smoke before independent implementation audit. No spec/plan blocker
remains at this checkpoint.
