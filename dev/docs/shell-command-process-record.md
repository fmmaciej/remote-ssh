# Shell command process record

Date: 2026-10-29
Status: plan ACCEPTED at R0; user approved implementation; implementation ACCEPTED at R0.

## Request and authorization

The user requested a plan for an explicit `remote-ssh shell` command after
accepting the proposed interface: ordinary no-argument `remote-ssh` keeps its
short help, while `shell` starts a new interactive Bash session using the
effective checkout's rcfile. The caller's current directory is preserved and
exiting the environment returns to the parent shell. No startup file or default
shell change is intended.

The existing agent workflow applies: separate planner, independent plan audit,
presentation of the accepted concrete plan for explicit user implementation
approval, then a fresh implementer and a fresh implementation auditor. Initial
audit is R0, with at most R1 through R3 for concrete revisions. No R4. This
request authorizes planning and plan audit only.

## Ownership and existing work

`shell_command_planner` owns only `shell-command-implementation-plan.md`.
The coordinator owns this process record and `shell-command-planning-evidence/`.
A separate plan auditor will own its report and any dedicated audit evidence.

The current working tree contains the independently accepted installed-CLI
implementation and unrelated welcome work, together with their plans, reports
and evidence. These are the effective baseline, not changes to revert. The
starting HEAD is `39226a2d9074acf08279e7c3edde6a51cc2a629c`.

[`worktree-before.json`](shell-command-planning-evidence/worktree-before.json)
records fingerprints of pre-existing dirty files/evidence and relevant source
inputs. All are to remain unchanged during planning. No runtime, test, existing
documentation, installation, staging, commit, push, publication, live asset
check or real-user configuration change is authorized in this planning phase.

## Checkpoints

- Captured the current working-tree baseline before plan authoring.
- Assigned a separate planner with ownership limited to the new plan document.
- The planner completed
  [`shell-command-implementation-plan.md`](shell-command-implementation-plan.md).
  Submitted R0 SHA-256:
  `cf52fce5f2e665c04316d08c9f7f112a40a30733fb62de43f30101f1da1e1124`.
  The coordinator preserved its exact
  [R0 snapshot](shell-command-planning-evidence/plan-r0.md).
- Assigned `shell_command_plan_auditor` to the independent R0 review, with
  ownership limited to `shell-command-plan-audit.md` and its audit evidence.
- Coordinator checks show all 277 fingerprinted pre-existing inputs unchanged;
  `git diff --check` passes. No implementation tests were run.
- User approval of an independently accepted concrete plan remains pending.
- The independent [plan audit R0](shell-command-plan-audit.md) returned
  **ACCEPTED**, with no blocking findings. Its non-blocking implementation notes
  address PTY job-control cleanup, pre-install guide execution, and actual
  interpreter-version evidence.
- Accepted plan SHA-256 remains
  `cf52fce5f2e665c04316d08c9f7f112a40a30733fb62de43f30101f1da1e1124`;
  audit SHA-256 is
  `edd51255423e71f8ce15bd46078262db2cf706253da40e2b69ceeeae8d9d0c5b`.
- Coordinator closure check confirms the plan matches its R0 snapshot, all
  277 pre-existing fingerprints are unchanged, and `git diff --check` passes.
  Present the accepted concrete plan and audit to the user before assigning
  implementation. No runtime or test changes occurred during this phase.
- The user explicitly approved implementation with "Implementuj" on
  2026-10-29. Approval applies to accepted plan SHA-256
  `cf52fce5f2e665c04316d08c9f7f112a40a30733fb62de43f30101f1da1e1124`,
  required verification, and independent implementation audit. It does not
  authorize staging, commit, push, publication, live asset checks or installation
  in the real user home.
- Immediately before implementation, the coordinator verified the accepted plan
  and audit fingerprints and all 277 baseline fingerprints: zero mismatches.
- Assigned the fresh `shell_command_implementer` to the accepted 15 source/test/
  documentation paths and its new implementation record/evidence. The accepted
  plan and audit remain immutable; the coordinator retains this record and
  planning/coordinator evidence ownership.
- Recorded the 264 protected pre-existing files outside that source scope in
  [`protected-before-implementation.json`](shell-command-planning-evidence/protected-before-implementation.json).
  Full smoke will be run by the coordinator using the established project
  runtime and appropriately permitted fresh-session launcher after the final
  focused checks and source freeze.
- First implementation-focused attempt completed with 175 passed and 10 failed
  (90.61 seconds). Eight PTY failures exposed sandbox denial of `/bin/ps` and
  defensive cleanup shortcomings in the new test harness. Two existing install
  override assertions still expected the removed manual-rcfile footer.
  The failed log and result remain in implementation evidence. Coordinator
  permitted the minimal semantic adaptation of that existing override test,
  extending the original extraction-only test-file scope for this necessary
  expectation change; the runtime contract and accepted plan are unchanged.
- A permitted process scan after that completed attempt found no matching
  task-owned supervisor or fixture-path PTY processes. Implementation may now
  correct its scoped harness before a fresh permitted focused run. The new
  coordinator supervisor tracks descendant identities, including separate
  job-control process groups, and records source/protected fingerprints.
- The first permitted focused run completed with 179 passed and 6 failed in
  107.54 seconds. All tracked inputs stayed unchanged; the coordinator verified
  zero surviving tracked descendants. Two Zsh failures were literal diagnostic
  tokens appearing in terminal echo; two Bash parent-return cases reached the
  expected return markers before timing out on final parent shutdown; two
  cleanup cases also timed out on direct-parent shutdown in the new harness.
  These are pre-audit implementation corrections, restricted
  to the test harness. Original failed evidence is retained as `focused.log`
  and `focused-result.json` in coordinator evidence.
- The permitted `focused-rerun` also completed with 179 passed and 6 failed;
  terminal assertions completed, but parent shutdown still timed out. Its
  evidence was retained. Before the coordinator interruption, the implementer
  compared the existing PTY helper and corrected master-descriptor closure to
  precede direct-child waiting, retaining all assertions and bounded cleanup.
  Static checks passed. Latest candidate:
  `shell-command-implementation-evidence/final-master-close-source-hashes.json`.
- Following the user's "Coś przerwało, kontynuuj", the coordinator resumed the
  remaining authorized gates and launched permitted `focused-final` on this
  candidate. Source and protected fingerprints are recorded around the run;
  full smoke and the independent implementation audit remain pending.
- `focused-final` passed: **185 passed in 73.11 seconds**, exit 0. All 15
  candidate and 264 protected fingerprints stayed unchanged; no tracked
  descendants survived cleanup. Launched unfiltered `just smoke` on this same
  candidate via the offline project-Python coordinator supervisor.
- Assigned fresh independent `shell_command_impl_auditor` ownership of only
  `shell-command-implementation-audit.md` and dedicated audit evidence. Read-only
  code/scope review may proceed during the final smoke run; final audit verdict
  is explicitly gated on its completed raw result and coordinator handoff.
- Full unfiltered offline permitted `just smoke` passed: **996 passed,
  58 skipped in 373.93 seconds**, exit 0. The supervisor recorded no timeout,
  unchanged source/protected fingerprints, and no surviving tracked descendants
  (2357 identities tracked). Raw `smoke.log` and `smoke-result.json` remain in
  coordinator evidence. The coordinator handed the complete gate to the
  independent R0 auditor and requested a record-only update from the implementer.
- Independent [implementation audit R0](shell-command-implementation-audit.md)
  returned **ACCEPTED**, with no actionable or blocking findings. Report SHA-256:
  `040f14db55ac3cd0989d444bcfa15018bd7a797cab98b5416570a51119fa8485`.
  No repair round is required. The coordinator's final
  [closure check](shell-command-coordinator-evidence/closure-check.json) confirms
  all 15 candidate and 264 protected fingerprints, immutable accepted plan/audit
  hashes, both successful raw gates and `git diff --check`. Implementation and
  the authorized process are complete. No staging, commit, push, publication,
  real-HOME install or live asset check occurred.
