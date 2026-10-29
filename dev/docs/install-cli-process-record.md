# Install CLI process record

Created: 2026-10-28
Status: implementation ACCEPTED by fresh independent audit R1; work complete.
Baseline HEAD: `39226a2d9074acf08279e7c3edde6a51cc2a629c`

## Authorization and sequence

The user accepted starting the previously described agent workflow: a separate
planner, independent plan audit, and presentation of an accepted plan to the
user before implementation. This is authorization to perform planning and plan
audit. It does not replace the later explicit approval of an accepted plan.

The coordinator assigned plan authoring to `install_cli_planner`, with exclusive
write ownership of `install-cli-implementation-plan.md`. The independent plan
auditor will own `install-cli-plan-audit.md`. The coordinator owns this record
and `install-cli-planning-evidence/`.

Initial plan audit is R0. Concrete findings return to the planner, followed by
independent re-audit, at most R1 through R3. An unresolved R3 is reported to the
user. A fresh implementer and a fresh implementation auditor follow only after
user approval of the accepted plan. Repairs require a separate repair planner.
No commit, push, live asset test, or installation in the real user home is
authorized by this workflow.

## Existing working tree

Earlier coordinator-authored CLI and installer changes are an unreviewed draft,
not an approved implementation. Their initial fingerprints and unrelated dirty
runtime/test/documentation sources are retained in
[`worktree-before.json`](install-cli-planning-evidence/worktree-before.json).
The accepted plan must assess which draft changes to retain, revise, or remove.

The working tree also contains unrelated welcome optimization work and its
records/evidence. All participants must preserve these changes. During the
planning phase, no runtime, test, or existing user documentation edits are
permitted.

## Checkpoints

- Captured the current HEAD and pre-existing source fingerprints before plan
  authoring.
- The separate planner completed
  [`install-cli-implementation-plan.md`](install-cli-implementation-plan.md).
- Assigned R0 independent plan audit to `install_cli_plan_auditor`, with write
  ownership limited to its report and any dedicated audit evidence.
- Preserved the submitted [R0 plan](install-cli-planning-evidence/plan-r0.md),
  SHA-256 `503e5fb19da5ff45dc3484cc8562dc8169bb7fb6be24e2c712d4f61b9ee38339`.
- Verified that all 20 fingerprinted pre-existing source inputs were unchanged
  during initial plan authoring.
- Independent [plan audit R0](install-cli-plan-audit.md) returned **ACCEPTED**
  with no blocking findings. It records fixture constraints to address during
  implementation and does not certify the inherited draft.
- Accepted plan SHA-256 remains
  `503e5fb19da5ff45dc3484cc8562dc8169bb7fb6be24e2c712d4f61b9ee38339`;
  audit report SHA-256 is
  `8e677edba451d52351a1ac72fc2696b176cee9e96323dde4bd994c33bdf8230a`.
- Coordinator verified that the accepted plan matches the submitted R0 snapshot,
  all 20 fingerprinted pre-existing inputs remain unchanged, and
  `git diff --check` passes. No implementation or test-suite run occurred in
  this planning phase.
- Present the accepted concrete plan and audit to the user. A fresh implementer
  is the next role only after explicit approval of this accepted plan.
- The user explicitly approved the presented accepted plan with
  "Zatwierdzam" on 2026-10-28. This approval applies to plan SHA-256
  `503e5fb19da5ff45dc3484cc8562dc8169bb7fb6be24e2c712d4f61b9ee38339`,
  its implementation, required verification, and independent implementation
  audit. The existing restrictions on publication, commits, live asset tests,
  and installation in the real user home remain in force.
- Assigned execution to the fresh `install_cli_implementer`. Its source ownership
  is the accepted plan's scope; it also owns its implementation record and
  `install-cli-implementation-evidence/`. The accepted plan and plan audit stay
  immutable. A fresh implementation auditor will follow completion.
- Captured
  [`protected-before-implementation.json`](install-cli-planning-evidence/protected-before-implementation.json)
  for the unrelated dirty files, including existing welcome evidence, before
  implementation. These files must remain unchanged.
- During execution, the implementer identified that guarding the existing
  `install_tools` call disables implicit Bash errexit in that function, whose
  current loop can mask an earlier tool failure. The coordinator requested a
  narrow planner-authored scope addendum and independent plan audit before
  allowing edits to `tools/lib/install/install.sh`. The approved purpose remains
  explicit failure propagation, with no tool-selection or transaction change.
  The original accepted plan and audit remain immutable.
- The separate planner produced
  [`install-cli-implementation-addendum.md`](install-cli-implementation-addendum.md),
  SHA-256 `ceddfb157e3bb6709d08b09b3d01f6eae1d1c205d7f9c3505749e3e6302bd09f`.
  Independent [addendum audit](install-cli-addendum-audit.md) returned
  **ACCEPTED**, without blocking findings. The coordinator accepted this narrow
  scope adjustment under the user's approved failure-handling objective:
  only explicit `mkdir` and per-tool error returns inside `install_tools`,
  keeping the existing single batch call and adding the required failure tests.
  The implementer was authorized to apply it. No new public behavior, rollback,
  user setup mutation, or publication was authorized.
- The implementer froze the candidate sources, completed a final focused run
  (94 passed), and started the full offline smoke check. A fresh independent
  implementation auditor, `install_cli_impl_auditor`, began read-only source
  review while the automated check runs. Final audit acceptance requires the
  completed smoke result, final record, and unchanged candidate fingerprints.
  The auditor owns `install-cli-implementation-audit.md` and its dedicated
  evidence; it cannot edit the implementation.
- The implementation auditor independently reproduced R0-B1: the existing
  post-install guide test requires literal double quotes around a simple path,
  while the new shell-safe formatter correctly emits that simple path without
  them. The failed required check blocks acceptance; it is not evidence of an
  unsafe command. The coordinator assigned a separate fresh
  `install_cli_repair_planner_r1` to prepare a minimal, semantic test correction
  in `install-cli-repair-plan.md`. The R0 candidate stays frozen while the
  remaining smoke and audit complete; no repair implementation is yet allowed.
- Completed R0 smoke returned 4 failed, 924 passed, 58 skipped. The final
  independent implementation audit returned **NOT ACCEPTED** with B1 (the
  lexical guide assertion) and B2 (the full verification gate, including tmux
  and welcome terminal cases). No other runtime blocker was identified.
- Coordinator repeated the tmux and all four welcome transport cases outside
  the sandbox, in a new session: 5 passed, exit 0. Evidence is retained in
  `install-cli-coordinator-evidence/r0-terminal-recheck.log` and its result JSON.
  This permits verification without changing unrelated source; final full
  smoke is still required.
- The separate repair planner completed
  [`install-cli-repair-plan.md`](install-cli-repair-plan.md), SHA-256
  `afc10272f6d7f4567a437d234849d9a5011bfc04b05f61009b9355b9dfcbcb6d`.
  The coordinator accepted it: only the identified guide test gains a semantic
  exact-argv assertion, while B2 is addressed through the verification launcher.
  The implementer was assigned R1; runtime and unrelated tests stay frozen.
- Preserved the R0 audit and the pre-repair guide-test fingerprint in
  `install-cli-coordinator-evidence/r0-audit-snapshot.md` and
  `pre-r1-checkpoint.json`. Full R1 smoke will be run by the coordinator outside
  the sandbox in a fresh session after the focused repair checks.
- R1 changed only the planned guide-test case. Final focused checks passed
  (1 exact case and 26 guide/post-install cases); scoped style and diff checks
  passed. Unrelated existing whole-file formatter differences were preserved
  and documented rather than edited. The final 13-file manifest is
  `install-cli-implementation-evidence/r1/final/source-hashes.json`, SHA-256
  `d66ef774b5518865f9576e8a3c0b10808743f7d0ddb0b155aedba37bbc3c55f3`.
- A coordinator start attempt referenced the preliminary R1 manifest and was
  correctly rejected by the fingerprint precheck before running tests. The
  corrected `install-cli-coordinator-evidence/run-r1-smoke.py` references the
  verified final manifest and runs unfiltered `just smoke` offline outside the
  sandbox with `start_new_session=True`. Raw log and result metadata are kept
  separately from all R0 evidence.
- Assigned independent R1 audit to a fresh `install_cli_impl_auditor_r1`.
  It owns `install-cli-implementation-audit-r1.md` and its dedicated evidence.
  Acceptance requires the completed full smoke, final implementation record,
  and preserved source/protected-file fingerprints.
- The first corrected outside-sandbox R1 smoke timed out after 1200 seconds,
  before producing a pytest summary. Its partial log and explicit timeout
  result remain in coordinator evidence. The coordinator verified and
  terminated its remaining task-owned process group. Temporary test state
  located the stall at the first Atuin lifecycle case; this is an observation,
  not an attributed installer defect.
- A bounded diagnostic of all six Atuin lifecycle variants, launched through
  the project's Python environment in a new session, passed (6 passed,
  11.87 seconds). No repository source/test changes were made. The exact cause
  of the earlier hang is not established.
- Started a separate unfiltered full R1 retry through the project runtime,
  offline and outside the sandbox, with a fresh session, closed stdin,
  unbuffered progress, a bounded process-group cleanup, and separate retry
  log/result names. The accepted R1 source manifest still matches all files.
- The complete unfiltered R1 retry passed: `just smoke` exit 0, 928 passed,
  58 skipped, pytest duration 340.90 seconds. Raw output and launch/result
  metadata are in `install-cli-coordinator-evidence/r1-smoke-retry.log` and
  `r1-smoke-retry-result.json`. All 13 frozen sources match before and after;
  a separate coordinator check confirms all 178 protected files unchanged.
  `git diff --check` also passes. Earlier failed/timeout outcomes remain intact.
- Requested the implementer to finalize its record with this outcome before
  the fresh independent R1 auditor issues the final verdict.
- The implementer finalized its verification record, retaining all prior
  outcomes. The fresh independent
  [implementation audit R1](install-cli-implementation-audit-r1.md) returned
  **ACCEPTED**, with B1 and B2 closed and no blocking findings. Report SHA-256:
  `35cedf5e1330a89050261b0394e690d291ce50eb8f0257235135823c81a74b8f`.
- The auditor independently checked the final complete smoke, the semantic
  repair (38 positive/negative probes plus exact-case reproduction), unchanged
  runtime, preserved failed/timeout evidence, all 13 final sources, and all
  178 protected files. No further suite run was needed.
- Coordinator closure check confirms the accepted report fingerprint, all
  source/protected fingerprints, and passing `git diff --check`. Implementation
  and independent verification are complete. Changes remain in the working
  tree; no staging, commit, publication, or real-home installation was performed.
