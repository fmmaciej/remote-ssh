# Atuin simplification — independent audit after repair round 1

Date: 2026-11-01

Verdict: **PASS**

Repair rounds used: **1 / 2**

## Scope and disposition

This is the independent re-audit of the frozen round-1 implementation against
the original [simplification plan](atuin-simplification-plan.md) and the new
planner's [repair plan](atuin-repair-plan-round-1.md). The auditor did not make
runtime, test or plan changes. This report is the auditor's only new file.

Reviewed evidence:

- Original baseline: `/tmp/remote-ssh-atuin-before`.
- Pre-repair snapshot: `/tmp/remote-ssh-atuin-pre-repair1`.
- Repair delta: `/tmp/remote-ssh-atuin-repair1.diff`.
- Frozen source manifest:
  `/tmp/remote-ssh-atuin-repair1-frozen-sha256.json`.

**A1 and A2 are closed. No remaining must-fix findings or new nonblocking
findings were identified.** The implementation follows the original
startup-only design and the bounded repair plan. No second repair round is
required on the audited evidence.

## Closure of the initial findings

| Finding | Repair and independent assessment |
| --- | --- |
| A1, P2 — a `bind` alias prevented parsing and backend selection | `shell/rc.d/23-atuin.sh:41` uses the alias-safe `function bind()` declaration. Lines 34–35 disable alias expansion for the entire staging/restoration operation; lines 78–82 restore the previous option. The alias entry is retained. Disabled, absent, successful, partial-failure and external startup cases now reach the intended final backend on Bash 3.2 and 5.3. |
| A2, P2 — a readonly user function bypassed interception and damaged keys on failed init | Lines 28–30 check replaceability using child-only `builtin unset -f bind` before the CLI request at line 32. A readonly function selects clean Bash fallback without requesting init code. Lines 73–76 check restoration/removal; redefining an existing function directly preserves its export attribute. No queue replay, import or HISTFILE suppression follows a failed setup/cleanup. The audit's private dispatch-key loss is prevented. |

The readonly probe does not remove or change the parent's function. With skim,
fallback may intentionally claim only editable Ctrl-R; without skim, the
existing private keys and Ctrl-R survive. A rejected attempt may leave the
early bash-preexec library loaded, which the original plan explicitly allows.
Reload keeps that fallback frozen rather than treating the prior failed attempt
as external Atuin.

The cleanup remains local and bounded. The repair retains the original
eval-helper boundary, callback snapshots, key queue, subshell preflight and
parent replay. It does not add a lifecycle subsystem or alter upstream
recording hooks.

## Compliance with the four original requirements

| Requirement | Assessment |
| --- | --- |
| Select the history backend once per Bash process | **Satisfied.** The early request and completed backend guards remain. Success, disabled/missing/error fallback and readonly fallback stay frozen across repeated reloads, toggle/PATH changes and later user key edits. An independent fresh-child probe selected its own backend while the parent retained its selection. |
| Ctrl-R is the only managed Atuin search shortcut | **Satisfied.** Owned startup retains `--disable-up-arrow --disable-ctrl-r --disable-ai`, followed by explicit emacs/vi-insert Ctrl-R. ATUIN_NOBIND and external ownership remain respected. Normal Up, vi-command `k`, `/`, redo and `?` retain their documented behavior. |
| Disable automatic synchronization | **Satisfied.** Bundled `auto_sync = false` and the other previously audited configuration changes remain unchanged. Import-once and manual sync capability are retained. |
| Load bash-preexec only when needed, before Starship | **Satisfied.** The early selector is unchanged by R1. Disabled/missing/external startup skips our library load, eligible startup precedes prompt initialization, and an existing library is reused. |

The retained features remain consistent with the plan: active owned Atuin
suppresses HISTFILE only after successful setup; fallback preserves explicit
custom/empty/null policy; external Atuin owns its hooks/keys/file policy;
ordinary upstream recording completes reload commands with their actual exit
status. The removed live detach/reattach and pending-entry machinery has not
returned. Bash remains the full-rc target; no Zsh redesign was introduced.

## Independent verification and supplied check evidence

The auditor independently ran the new
`dev/tests/test_atuin_bind_ownership.py`: **28 passed** on Bash 3.2.57 and
5.3.20. Inspection confirms it exercises aliases, ordinary/exported/readonly
functions, both initial `expand_aliases` states, partial eval and explicit
return, external ownership, HISTFILE choices, private maps, callback sentinels,
reload freeze, actual private `bind -x` actions and exit-7 recording. The saved
pre-R1 regression run shows **26 failed / 2 passed**, so the new coverage
distinguishes the broken revision from the repair.

Additional independent isolated probes covered combinations beyond simply
rerunning the implementer's tests:

- Alias plus exported forwarding function, actual builtin Readline query,
  preserved definition/alias/option, and a fresh child selecting fallback:
  **4/4 passed**, both Bash versions and alias expansion initially on/off.
- Actual PTY Ctrl-R with the alias plus exported function after successful
  Atuin startup: **4/4 passed**, emacs and vi insert on both Bash versions.
- Actual PTY Ctrl-R after readonly-function rejection, with alias and skim:
  **4/4 passed** in those same maps/interpreters. No Atuin CLI call occurred.

These probes used temporary HOME/bin state and did not touch the user's
history, credentials or database. The readonly rejection was checked with a
failure-capable fake CLI, establishing that it is never reached rather than
relying on a harmless initializer.

The coordinator supplied final verification on the frozen revision:

- Focused history/init suite, including the local real pinned CLI:
  **202 passed / 4 skipped**.
- Full `just smoke`: **1256 passed / 30 skipped**, exit **0**, 304.84 seconds.
- Bash syntax, shellcheck, ruff and mypy: **passed**.
- Refreshed real Atuin 18.14.1 shared-DB checks on both Bash versions:
  `recording-round1-bash32.json` and `recording-round1-bash53.json` contain
  two sessions with distinct IDs, shared isolated DB, expected cwd/nonempty
  host, exit 7 and nonnegative duration. The unchanged verifier also checks
  reload, `?` and literal `$?` behavior.

The auditor independently checked all **20** frozen manifest hashes with no
mismatches. The coordinator repeated that check after full smoke, also clean,
and reports no edits during the frozen focused/smoke runs. Vendor
bash-preexec, the Atuin 18.14.1 fixture, the tool definition/pin, initial audit,
and repair planner document are byte-identical to the pre-repair snapshot.
The repair delta is confined to the Atuin initializer, its new regression
module, measurement labeling and refreshed recording evidence. Existing skim
and unrelated working-tree changes were preserved. No live asset checks,
staging or commits were performed by this auditor.

## Limits of the conclusion

The original startup timing series is explicitly **PRE-R1** evidence. Its
after-series fingerprints describe `/tmp/remote-ssh-atuin-pre-repair1`, not
the repaired initializer. The README now states this clearly and preserves
the historical samples. Startup timing was not rerun after repair 1; no
measured speedup for the repaired revision is claimed. The original fresh-HOME,
empty-database, cache/order/noise and unmeasured per-command/large-database
limitations still apply.

The documented transient parent-only replay failure remains a bounded-recovery
limitation, as accepted by the initial audit and explicitly excluded from the
repair plan. A failure arising only after a successful inherited-subshell
preflight can leave partial key writes; it is not an absolute transaction.
No new ordinary deterministic trigger was found. This does not reopen A2:
readonly functions now reject before any initializer is requested or staged.

The normal navigation-key contract is supported primarily by Readline map
assertions, supplemented by actual custom private-key and Ctrl-R PTY actions.
The opt-in real-CLI check covers generated AI glue outside the unchanged
offline fixture. Neither the repair nor this audit claims arbitrary user
functions, unrelated readonly helpers, or all possible aliases throughout the
whole rc are supported.

## Verdict

**PASS after repair round 1 / 2.** Both initial P2 findings are resolved, the
four agreed behaviors and retained history/status guarantees remain consistent
with the original plan, and required checks pass on the frozen repaired state.
