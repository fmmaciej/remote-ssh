# Atuin simplification — repair plan, round 1

Date: 2026-11-01

Status: ready for the existing implementer; implementation not performed here

Repair budget: this is round **1 / 2**, followed by independent audit

This plan addresses **A1 and A2**, both P2, from the
[independent initial audit](atuin-audit-initial.md). Keep the approved
[simplification contract](atuin-simplification-plan.md). The baseline is
`/tmp/remote-ssh-atuin-before`; the initial implementation delta and frozen
manifest are `/tmp/remote-ssh-atuin-implementation.diff` and
`/tmp/remote-ssh-atuin-frozen-sha256.json`. Preserve these historical artifacts.
The initial frozen smoke passed with 1228 passed / 30 skipped; it does not
cover the two findings and is not validation of this repair.

## Required decisions

- Keep the existing bind queue, subshell preflight and parent replay. Repair
  interception rather than replacing the integration or snapshotting all maps.
- Preserve the user's `bind` alias, existing function and alias-expansion
  setting. An alias must neither prevent parsing nor bypass the queue.
- If an existing `bind` function cannot be replaced, select startup Bash
  fallback **before calling `atuin init`, evaluating its output, or installing
  the temporary wrapper**. Do not try to remove a readonly attribute.
- Keep the final backend frozen on reload, including this new fallback case.
  The early preexec library can remain loaded after this late eligibility
  failure, as already permitted for failed startup; no unload machinery is needed.

## Minimal implementation

Primary runtime ownership is `shell/rc.d/23-atuin.sh`. No change to
`05-bash-preexec.sh`, `06-bash-history.sh` or `20-skim.sh` is expected. Extend
the existing history/lifecycle tests; change other files only if a concrete
regression requires it. Preserve the unrelated skim migration.

1. **Make the wrapper declaration parse safely.** Replace bare `bind() {`
   with the alias-safe Bash form `function bind() {`. This is required even
   for disabled, missing and external Atuin: Bash parses the function body
   before the execution-time branch. Do not globally delete aliases.

2. **Check replacement before any Atuin initialization.** When a `bind`
   function exists, test `(builtin unset -f bind) 2>/dev/null` in a subshell.
   Failure returns unsuccessful setup immediately. This tests removal only in
   the disposable child, leaves the parent's function/attributes untouched,
   and never attempts to make a function writable. With no function, skip the
   probe. Use `builtin declare -F/-f` for presence/capture; save the original
   definition before replacing it. Do not parse modern `declare -pf` attribute
   output: Bash 3.2 does not provide the same output as Bash 5.3.

3. **Protect the whole staging operation from alias expansion.** Remember
   whether `expand_aliases` was enabled; disable it while evaluating upstream
   code, defining its helpers, staging explicit Ctrl-R bindings, and restoring
   the saved function. Keep every alias entry intact. Merely using an
   alias-safe declaration is insufficient: `alias bind='builtin bind'` would
   otherwise expand the initializer's calls into direct parent key writes.
   Restore the original `expand_aliases` state on success and every failure.
   Retain the existing eval helper boundary so an upstream `return 1` cannot
   skip the caller's cleanup. Do not return early after changing shell state.

4. **Require working interception and cleanup before replay.** Check wrapper
   installation and cleanup results instead of ignoring them. If a previous
   function existed, restore its captured definition with `builtin eval`
   while aliases are disabled. Prefer replacing the wrapper directly, without
   unsetting the function first: this also retains an existing export
   attribute. If no function existed, remove only the temporary wrapper.
   A failed setup/restore must not advance to preflight, replay, import or
   `HISTFILE` suppression. Use one small cleanup path, then restore the existing
   callback arrays and select fallback. Do not create a general transaction
   framework or add restoration of unrelated upstream helper definitions.

5. **Keep the bounded transaction unchanged after cleanup.** Only validated
   queued `builtin bind` statements enter subshell preflight and parent replay.
   Queries still use the real builtin; restoring a user function must not
   route replay through it. Keep existing partial-eval, explicit-return,
   missing-helper and deterministic-invalid-keymap failure handling.

Successful owned setup still passes all three flags:
`--disable-up-arrow --disable-ctrl-r --disable-ai`. It installs managed search
only on Ctrl-R in `emacs` and `vi-insert`, honors `ATUIN_NOBIND`, and suppresses
`HISTFILE` only after success. Keep `auto_sync = false`, conditional early
preexec loading, external ownership, import behavior, and startup-only choice.
Readonly fallback uses the existing policy: skim may claim those two Ctrl-R
keys; without skim, keep native/user keys. All other user keys, including
Atuin's private dispatch sequences, must survive a rejected or failed attempt.

## Regression coverage

Reuse the unchanged 18.14.1 fixture, current fake CLI and `runtime_bash`
parameterization. Define test functions before installing the alias, or use
the alias-safe declaration, so the tests themselves reach the intended source.
Use `builtin bind` for setup/assertions to observe real maps independently of
the alias or user function. Add bounded cases rather than a large Cartesian
product.

| Case on both Bash versions | Required assertions |
| --- | --- |
| Alias `bind='builtin bind'`, disabled and binary absent | Full rc sources without syntax errors; backend is Bash; skim fallback works when available and native fallback works without skim; no Atuin init or new preexec load. Repeated reload stays frozen. |
| Alias, eligible successful init; with and without an ordinary existing function | Exactly one init; queued setup succeeds; alias, function definition/absence and `expand_aliases` state are restored. Include an exported function and preserve its export attribute. Only agreed managed search keys change. Exercise initially enabled and disabled alias expansion. |
| Alias plus partial fixture eval ending in `false` and explicit `return 1` | No direct private-key writes escape staging; original function and alias survive; callbacks/HISTFILE recover; Bash fallback is finalized. Include an alias plus ordinary-function combination to test capture/restoration together. |
| Readonly forwarding `bind` function; also with the alias present | Init CLI is never called, wrapper is never installed, no readonly diagnostics, no Atuin callbacks/import or HISTFILE suppression. Function definition and readonly attribute remain. With skim, only editable Ctrl-R fallback may change; without skim all seeded keys remain. Repeat with a partial-failure-capable fake to prove the initializer is never reached. |
| Externally initialized Atuin with alias/readonly function | Backend remains external; no init, wrapper/probe mutation, skim rebinding or new preexec load; existing callbacks, keys and explicit/unset HISTFILE stay owned externally. |
| Reload after success and each new fallback | Change toggle/PATH/binary availability and run `rcrc` twice; no new init or bindings. Later user edits to Ctrl-R and private keys survive. A new Bash can select anew. |

Seed the audit's overwritten dispatch macro `\C-x\C-_A0\a` and representative
private keys from both interpreter paths; compare normalized Readline map
output before/after failed or rejected setup. Preserve the existing Up forms,
`?`, vi-command `k`, `/` and Ctrl-R redo assertions. Include a custom executable
`bind -x` action in failure cases and verify its actual keypress where Bash 3.2
cannot serialize that action reliably. Without skim, verify original Ctrl-R
also survives; with skim, assert its intended fallback ownership separately.

Check pre-existing callback sentinels in `preexec_functions`,
`precmd_functions` and `BLE_ONLOAD`, with no new Atuin registrations after
failure/rejection. Cover explicit custom, empty and `/dev/null` HISTFILE values
across representative cases; retain the existing default and external-unset
coverage. Verify exact alias and function definitions and the shell option,
not just the final backend. Check readonly preservation with a disposable
subshell removal probe after setup; do not mutate the parent's attributes.

Use the existing PTY harness for actual Atuin Ctrl-R in both editable modes,
skim fallback and preserved user actions. Retain prompt-status/pipeline tests
and run an ordinary exit-7 command through recording/callbacks after repaired
startup and reload. Do not assert zero private bindings after successful Atuin:
the pinned integration needs those macros.

## Validation and handoff

1. Confirm the new A1/A2 regression cases fail on the initial frozen runtime
   and pass with the repair, without changing vendor/fixture bytes.
2. Run the focused history/init suite, including PTY tests:
   `test_history_backend.py`, `test_atuin_lifecycle.py`,
   `test_atuin_ownership.py`, `test_atuin_prompt.py`,
   `test_tool_init_shell.py` and `test_atuin_real.py` under `dev/tests/`.
   Confirm actual interpreter coverage is Bash 3.2.57 and Bash 5.3.20; report
   missing coverage explicitly. Supply the local real pinned binary for the
   real-CLI tests; do not download or run live asset checks.
3. Repeat isolated `dev/verify_atuin_recording.py` on both interpreters with
   real Atuin 18.14.1: shared DB/two sessions, distinct session IDs, cwd/host,
   exit 7, duration, reload and `?`/literal `$?` behavior remain covered.
4. Refresh startup measurements with the existing isolated wrapper on the
   repaired state, **or** explicitly label the current after-series as the
   pre-repair revision in its README and final report. Preserve raw samples
   and fingerprints; do not present old timings as measurements of new code.
   If refreshing, keep test/audit work from running concurrently with samples.
5. After all edits, record a separate round-1 delta and SHA-256 manifest.
   Run focused PTY coverage and full `just smoke` on that frozen source state;
   report counts, skips, interpreter versions and exit status. Any subsequent
   source change requires relevant checks again on the new frozen state.
   Do not run `just test-assets-live`, stage or commit.
6. Submit the concrete repair diff, new test evidence, source manifest and
   measurement disposition for independent audit. The repair consumes round
   1; if that audit finds blockers, use a new planner for round 2. Do not begin
   a third repair round without the user's next acceptance.

Acceptance requires A1/A2 repros resolved on both Bash versions, clean
fallback with alias/function/option preservation, unchanged four agreed
behaviors, no vendor/pin/unrelated skim changes, and passing required checks on
the final frozen revision. No unresolved design choice blocks implementation.

## Explicitly outside this repair

The audit accepted the residual transient parent-only replay failure as a
bounded recovery limitation. Keep documenting it; do not rebuild rollback for
fault injection that changes behavior only after successful subshell preflight.
General alias hardening of the whole rc, arbitrary user-function behavior,
readonly unrelated Atuin helpers, preexec unload, live backend switching,
Zsh redesign, large-database/per-command performance claims and Flyline remain
outside scope. Preserve existing direct-module Zsh tests and all normal
recording/status guarantees.
