# T1–T2 private foundation integration contract

Source basis: SPEC-MANAGED-TOOL-LIFECYCLE 0.3 and PLAN-MANAGED-TOOL-LIFECYCLE 0.2,
combined `baseline-1/baseline.json`. These modules are private and are not sourced
by public facades yet. T3–T7 must integrate their real protocols before the new
CLI is accepted. This is an implementer checkpoint, not an independent audit.

## Proof and health

`remote_ssh_release_identify DIR [TOOL] [saved]` is A: strict, complete marker
parsing and live root/identity proof, independent of payload existence. `saved`
requires an explicit matching tool and permits retired names only for callers
with validated saved context. It sets `REMOTE_SSH_RELEASE_*` metadata.

`remote_ssh_selector_repair_valid LINK ROOT TOOL VERSION LAYOUT MEMBER LITERAL`
is B: a current exact literal symlink target, matching live marker, real contained
parents and absent-or-ordinary leaf. Missing parents, any symlink leaf, a changed
marker, unsafe `.active`, another literal target or an ordinary selector fail.
It only permits replacement of the selector; it never permits release deletion.

`remote_ssh_release_delete_valid DIR [TOOL] [saved]` is C: A plus an existing
ordinary nonsymlink member and every parent real/non-symlink; libraries must be
readable. `remote_ssh_release_validate` remains the old known-definition-only
C API. Prune must keep that API and its current-definition constraint.

`remote_ssh_release_health ROOT TOOL LAYOUT MEMBER [REQUIRED_PATH...]` checks
structural file health without running payloads. `ms_tool_health TOOL ROOT` adds
saved required paths, typed file/directory manifest and every saved required
alias/main selector; library selectors must be absolute under real `.active`.
`BUNDLE_REQUIRED_PATHS` is optional definition metadata. nvim declares
`share/nvim/runtime`; no pin or asset changed.

## State and records

Source `tools/lib/env.sh`, then `tools/lib/managed.lib.sh` once in the owning
process. `ms_state_load` resolves the physical effective pair, scans every slot,
and loads `MS_ROWS`, `MS_SLOT`, `MS_GENERATION`, `MS_ADOPTED`, `MS_FZF_HINT`.
A genuinely absent metadata root or zero matching pair is new state. Missing,
corrupt, duplicate, foreign-pair, symlinked or incorrectly private existing
records are errors. No caller may turn nonzero into an empty valid set.

State is `$INSTALL_PREFIX/.remote-ssh-managed/locations/NUMBER/state`, with
private real 0700 directories and owned readable ordinary 0600 files. XDG does
not choose it. The fixed NUL header is magic, schema, full prefix/bin pair,
generation, adoption_done, fzf_hint, row_count. Each typed row is tag, explicit
field_count and exact fields. No data file is sourced or evaluated.

| Tag | Fields in order |
| --- | --- |
| member | tool |
| tool | tool, layout, member |
| alias | tool, alias filename |
| required | tool, relative path, file/dir/any |
| manifest | release root, relative path, file/dir |
| release | tool, root, version, layout, member |
| selector | tool, selector path, literal target, root |
| protected | tool, root, pending/partial |
| batch | batch ID, install/uninstall/update/wrapper, tools/refresh/refreshed/settled |
| item | batch, tool, install/uninstall, status, membership-before, phase, ordinal |
| publication | batch, tool, stage, final, version, layout, member, intended/renamed |
| link-intent | batch, tool, selector, absent/link, old literal, new absolute literal, new root, intended/done |
| remove-intent | batch, tool, link/release/absent, path, literal, root, intended/done, required/optional |
| result | historical batch, tool, action, completed/failed/not-run |

`ms_row_add`, `ms_row_find`, `ms_row_drop`, `ms_member_has/set` operate on a
flat array, preserving path whitespace/newlines and delimiters. `MS_INDEX`
points to the first field of a found row. `ms_state_commit` requires the owning
prefix lock, validates all rows and re-reads all slots/generation before a
sibling-temp validation and guarded atomic rename. On failure callers abort
and reload; they must not keep using the proposed in-memory generation.
No temp file/directory is imported as membership or automatically removed.

## Complete inventory, adoption and read-only reports

`ms_inventory_children DIR` captures direct children in `MS_INVENTORY` only
after an explicit NUL producer-status trailer and EOF. It uses no temp file.
`ms_inventory_live` collects bin, `.active` and direct prefix inventory; any
producer/readlink/active-directory error prevents dependent mutation.

`ms_migration_preview` is read-only. It adopts every proven declared active
main or alias, including alias-only nu/nushell, old versions and all layouts.
Inactive releases become evidence/claims only. `ms_migration_commit` runs a
fresh preview under the prefix lock and atomically records adoption_done.
The engine must compare fresh preflight/selection with the approved preview
before this commit. `ms_legacy_hints FILE` is optional and only retains the
informational fzf hint; it never contributes membership or writes the file.

`ms_report_begin` and `ms_report_end` fence generation and live tickets, including
registered mutator children. Build the entire report in memory between them;
print only after the final fence. Reports create no state or lock storage.

`ms_claims_collect [all|prune]` reads every slot and journal without recovery.
It returns `MS_CLAIM_PATHS`, `MS_CLAIM_SELECTORS`, and foreign-only versions of
both arrays. Pending publications/intents and protected evidence are included,
even for dead writers. `prune` mode excludes ordinary release claims of the
current pair, preserving the ability to prune its inactive releases; other
pairs' claims and all pending evidence remain protected. A malformed or
incomplete slot image blocks deletion. Recollect before each prune deletion.

## Locks, signals and external mutation lifetime

`ms_lock_plan COMMAND EXECUTABLE_BOOL` returns `MS_REQUIRED_LOCKS`. Install,
uninstall and wrapper need prefix plus bin when executable selectors may change;
libraries/state-only operations need prefix. The prior journal can enlarge the
set. Update also needs checkout; prune only prefix. Compute read-only before
confirmation, acquire afterward, then reload/recompute under locks. A changed
set requires release/re-acquire without mutation. Create missing selected roots
only after confirmation, then re-resolve the same physical pair.

`ms_lock_acquire ROOT...` physically resolves, sorts and deduplicates roots.
Bakery storage is inside each root. Atomic participant mkdir marks choosing,
then a private positive ticket is published. Complete scans wait for choosing
or smaller (ticket, token) pairs. Dead participants are ignored without deletion;
PID reuse/uncertainty is conservatively busy. The default timeout is 15 seconds.
Only the actual owner Bash process can pass `ms_lock_holds`; staging children
cannot publish through this API. EXIT/HUP/INT/TERM clean only verified own files.

Every lifecycle publication, rename, unlink, deletion and mutating Git utility
must use `ms_lock_mutate_guarded GUARD ARITY GUARD_ARGS... COMMAND ARGS...`.
It starts a blocked child, registers that exact PID in every held ticket, arms
it only afterward, revalidates the guard in that child and execs the utility
in that same PID. If the owner is SIGKILLed, the live mutator keeps all roots
busy until its utility exits. This also fences reports/prune. Raw
`ms_lock_mutate COMMAND...` exists for cases whose caller already has a complete
non-path guard; prefer the guarded variant for engine operations. T5 fetch/reset
must retain checkout ownership with the same runner. Do not assume that merely
calling a utility from the owner Bash prevents a lingering child from publishing.

## Journal gate and checkpoints

Every lifecycle entry, including the low-level wrapper, must reload under the
correct lock set and call `ms_recovery_gate` before it determines a new batch.
It settles a proven completed install/uninstall with membership in the same
atomic generation. Safe partial results retain membership-before and receipts;
unresolved evidence returns nonzero and cannot be overwritten. Full preflight
must run again after normalization; changed choice/collision ends the old consent.

`ms_journal_begin COMMAND ACTION TOOLS...` requires a gate stamp equal to the
current generation. If adoption committed in between, call the gate again.
It archives prior outcomes and preserves failed publication roots as protected
evidence. It records ordered queued items and membership-before. Metadata changes
for new tools can be assembled in memory before this journal commit.

`ms_journal_item TOOL STATUS PHASE` checkpoints transitions. Before staging or
publication, write the old selector states, publication receipt, manifest and
per-link intention with `ms_row_add` and `ms_state_commit`; only then mutate disk
through the guarded runner. `ms_journal_complete TOOL` is a private low-level
state checkpoint: the engine must first verify its entire tool-specific receipt,
all selectors and health (or complete uninstall absence/scope). It changes
membership and completed status together. `ms_journal_fail_tail TOOL` retains
membership and records failed/not-run outcomes; it is not permission to delete.

Recovery handles completed-on-disk installs, partial alias rollback only while
selectors still point to the exact owned new target, and completed-on-disk
uninstall tombstones before any unrelated new batch. It never recursively
removes releases. Missing C evidence, foreign substitutions or incomplete
required selector scope retain the running journal and block every entry.
Refresh/refreshed journals intentionally block here until T5 implements the
fresh-code continuation; no update success is claimed by this foundation.

## Remaining integration

T3–T7 still own actual staging receipts/manifest generation, engine selection,
consent/collision preflight, public install/uninstall/update facades, fresh-code
continuation, report rendering/routing, prefix-only prune integration, bootstrap
and documentation changes. Existing callers keep their previous public behavior
in this checkpoint. Full smoke and independent implementation audit happen only
after that integration. Do not publish a partial new public CLI from these files.
