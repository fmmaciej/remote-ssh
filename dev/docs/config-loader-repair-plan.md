# Config Loader Repair Plan

Created: 2026-10-27
Status: R1 implemented and independently ACCEPTED; R0-F1 closed

Related: [implementation plan](config-loader-implementation-plan.md),
[implementation record](config-loader-implementation-record.md),
[fresh independent re-audit](config-loader-independent-reaudit.md).

This is the first repair round after the fresh independent re-audit's R0.
The earlier plan audit and implementation audit remain separate historical
reviews. The fresh auditor is `/root/config_fresh_reaudit`; the implementer is
`/root/config_implementer`. The planner changes only this document.

## R1 — preserve failed snapshot initialization

Finding: **R0-F1, P3**, confirmed by the fresh auditor. The config parser and
ownership probes passed in ordinary supported Bash operation; this repair
addresses incorrect success reporting after catalog initialization fails.

### Cause and reproduction

In `shell/config/parse.sh`, `remote_ssh_config_snapshot_init` continues after a
failed `while ... done < <(remote_ssh_config_entries)` input redirection, assigns
the count, and explicitly returns zero. `remote_ssh_config_load` then accepts an
empty snapshot, does no application work, and also returns zero.

The actual trigger is Bash 3.2.57 after the functions have been sourced normally
and the caller subsequently enables POSIX mode. The same catalog redirection
fails in the baseline, whose enabled loader returns one; a standalone call under
`set -euo pipefail` terminates that shell with status one. Current code instead
continues with status zero. Both emit a redirection diagnostic and neither
loads new data. After an earlier successful load, old settings and ownership
markers remain, so the false success can conceal an ineffective reload.

Use the auditor's existing evidence rather than changing its files:

- [Reproduction source](config-loader-reaudit-evidence/behavior-independent/behavior_probe.py)
- [Parser results](config-loader-reaudit-evidence/behavior-independent/parser-results.json)
- [POSIX results](config-loader-reaudit-evidence/behavior-independent/posix-results.json)
- [Frozen R0 gate comparison](config-loader-reaudit-evidence/behavior-independent/posix-gate-R0-results.json)

The pertinent cases are `helper-after-enabling-posix` and
`helper-after-real-rc-then-posix`. Full rc startup already in Bash 3.2 POSIX
mode fails earlier in the baseline too; that is not the regression to repair.
Bash 5.3.20 handles the tested catalog redirection successfully and must retain
its successful loading behavior.

### Minimal repair

The implementer owns only these runtime/test changes and their verification
record. Do not revert other agents' edits, stage/commit/push, or run live assets.

| File | Required change |
| --- | --- |
| `shell/config/parse.sh` | Preserve a failing initialization input-loop/redirection status before count assignment can overwrite it; immediately return it. Stop the raw single-key caller if initialization fails. |
| `shell/config/load.sh` | Check snapshot initialization; on failure stop before reading/applying anything, returning the actual error when enabled and zero when disabled. |
| `dev/tests/test_config.py` | Add focused ordinary/strict status and state regressions on both actual Bash interpreters. |
| `dev/docs/config-loader-implementation-record.md` | Record corrected red/green results, the legacy gate distinction below, final checks, and the R1 handoff. |

Guard the initialization loop itself. The raw lookup propagates its actual
failure immediately, before any path lookup. The loader saves that failing
status immediately and then follows the existing enable gate: return that
status when enabled, or zero when disabled. Both branches stop before any read
or application work. This is a general gate policy, without a POSIX/Bash-version
exception. Do not infer success or failure from whether the count is zero. An
empty successfully enumerated catalog is different from failed redirection.
Do not lose the failing status with a negated `if ! ...` or by checking the gate
before saving `$?`.
No new subprocess, fallback enumeration, producer-status protocol, or POSIX
detection is needed. Process-substitution producer exit status is a separate
mechanism; this finding concerns failure of the consuming input loop/redirection.

The optional config file remains optional: missing/unreadable paths and guarded
config read failures still produce absent entries and the existing cleanup
behavior. Do not change `snapshot_read`, literal parsing, precedence, ownership,
marker names/exports, or the single-pass design. Retain the intended improvement
where raw lookup of a directory is safely absent under Bash 5.3 strict mode.
Do not add support for POSIX mode or change full rc/guide initialization.

The old disabled-config branch explicitly returned zero after its failed loop
in both an ordinary caller and a standalone strict caller. That status and its
unchanged values/markers must be preserved. Only the enabled loader's false
success is the R0 regression; do not also change the earlier disabled policy.

The first R1 plan incorrectly assumed disabled strict execution aborted and
temporarily requested uniform error propagation. The auditor's fresh eight-pair
comparison of frozen R0 trees disproved that assumption: baseline and R0 current
both returned loader/process status zero for disabled normal and strict calls.
Root then required exact preservation of this legacy policy. This correction
remains within R1. Retain the earlier 7-failed/7-passed red output as historical
evidence based on the superseded expectations, and label it accordingly; record
corrected regression results separately rather than overwriting old evidence.

### Regression and verification sequence

1. Add and run the new regression before editing runtime; retain its red output.
   Use `runtime_bash` and sanitized isolated environments, selecting actual
   `/bin/bash` 3.2.57 and `/opt/homebrew/bin/bash` 5.3.20. Source the library before
   `set -o posix`, rather than launching full rc in POSIX mode.
2. Cover enabled fresh load and enabled reload after a successful ordinary load
   and file change. For an ordinary caller, save `$?` immediately after the
   loader, then assert that status and the actual setting plus canonical source
   and loaded-value markers. Bash 3.2 must report failure and preserve prior
   state; Bash 5.3 must report success and apply the new config.
3. In strict cases call the loader as a standalone command, without placing it
   inside `if`, `!`, `&&`, or `||`, which would suppress the `errexit` behavior
   under examination. Assert process status and whether a following sentinel was
   reached. An EXIT trap may record the actual setting/marker state without
   reusing the failing catalog enumeration. The enabled Bash 3.2 case must stop
   with status one; Bash 5.3 must continue with newly loaded data.
4. Include disabled cleanup after a successful ordinary load, in both ordinary
   and strict callers. Bash 3.2 initialization failure must leave the existing
   values/markers intact and return zero, with the following sentinel reached
   even in strict mode. Bash 5.3 must succeed and release owned values/markers.
   These disabled expectations match baseline; keep the corrected distinction
   explicit in the red/green record. Rerun corrected expectations against frozen
   R0 runtime before the final guard change, then against the corrected R1.
5. Apply the minimal runtime repair. Rerun the new tests, the focused config
   suite below, syntax checks with both interpreters, and targeted ShellCheck.
   Confirm the existing optional-file/directory and lifecycle cases still pass.
6. Run `just smoke` after the repair, `git diff --check`, and local documentation
   link checks. Record actual results and failures; do not rewrite R0 evidence
   or claim that an earlier smoke covered this repair.
7. Send the completed diff and red/green verification to
   `/root/config_fresh_reaudit` through `collaboration.followup_task` for
   independent **R1** verification, and notify `/root` of the handoff. The fresh
   auditor owns its report and evidence. No further runtime edit is authorized
   to the planner.

Focused command from the repository root:

```bash
(cd dev && uv run pytest -q tests/test_config.py tests/test_welcome.py tests/test_guide.py -k config)
```

Acceptance requires correct failure propagation and actual state in the new
cases, unchanged successful loading/ownership and optional-file handling, all
required checks passing, and independent R1 acceptance. If R1 or R2 still finds
a problem, the planner prepares R2 or R3 respectively. After unresolved R3,
stop the repair loop and report open findings, attempts, and the needed decision
to `/root`; do not create R4.
