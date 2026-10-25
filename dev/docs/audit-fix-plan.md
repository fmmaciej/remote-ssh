# Repository Audit Fix Plan

Created: 2026-10-16
Updated: 2026-10-24
Status: live-wrapper pipeline repair implemented and verified

Repair installation, update, removal, and shell helper correctness before
changing startup behavior or tool profiles. Performance and simplification
ideas are deferred in [Shell Startup Benchmark TODO](../todo-bench.md).
The earlier [refactor audit plan](refactor-audit-plan.md) records a different
audit cycle.

## Pipeline state at a prepended wrapper boundary

Created: 2026-10-24. The subsequent independent audit found one P2 regression
introduced by the preceding repair. This section is the current implementation
plan and implementation record; the completed sections below remain historical
records.

### Finding and baseline

The compatibility entrypoint in `shell/rc.d/23-atuin.sh` captures `PIPESTATUS`
before helper work, but forwards that capture only when the serialized statement
replaced a vendor prologue (`mode=1`). When it was prepended before a bare user
wrapper (`mode=0`), its local capture disappears on return. The wrapper then
invokes the ordinary dispatcher, which captures only the returned status.

The audit reproduced this in a real Bash 5.3.20 PTY with the unmodified Atuin
18.14.1 fixture and a wrapper evaluating the saved ordinary vendor prompt:

| Final pipeline | Ordinary wrapper control: status / `BP_PIPESTATUS` | Disable integration and reload: status / `BP_PIPESTATUS` |
| --- | --- | --- |
| `(exit 4) \| (exit 0)` | `0 / (4 0)` | `0 / (0)` |
| `(exit 4) \| (exit 7)` | `7 / (4 7)` | `7 / (7)` |

The previous argument stayed correct, and the owned history entry ended once
with the correct status. The defect is loss of individual pipeline statuses at
the later user callback. A comparison with the pre-repair runtime confirmed
that this is a regression. Bash 3.2.57 has its own vendor capture limitation;
compare it with its matching control rather than imposing modern Bash results.

The audited focused history/initialization suite passed **364 tests with 36
skips in 230.47s**. The preceding full `just smoke` passed **688 tests with 36
skips in 302.82s**. Neither result covers the missing live bare-wrapper metadata
case; retain these as baselines, not acceptance of the new repair.

Scope: `shell/rc.d/23-atuin.sh`, `dev/tests/test_atuin_prompt.py`, shared cleanup
assertions in `dev/tests/test_atuin_ownership.py`, and the history documentation
in `docs/shell/helpers.md` if its guarantees or lifecycle explanation change.
Reuse the existing PTY helper and unmodified pinned vendor fixture. Tool pins,
runtime dependencies, vendor code, and shell startup simplification stay outside
this repair.

Full-suite verification also required a developer-only clone fixture correction
in `dev/tests/test_update.py`, detailed in the implementation record below.

### 1. Add the missing regression and its controls

- Use a bare forwarding wrapper with scalar `PROMPT_COMMAND` to reproduce the
  live `mode=0` path when Atuin is disabled and the shell configuration reloaded.
  Feed the final pipelines above as raw PTY input; `PtyShell.command` appends a
  marker that would replace the pipeline being tested.
- For each case, first measure the same wrapper and vendor dispatcher without
  the owned detach prologue. Compare callback-visible status, pipeline vector,
  previous argument, callback order, and count with that control. Assert the
  full two-element vectors explicitly on modern Bash. Assert one owned end
  event with the original status, and no duplicate end on the next prompt.
- Retain a separate control where a user prefix intentionally changes pipeline
  state before forwarding to the wrapper. Match that layout's ordinary behavior;
  restoring the original vector unconditionally would introduce another bug.
  Keep the existing chronological prefix/wrapper/callback/tail trace.
- Demonstrate the bare-wrapper failure on the audited runtime before editing
  it. Run scalar cases on both supported Bash versions and add representative
  supported array/sparse layouts without multiplying every lifecycle dimension.

### 2. Prove metadata transfer without moving user dispatch

- Prototype the `mode=0` path in isolated PTYs before choosing its runtime form.
  The design must pass both the bare-wrapper controls and the prefix controls
  from step 1. Do not simply enable whole-dispatch delegation for `mode=0`:
  user callbacks must remain at the wrapper's existing position.
- Preserve the current command's pipeline information until the ordinary
  dispatcher consumes it. Account for the vendor capturing its inputs again;
  restoring only `$?` or retaining a local array until the entrypoint returns
  cannot solve this path.
- Distinguish effects of our boundary helper from legitimate prefix effects
  using a proven runtime protocol. Do not infer this from wrapper names, inspect
  or evaluate user function bodies, or assume every prefix preserves metadata.
  If a proposed transfer cannot preserve both controls, revise the boundary
  mechanism before promotion rather than adding a blanket pipeline override.
- If the design needs a transient handoff, give it an authenticated token and
  an explicit consume/expire lifecycle. Its lifetime is separate from the
  detached history record: finishing that record clears pending history state
  before the later wrapper dispatch. Cleanup must neither erase a still-needed
  handoff nor leave it available to an unrelated later command.
- Retain strict origin validation and conservative expiry. A stale token must
  not consume a newer token's metadata or alter a newer live Atuin ID/time.
  Do not use command text, `HISTCMD`, or timing thresholds to associate prompts.
  If the intended dispatcher never runs, expire metadata before a later input
  can consume it; discard uncertain ownership rather than attaching it late.
- Preserve the compact serialized statement compatibility and the working
  `mode=1` dispatch path, including cached old statements. Keep transient names
  private, let user callbacks edit their global callback array, and remove an
  owned hook before invoking user callbacks. Do not copy the vendor callback
  loop, replace its dispatcher permanently, or add a DEBUG/PS0/PS1 observer.

### 3. Exercise cleanup and integration boundaries

- Check repeated disable/reload cycles, successful consumption, lost/replaced
  prompt boundaries, skipped dispatch, and available-helper/backend failure
  paths. Prove that a later command cannot receive the previous vector or a
  second end event after either consumption or expiry.
- Extend shared cleanup assertions for any new state. Keep existing stale/new
  token, cached-wrapper replay, newer live state, user-global variable, callback
  array mutation, missing helper, and failed-end regressions passing. Add focused
  cases where the new metadata lifetime actually crosses these boundaries.
- Include representative function/source reload and real-startup cases, while
  preserving the documented conservative discard for directly entered multiline
  blocks. Report unsupported legacy array cases as skips, not coverage.

### 4. Verify and record the completed repair

- Run the five-file focused suite shown in the historical repair section below,
  then `just smoke`. Check explicit Bash 3.2 syntax, Ruff lint/format for changed
  Python files, `git diff --check`, and local documentation links. Do not run the
  live asset checker. Record actual counts and version-specific skips.
- Review the final diff separately from test execution, checking callback order,
  metadata lifetime, and compatibility cleanup. Keep independent audit findings
  distinct from test results; a green suite alone does not close this finding.
- Update this section with the chosen protocol, red/green evidence, measured
  verification results, and any remaining limitations. Qualify earlier claims
  that the existing metadata tests covered every live wrapper layout.

### Acceptance checklist

- [x] Bare live wrappers reproduce the defect before repair and preserve the
  matching control's metadata afterwards for both final statuses.
- [x] Modern Bash callbacks receive `(4 0)` and `(4 7)` in the respective bare
  wrapper cases; legacy Bash matches its own unmodified vendor control.
- [x] Prefix effects, callback position/count, previous argument, and user state
  match their corresponding ordinary prompt layouts.
- [x] Owned history ends once with the correct status; completion or
  expiry leaves no metadata that can affect a later command or newer token.
- [x] Existing direct/stale dispatch, cached formats, reload/startup, supported
  sparse arrays, callback mutations, and failure cleanup remain covered.
- [x] Documentation and verification results are updated; final review is
  recorded without treating prior green tests as proof of this repair.

### Implementation and verification record

- The isolated prototype established that Bash 5.1+ restores the original
  status, pipeline vector, and previous argument before each separate
  `PROMPT_COMMAND` array entry. A prepended `mode=0` boundary now occupies its
  own entry. Bash then supplies the original metadata to the existing prefix
  or wrapper; no saved-vector override or extra precmd handoff is needed.
- Cleanup runs before user prompt code. It restores a temporary scalar's type
  and current export flag, or an array's original indices. Only the occupied
  initial array segment is shifted to free index 0; sparse entries beyond it
  stay in place. Edits to retained entries and added entries survive cleanup. A scalar
  with user-added array entries remains an array. Reversal requires the exact
  owned entry at index 0, so a replacement prompt is not rearranged on expiry.
- `REMOTE_SSH_ATUIN_PENDING_LAYOUT` records only this temporary layout. Existing
  pending-state cleanup clears it on completion, failure, or expiry. There is
  no new retained command metadata that could leak into another input. Shared
  assertions now require this field to be unset as well.
- The serialized statement, token authentication, context validation, `mode=1`
  delegation, and vendor code are unchanged. Bash 3.2 keeps its existing path
  and is checked against its own unmodified vendor control. No runtime
  dependency, observer, or user-function inspection was added.
- Before the runtime edit, the new bare-wrapper matrix reported **6 failed,
  2 passed, 4 skipped in 6.94s**. All six modern Bash cases lost the first
  pipeline status. The isolated runtime prototype then passed the bare-wrapper
  and prefix matrices: **20 passed, 8 skipped in 22.30s** on Bash 3.2.57 and
  5.3.20, before promotion to the working tree.
- Regression coverage now also checks two callbacks, repeated disable/reload,
  a different following pipeline, callback-visible global state and callback
  array edits, exact layout restoration, prompt edits/deletions, failed/missing
  completion infrastructure, and replay of saved array prompts after either
  completion or expiry. The prefix tests inspect the incoming pipeline as well
  as the callback metadata after the prefix intentionally changes it.
- The initial focused suite passed **389 tests with 55 skips in 291.06s**.
  Final diff review then found that restoring the initial export flag would
  discard an intervening user export/unexport. Both added tests failed before
  that refinement (**2 failed, 9 passed, 11 skipped in 6.92s**). Cleanup now
  uses the current flag; the expanded layout matrix passed **11 tests with 11
  skips in 7.05s**. No new state is required to preserve this edit.
- The final focused history/initialization suite passed **391 tests with 57
  skips in 303.81s** after the export-flag refinement. The 21 additional skips
  relative to the audited baseline are new array-only scenarios on Bash 3.2;
  existing legacy scalar and lifecycle tests continue to run.
- The final diff review checked exact-entry ownership before layout reversal,
  preserved sparse indices and user edits, stale/new-token isolation, and
  cleanup after missing dispatch. Verification comprises tests and an
  implementer review.
- The full run after the export refinement reported **714 passed, 57 skipped,
  1 failed in 345.23s**. The failure reproduced independently in the update test's
  repository setup, before any updater execution. `git fsck` found the source
  repository intact and the local bare clone missing objects. An isolated
  prototype using `git clone --no-local --bare` passed. This developer-only
  fixture change now uses Git's transfer protocol instead of copying a source
  object directory that can be repacked concurrently; public update behavior
  is unchanged. All **12 update tests passed in 2.82s**, with Ruff lint/format
  checks passing. This is the only scope addition to the repair files above.
- Final `just smoke` after the fixture correction: **715 passed, 57 skipped in
  337.59s**. Bash syntax, ShellCheck, Ruff, and mypy passed. Explicit Bash 3.2
  syntax, Ruff lint/format for all three changed test files, `git diff --check`,
  and local documentation links passed as well. The live asset checker was not
  run. No vendor fixture, tool pin, or runtime dependency changed.

## Prompt dispatch, cached registrations, and pipeline state

Created: 2026-10-24. The three P2 findings were implemented and passed the checks
recorded below. A subsequent independent audit found the live `mode=0` wrapper
pipeline regression planned above. This section records the preceding repair;
its checked items do not establish that the new finding is resolved.

| Finding | Reproduction and required behavior |
| --- | --- |
| A wrapper evaluating a saved pending prologue stops normal dispatch | Save the prompt while detach has installed its temporary statement, allow that entry to complete, reactivate Atuin, then invoke the saved text through a function. The audit observed zero user callbacks; Bash 5.3 started two later entries without ending either, while Bash 3.2 also stopped invoking preexec. Restore ordinary dispatch and rearming without reviving the detached ID. |
| The temporary prologue invokes user callbacks before their prompt prefix | A multiline prefix prepares a value and forwards status 7 to a saved dispatcher through a wrapper. Before the repair, the trace was `prefix -> callback:new:7`; the current implementation produces `callback:old:7 -> prefix` on both Bash versions. Only owned history completion may run early; user callbacks must retain their position relative to the prefix and tail. |
| Replaying an old prompt loses individual pipeline statuses | A normal Bash 5.3 dispatcher reports `BP_PIPESTATUS=(4 7)` after `(exit 4) \| (exit 7)`. Restoring the saved pending prompt instead reports `(7)`, although `$?` and the previous argument remain correct. Preserve the current command's metadata when handling stale code. |

The audited checkout passed the focused history/initialization suite with
**332 passed, 30 skipped in 238.24s**. The earlier full `just smoke` result was
**656 passed, 30 skipped in 283.42s**. These are baselines: the existing tests
miss callback/prefix interleaving and pipeline metadata during saved-prompt
replay, and restore saved text directly rather than through a cached wrapper.

Scope: `shell/rc.d/23-atuin.sh`, `dev/tests/test_atuin_prompt.py`, the shared
cleanup assertions in `dev/tests/test_atuin_ownership.py` if their state contract
changes, and the history section of `docs/shell/helpers.md`. Reuse the PTY
helper, fake CLI, and unmodified Atuin 18.14.1 fixture. No vendor edits, tool pin
changes, runtime dependencies, or shell startup simplification are included.

### 1. Establish all three failures before changing runtime code

- Add a cached-wrapper regression on Bash 3.2 and modern Bash. Save the pending
  prompt text before the first completion prompt, then let that entry complete
  and reactivate Atuin. A function must evaluate the saved text on later prompts.
  Compare with the same wrapper holding an ordinary saved vendor prompt. Check
  callback counts and rearming at the first restored prompt, then correlate
  start/end IDs for two subsequent ordinary commands after the control's normal
  rearming sequence. The detached ID must still have exactly one end event.
- Repeat the cached-wrapper case when the original completion boundary was
  missed. Its detached ID must receive no late end event, while newly active
  commands and user callbacks recover normally. Repeated replay must not need
  manual resetting of `PROMPT_COMMAND`.
- Test old serialized statements as well as statements generated by the repaired
  implementation. Keep a small literal fixture of the audited statement format
  in the test; do not depend on a temporary backup or a second checkout. Existing
  interactive sessions can retain that old format after `rcrc` loads new code.
- Replace the split callback/prompt logs in the order regression with one
  chronological trace. Record prefix, wrapper, every user callback, and tail in
  that trace; the prefix must prepare data actually read by a callback. Save and
  restore status 0/7 in the prefix so the test cannot confuse order with a lost
  `$?`. Compare against the same configured prompt without an owned detach
  registration, rather than against a different default prompt layout.
- Add pipeline replay tests for a saved pending prompt restored directly and
  through a wrapper. Feed raw PTY input so the execution marker appended by
  `PtyShell.command` does not overwrite the pipeline under test. Check `$?`,
  `BP_PIPESTATUS`, the previous argument, callback order, and callback count.
  On modern Bash the direct normal-dispatch control must retain `(4 7)`;
  compare legacy Bash with its own unmodified vendor control instead of fixing
  an upstream Bash 3.2 capture difference in this change.
- Cover scalar and supported array/sparse prompt forms. Exercise real startup
  and an existing interactive shell in representative cases rather than taking
  an unnecessary Cartesian product of every existing lifecycle parameter.

### 2. Separate the owned completion boundary from user dispatch

- Replace the assumption that entering our temporary prologue should invoke all
  `precmd_functions`. Preserve the existing dispatch position: when the vendor
  statement is already first, callbacks naturally run there; when a user prefix
  forwards to a wrapper, those callbacks must remain after that prefix.
- At the first actual prompt boundary, authenticate the live registration and
  capture the origin and current command metadata before helper work can change
  them. Complete only our detached history there, or retain a validated boundary
  record for its finalizer. If completion is deferred, record its end time at the
  boundary as well; user prompt work must not inflate its history duration.
- Keep strict origin/expiry validation. A later wrapper callback may consume
  only a boundary already authenticated for this input; its shifted line number
  must not authorize an old record. Do not weaken the context comparison or
  replace it with history text, timing thresholds, or fixed line offsets.
- Prototype the capture/delegation sequence in isolated PTYs before committing
  to its runtime form. It must pass the combined order and metadata controls on
  both Bash versions. Capturing data and then calling the existing dispatcher
  from an arbitrary helper is insufficient: that dispatcher captures its inputs
  again. Restoring only `$?` through `__bp_set_ret_value` is also insufficient.
- If metadata needs an explicit handoff, keep it private to one authenticated
  prompt invocation. Verify that the eventual dispatcher cannot overwrite the
  handoff before the first user callback, and that later callbacks see the same
  values. Do not install a permanent dispatcher replacement, copy the vendor's
  callback loop, or add a DEBUG/PS0/PS1 observer to work around capture ordering.

### 3. Make stale replay compatible with cached wrappers

- Retain a compatibility entrypoint for the audited `__rs_astale` statement
  format. An expired token must delegate to ordinary prompt handling where the
  saved statement replaced the vendor dispatcher, including when the current
  `PROMPT_COMMAND` contains only a wrapper name. Finding or removing literal
  code in the current variable must not be a prerequisite for that delegation.
- Distinguish an invocation already dispatched in this prompt from one still
  needing normal dispatch. Reuse the vendor's recursion protection and rearming
  behavior; neither unconditionally force callbacks twice nor skip them merely
  because forwarding happens inside a function.
- Capture fresh status, pipeline information, and previous argument before
  stale-token validation or cleanup. These belong to the command now finishing,
  never to the expired history record. Ensure both direct replay and wrapper
  forwarding deliver the metadata expected from their matching normal control.
- Never complete an expired detached ID. Consume or expire only owned pending
  state; a stale statement must not clear or authenticate an intact newer pending
  token, change a newer live Atuin ID/time, or reset the serial counter. If that
  newer registration's own boundary was lost, later context validation must
  expire its association so old cached code cannot block ordinary dispatch.
- Cleanup may remove exact owned statements from the current prompt, preserving
  scalar/array type, sparse indices, and user edits. Do not inspect, rewrite, or
  evaluate user function bodies to remove their cached copies. Compatibility
  handling must remain usable when those copies appear again after cleanup.
- Keep failures best-effort: unavailable backend/helpers or a failed history end
  must clear the owned association without retrying it. Do not let handling an
  old history registration permanently suppress otherwise available user hooks.

### 4. Integrate, verify, and document

- Preserve existing off/filtered/cleared-history, same-input toggle,
  function/source reload, prompt-loss expiry, stale/new-token, newer live state,
  missing backend/helper, failed-end, sentinel, external ownership, fzf, bindings,
  and `HISTFILE` regressions. Extend shared assertions for any new transient
  metadata and prove cleanup after success, expiry, and repeated replay.
- Update the user docs to explain owned history completion separately from user
  callback dispatch. Document cached old prompt compatibility and the retained
  conservative discard for directly entered multiline blocks. Correct the
  historical claim below that the old tests established all relevant ordering
  and metadata guarantees.
- Run the focused suite from `dev/`:

  ```bash
  uv run pytest -q --tb=short -p no:cacheprovider \
    tests/test_atuin_ownership.py tests/test_atuin_lifecycle.py \
    tests/test_atuin_prompt.py tests/test_history_backend.py \
    tests/test_tool_init_shell.py
  ```

- Run `just smoke`, explicit Bash 3.2 syntax, Ruff lint/format checks on changed
  Python files, `git diff --check`, and local documentation links. Obtain the
  required permissions for socket-dependent tests; do not run the live asset
  checker. Record measured results, separate version-related skips from actual
  coverage, and review the final diff before closing the findings.

### Acceptance checklist

- [x] Each of the three audited regressions fails before the runtime repair and
  passes afterwards, with an ordinary vendor/wrapper control on both Bash versions.
- [x] Cached old and new statement formats recover callbacks and later history
  start/end pairs without manual prompt repair, duplicate callbacks, or late
  completion of an expired ID.
- [x] A single event trace proves unchanged prefix/wrapper/callback/tail order,
  callback-visible prepared state, and original 0/7 status.
- [x] Direct and wrapped saved-prompt replay preserve the matching control's
  status, pipeline metadata, and last argument; modern direct dispatch retains
  the full `(4 7)` vector.
- [x] Sparse arrays, startup/reload, expiry, stale/new ownership, and cleanup
  regressions pass without vendor edits or new runtime dependencies/observers.
- [x] Documentation, focused tests, `just smoke`, and the required static checks
  are complete; actual results replace the baseline figures as repair evidence.

### Implementation and verification record

- The serialized statement format is unchanged. Its live map now selects the
  same compatibility entrypoint as a stale statement; reload redirects an
  already-pending legacy map as well. The entrypoint authenticates the live
  token and completes only the owned history record before a user prefix.
- A statement that replaced an original vendor prologue delegates ordinary
  dispatch at that original position. Cached wrappers can trigger the vendor's
  normalization even when the current prompt contains only the wrapper name.
  An already-present first vendor statement and its recursion guard avoid
  duplicate callbacks; a newer pending token prevents stale delegation.
- Pipeline state is captured as the entrypoint's first operation. For the
  replaced-vendor (`mode=1`) path, a temporary first precmd hook hands it to user
  callbacks after the vendor's own capture.
  The hook removes itself before user callbacks edit their global array; the
  array is never hidden in a local copy. A skipped/interrupted registration
  without the dynamically scoped capture can only remove itself. The entrypoint
  also removes a skipped hook after dispatch, and pending cleanup removes it.
- All entrypoint locals visible to callbacks use private names. A strengthened
  test proved that callbacks can read and update global `status`, `force`, and
  similar user state while changing their callback array. It failed before
  namespacing and passed on both Bash versions afterwards.
- Stale replay preserves an intact newer pending record in the same input.
  When a cached old wrapper replaces that newer prologue, a later invocation
  validates and expires the missed boundary, allowing callbacks and subsequent
  history recording to recover. The regression failed with zero callbacks before
  this expiry path was added; same-input newer-token protection remains tested.
- The multiline prefix control now uses the same configured wrapper and one
  chronological log. Its callback metadata is compared with that layout's
  ordinary dispatcher, rather than forcing default first-dispatch behavior onto
  a wrapper that deliberately runs after a prefix.
- Before runtime edits, separate regression runs failed on all three audited
  behaviors: no callback from a cached wrapper; `7|7|EXPECTED` instead of the
  legacy vendor control's `7|0|EXPECTED`; and callbacks reading `old` before the
  prefix prepared `new`. The order regression preserved status 7 in both traces.
- The isolated runtime prototype passed **22 PTY scenarios** across Bash 3.2
  and 5.3 before promotion to the worktree. The expanded prompt module then
  passed **54 tests with 8 skips**. The focused history/initialization suite
  passed **362 tests with 36 skips in 243.88s**. Final review strengthened the
  global-state case and added the lost-newer-boundary regression; these and the
  existing intact-newer-token case passed **6 tests in 6.80s** after refinement.
- The three original regressions also failed against an isolated copy of the
  pre-repair runtime on modern Bash, supplementing the legacy Bash red runs.
  The controls use the unmodified pinned Atuin fixture in actual PTYs.
- Final `just smoke`: **688 passed, 36 skipped in 302.82s**. Bash syntax,
  ShellCheck, Ruff, and mypy passed; socket-dependent checks ran with the required
  permissions. Explicit Bash 3.2 syntax, Ruff lint/format for changed tests,
  `git diff --check`, and local documentation links passed as well.
- The six additional skips relative to the audited baseline are unsupported
  array prompt cases on legacy Bash. New scalar cases run on both Bash 3.2.57
  and 5.3.20. No vendor source, pinned tool version, runtime dependency, or shell
  startup profile changed; the live asset checker was not run.

## Multiline prompt completion boundary

Historical implementation record. The independent audit found the three
dispatch/order/pipeline regressions planned above. The checked items and measured
results below reflect the previous test coverage, which did not establish those
guarantees for all saved-prompt paths.

Created: 2026-10-21. The earlier multiline-prefix finding was implemented and
verified by the tests below. The current repair plan supersedes its early
whole-dispatcher approach and its claims about saved registrations.

Before this repair, the validator compared the outermost `BASH_LINENO` value
during detach and inside a later precmd callback. A multiline `PROMPT_COMMAND` can change
that value before invoking a working wrapper. The audit reproduced origin
**3**, callback context **6**, and correctly forwarded status **7**, but no
history-end attempt, on Bash 3.2.57 and 5.3.20. The user's input was one line.
This is separate from the documented conservative treatment of directly
entered multiline input.

Required behavior: finish the owned entry exactly once at its first valid
prompt, including when a multiline prompt forwards dispatch indirectly. Keep
expiry of entries whose completion boundary was missed. Preserve the incoming
status, user prompt commands, callbacks, and any newer live Atuin state.

Scope: `shell/rc.d/23-atuin.sh`, `dev/tests/test_atuin_ownership.py`, the new
`dev/tests/test_atuin_prompt.py`, and the history section of
`docs/shell/helpers.md`. Adjust existing lifecycle assertions
only if the temporary registration changes. Reuse the PTY helper, fake CLI, and
unmodified Atuin 18.14.1 fixture. No tool pin, vendor source, runtime dependency,
or shell startup simplification changes are included.

### 1. Establish the failing regression and prompt-order controls

- Extend the wrapper test beyond `PROMPT_COMMAND=audit_prompt_wrapper`.
  Capture the installed prompt after its first real invocation; save scalar
  and array forms without replaying bash-preexec's deferred installer.
- Reproduce a scalar multiline prompt that saves `$?`, runs preceding commands,
  restores the saved status, and invokes the wrapper on a later line. Keep the
  disabling input itself on one line. Assert one end event for its unique ID,
  with status 0 or 7, before sending another input.
- Retain controls for the bare wrapper, trailing prompt commands, a sourced
  prompt wrapper, and Bash's supported array prompt form. Use arrays only on
  Bash versions that execute them; Bash 3.2 must exercise the scalar cases.
- Record user callback order/count and the status received by user prompt code.
  A prefix that accidentally overwrites `$?` would test a different failure.

### 2. Complete at the start of the actual prompt

- Move the history-end attempt to a temporary owned prologue at the beginning
  of `PROMPT_COMMAND`, before any user prefix or wrapper can shift its context.
  Continue validating ordinary reloads at their interactive call site.
- Prototype prologue installation/removal in real PTYs on both Bash versions
  before changing the lifecycle implementation. For a scalar, prepend one
  owned statement. For an array, prefix its first executed element while
  preserving other elements and indices, including sparse arrays. Verify that
  removal during execution neither skips nor repeats user commands.
- Give each pending registration a fresh shell-local token. Generate the token
  from private state; do not interpolate an Atuin ID or user command into prompt
  code. Only the matching prologue may perform completion. A saved registration
  from an older cycle must not complete or delete a newer pending record.
- Capture `$?` before validation/cleanup and preserve it for the remaining
  prompt commands. Consume pending state before invoking the retained upstream
  completion helper, restore any newer live ID/timestamp, and return the
  original status to the prompt chain.
- Keep the first-prologue context comparison strict. Its position supplies the
  normalization; do not compensate with a fixed line offset, widen the accepted
  range, or remove the expiry check from all precmd invocations.

### 3. Keep cleanup safe when prompt dispatch is replaced

- Retain a one-shot precmd cleanup guard for pending records whose owned
  prologue disappeared. That guard discards the association without calling
  `history end`; it must not compare an arbitrary wrapper's line number and
  then authorize completion there.
- Extend the shared cleanup to cover ID, timestamp, context, token, owned
  prologue, and cleanup guard. Removal must be idempotent and limited to our
  exact registration; preserve unrelated prompt commands and user edits.
  Exercise bash-preexec's own prompt rewriting as well as user replacements.
- Validate at inactive reloads and reactivation as before. Same-input toggles
  with an intact prologue still complete once at the first prompt. Restoring an
  old prompt snapshot after later inputs must discard the old ID, whether that
  snapshot contains the owned prologue or predates its installation.
- Missing backend/helpers and a failed end remain best-effort. Clear local
  state and never retry an old ID. Preserve the sentinel handling, external
  Atuin ownership, fzf fallback, and existing binding restoration.
- Do not execute or parse user functions to classify prompt forwarding, replace
  DEBUG/PS0/PS1, or add a permanent observer. Direct multiline input whose origin
  remains uncertain retains its documented conservative behavior.

### Acceptance tests and delivery

- [x] The audited multiline-prefix case fails before runtime edits and passes
  on Bash 3.2 and modern Bash with one end event and the original 0/7 status.
- [x] Bare, prefixed, suffixed, and sourced wrappers work. Supported array forms,
  including sparse indices, execute all user commands in their original order
  exactly once; the prologue preserves the status supplied to them.
- [x] Prompt/prologue replacement before completion, restoration of snapshots
  from before/after scheduling, repeated inactive reloads, later reactivation,
  and stale registration tokens cannot end an old ID or disturb a newer one.
- [x] Retain the history off/filtered/cleared matrix, same-input toggles,
  function/source reloads, new live state, missing helpers/backend, failed end,
  sentinel, external ownership, bindings, and `HISTFILE` regressions. Verify
  complete removal of owned temporary state and registrations.
- [x] Exercise actual startup through `bash --rcfile` as well as loading `rc.sh`
  in an existing PTY. Keep HOME/XDG state and fake command events isolated.
- [x] Update user docs and the historical implementation claim below: the old
  raw call-site marker is not stable across arbitrary prompt prefixes. Explain
  the temporary prologue and the retained conservative fallback behavior.
- [x] Run focused ownership/lifecycle/history/tool-init tests, `just smoke`,
  explicit Bash 3.2 syntax, Ruff lint/format for changed Python files,
  `git diff --check`, and local documentation links. Use required permissions
  for socket tests; do not run `just test-assets-live`.
- [x] Review the final diff and record measured results before marking this
  repair implemented. The latest audit's **260-pass/16-skip** focused result and
  the earlier **584-pass/16-skip** full result are baselines, not proof of repair.

### Implementation details

- The owned first statement invokes the existing bash-preexec dispatcher, which
  captures status, pipeline status, and the previous argument before any user
  prefix. A normal first vendor statement is temporarily replaced rather than
  duplicated. Wrappers remain under bash-preexec's existing recursion guard.
- Each statement contains a fresh numeric token and a replacement/prepend mode.
  A token-indexed private dispatch map authorizes the live statement; argument
  expansion records its authentication before the dispatcher captures state.
  The retained precmd finalizer completes only that authenticated invocation.
  Otherwise it is a cleanup guard, never an authorization based on a wrapper's
  shifted line number.
- Inactive tokens call a fixed stale-registration helper. It removes only its
  exact generated statement, leaves newer pending state intact, and restores
  normal dispatch when the statement replaced the vendor's first command.
  The serial counter survives cleanup, so a new cycle cannot reuse an old token.
- The private serialized names are compact (`__rs_ap` for dispatch and
  `__rs_as` for authentication). Long generated statements made the vendored
  sanitizer excessively slow on Bash 3.2 when processing multiline prefixes.
  This does not modify vendor code or require aliases, eval, or new dependencies.
- Scalar type and sparse array indices are retained. Cleanup removes exact
  owned statements without evaluating user code. The replacement is deliberately
  unquoted inside Bash's parameter substitution: Bash 3.2 otherwise inserts the
  replacement quotes literally and breaks restored prompt dispatch.

### Measured verification

- Before runtime edits, the new multiline-prefix regression failed on Bash 3.2
  because the detached ID received no end event. The repaired wrapper matrix
  passed **60 cases with 12 skips**, covering 0/7 status, direct/function/source
  reloads, bare/prefix/suffix/sourced wrappers, and supported prompt arrays.
- The new prompt lifecycle module passed **24 cases with 2 skips**. It compares
  callback status, pipeline state, last argument, and order against the same
  vendor's normal dispatcher; it also covers real startup, sparse arrays, saved
  prompt restoration, and stale tokens while a newer record is pending.
  New array cases are skipped only on Bash versions without array prompt support.
  Scalar cases run on both Bash 3.2.57 and 5.3.20 with the unmodified Atuin
  18.14.1 fixture.
- Final `just smoke`: **656 passed, 30 skipped in 283.42s**. Bash syntax,
  ShellCheck, Ruff, and mypy passed. Socket-dependent tests ran with the required
  permissions. Explicit Bash 3.2 syntax, Ruff lint/format for the changed Python
  files, `git diff --check`, and local documentation links also passed.
- The final diff retains the documented conservative discard for directly
  entered multiline blocks whose origin is uncertain. No vendor source, pinned
  tool version, runtime dependency, or startup profile changed in this repair.
  The live asset checker was not run.

## Prompt wrappers and pending history expiry

Created: 2026-10-21. Both P2 repairs from the follow-up audit are implemented
and verified. The checklist records the agreed scope, refined by the PTY
experiment below; measured results follow it. Later sections record earlier
repair cycles.

| Finding | Required behavior |
| --- | --- |
| Detach rejects a working prompt wrapper because `PROMPT_COMMAND` does not directly contain `__bp_precmd_invoke_cmd` | Finish the owned entry at the first valid prompt even when a user function invokes the saved prompt dispatcher indirectly. |
| Removing prompt dispatch after scheduling leaves a pending ID that reactivation finishes with a later command's status and duration | Expire a pending association whose original completion boundary was missed; a later command must never finish that ID. |

The audit reproduced both cases in actual PTYs on Bash 3.2.57 and 5.3.20,
using the pinned, unmodified Atuin 18.14.1 source fixture. In the second case,
the original command returned **7**, but a later reactivation finished its ID
with status **3**. Existing focused tests passed **178 tests, with 16 skips**;
the **502-pass/16-skip** full-suite result below predates this follow-up and
does not establish that these two cases work.

Changed files: `shell/rc.d/23-atuin.sh`, `dev/tests/test_atuin_ownership.py`,
the lifecycle count assertion in `dev/tests/test_atuin_lifecycle.py`, and the
history section of `docs/shell/helpers.md`. The PTY helper, fake CLI, pinned
upstream fixture, fzf ownership fix, bindings, upstream guard/helpers, runtime
dependencies, and pinned tool versions are unchanged. Shell startup
simplification remains deferred.

### 1. Establish the regressions and a reliable completion boundary

- Add both failing PTY regressions before changing runtime behavior. Load full
  `rc.sh`, send separate interactive commands, and correlate unique start/end
  IDs. Run every new lifecycle case on legacy and modern Bash.
- For the wrapper case, save the existing scalar/array prompt commands, expose
  them through a user function, then disable Atuin before the next prompt.
  Verify that the wrapper actually dispatches user precmd callbacks and that
  the detached entry ends exactly once with its original exit status.
- For late prompt loss, disable Atuin, remove/empty `PROMPT_COMMAND` after
  scheduling, and finish the original command with status 7. Send a fallback
  command, then restore dispatch and reactivate with status 3. The old ID must
  receive no delayed end attempt, and newly active commands must work normally.
- Before implementing expiry, use a small PTY experiment to select a Bash 3.2
  compatible origin marker for the pending command. It must distinguish a
  later interactive input from more statements in the original compound input,
  including when prompt dispatch and legacy preexec stop running. Evaluate the
  outer interactive call context together with available preexec state; verify
  behavior through sourced files, functions, multiline input, and prompt wrappers.
- Do not assume that a preexec counter alone observes every fallback command:
  Bash 3.2's DEBUG backend stops dispatching without its prompt rearm. Do not
  use `HISTCMD`/`history 1` alone, elapsed-time thresholds, or command text as
  proof of identity. History can be disabled, filtered, or changed. If origin
  cannot be established reliably, discard the pending association rather than
  assign a later command's status to it. Treat this experiment as a prerequisite
  for the runtime change, not an unverified implementation assumption.

### 2. Make pending-state validation and cleanup explicit

- Treat a pending record as the saved ID, timing data, and origin context.
  Keep all of it private to remote-ssh's own integration.
- Add one idempotent cleanup helper that clears the whole pending record and
  removes only our temporary finalizer registration. Reuse it for successful
  completion, expiry, unavailable helpers/backend, and interrupted setup.
- Validate pending origin at the start of a reload/reactivation and immediately
  before completion. Perform reload validation even when Atuin is already
  inactive; the current `ACTIVE=0` early return must not bypass stale cleanup.
- Permit disable/re-enable within the original compound input to retain its
  pending record. At its first valid prompt, finish that ID once with the
  original status. Reattachment must not discard every pending ID blindly.
- If a completion boundary was missed or origin is uncertain, discard the
  record without calling `history end`. Reactivation must not restore that ID
  into `ATUIN_HISTORY_ID`. Preserve any newer live ID and timestamp.
- Consume valid pending state before invoking the upstream helper. Keep the
  existing best-effort behavior for a failed end operation and preserve the
  incoming status before cleanup statements change `$?`.

### 3. Support indirect prompt dispatch without executing it during detection

- Remove the direct-name substring check as the requirement for scheduling.
  With the existing bash-preexec/helper infrastructure and a nonempty prompt
  configuration, allow the one-shot finalizer to be dispatched indirectly.
  The origin validation above decides whether an eventual invocation is timely.
- Retain immediate discard for explicitly absent dispatch, including an unset
  or empty prompt and an array containing only bash-preexec's rearm epilogue.
  A nonempty prompt value alone is not proof that completion will be dispatched.
- Do not evaluate a user prompt, invoke its functions early, or inspect/evaluate
  function bodies to guess whether a wrapper forwards dispatch. Preserve user
  prompt commands and callback order. Do not replace DEBUG, PS0, or PS1 to gain
  a second independent prompt observer, and do not modify vendor source.
- If dispatch is absent, discard at the next observable validation boundary.
  Restoring a working prompt before a later reload must still reject an expired
  record; checking only whether `PROMPT_COMMAND` is currently empty is insufficient.

### Acceptance tests and delivery

- [x] Both audit reproductions fail on the previous runtime and pass after repair
  on Bash 3.2 and modern Bash, using the unmodified upstream fixture and PTYs.
- [x] Direct and wrapped dispatch complete one owned entry with status 0 or a
  nonzero status, preserve user callbacks, and remove the temporary registration.
- [x] Late loss covers unset/empty prompt commands, restoration before or after
  reactivation, repeated inactive reloads, and several intervening fallback
  inputs. No old ID receives status 3 instead of 7, a delayed duration, or a
  repeated end attempt. Assert event ordering rather than wall-clock thresholds.
- [x] Same-line disable/re-enable and repeated toggles complete the original
  entry once, including multiline sourced/function-based reloads. Direct
  multiline input with an uncertain origin is discarded, following the
  conservative policy selected in the experiment below. Include history
  disabled/filtered/cleared so expiry does not depend solely on a history
  counter, and ensure later normal Atuin recording recovers.
- [x] Missing executable/helpers, failed completion, newer live history state,
  the upstream sentinel, external ownership, typed binding restoration, and
  custom/empty/`/dev/null` `HISTFILE` behavior retain their existing coverage.
- [x] Update the history docs to explain indirect dispatch and conservative
  expiry. When all completion observers are removed, immediate cleanup cannot
  run; guarantee that the next reload or resumed callback discards an expired
  record before any old history-end attempt. Backend entries may remain open.
- [x] Run focused ownership/lifecycle/history/tool-init tests, then `just smoke`,
  explicit Ruff lint/format checks for any changed Python files, Bash 3.2 syntax
  checks, `git diff --check`, and local documentation links. Use the required
  permissions for socket-dependent tests; do not run `just test-assets-live`.
- [x] Review the final diff and record actual test results here. Mark this
  section implemented only after both reproductions and all required checks pass.

### Implementation decision from the PTY experiment

The experiment found the outermost `BASH_LINENO` call site stable through
functions, sourced files, repeated same-line toggles, and the single-name
prompt wrappers tested at that time. The later audit above invalidates the
broader claim for multiline prompt prefixes. It advances for later interactive
inputs even when history is disabled
or filtered and Bash 3.2's preexec no longer runs. Capture that call site as
`REMOTE_SSH_ATUIN_PENDING_CONTEXT`; missing or different context expires the
record before reload/reactivation or upstream completion. The shared cleanup
removes ID, timestamp, context, and only the temporary finalizer registration.

The experiment also showed a limit: statements in a directly entered multiline
block can have different outer call sites from its closing prompt. Those cases
cannot be proved to belong to the original input using this marker. They are
discarded rather than assigned a possibly unrelated status. This refines the
original blanket multiline acceptance criterion according to the plan's
conservative uncertainty rule; multiline functions and sourced scripts called
from one line still complete normally. No extra history assumptions, persistent
observers, vendor modifications, or runtime dependencies are introduced.

### Implementation and verification on 2026-10-21

- Before runtime edits, the wrapper regression timed out waiting for its end
  event, and late restoration ended the old ID with status 3 instead of 7.
- Pending validation runs before initialization snapshots, during detach, and
  before the one-shot finalizer consumes its record. It therefore also covers
  already inactive reloads and callbacks resumed without a reload.
- Prompt detection accepts indirect forwarding without executing user functions
  or inspecting their bodies. Explicitly empty/unset dispatch and a lone
  bash-preexec rearm epilogue still discard the association immediately.
- New PTY regressions: **82 passed** in 84.03 seconds on Bash 3.2.57 and
  5.3.20. Coverage includes direct/function/source wrappers, status 0/7,
  unset/empty prompt commands, restoration before/after reactivation, callback
  resumption without reloading, repeated inactive reloads, normal/disabled/
  filtered/cleared history, recovery of new recording, nested multiline toggles,
  and conservative expiry of direct multiline input.
- Tests save the installed prompt only after bash-preexec's first real prompt,
  avoiding accidental replay of its deferred installer. The old directly
  entered multiline lifecycle loop now requires expired pending state and
  exactly the active hooks after reattachment; its six variants passed.
- `just smoke`: **584 passed, 16 skipped** in 210.95 seconds. Bash syntax,
  ShellCheck, Ruff, and mypy passed. The full run used permission for the tmux
  test's local Unix socket. The legacy binding-dump skips are unchanged; none
  of the 82 new cases were skipped.
- After the full run, the wrapper assertion was strengthened to require exactly
  one user callback at the target prompt. All **12 wrapper cases passed** again
  in 7.75 seconds; runtime code did not change after the full run.
- Explicit Bash 3.2 syntax, Ruff lint/format checks for both Python files,
  `git diff --check`, local documentation links, and the final diff review passed.
  No live asset check was run.

## External Atuin ownership and pending history

Created: 2026-10-21. Both P2 repairs are implemented and verified. The checklist
records the agreed scope; measured verification results follow it.

| Finding | Required behavior |
| --- | --- |
| fzf fallback replaces Ctrl-R belonging to independently initialized Atuin | Preserve the external integration's bindings and registrations through startup and reload. |
| Detaching Atuin leaves its current history entry open until reactivation | Finish an owned entry at the first prompt after graceful disable; never carry a detached entry into reactivation. |

Changed files: `shell/rc.d/20-fzf.sh`, `shell/rc.d/23-atuin.sh`,
`dev/tests/test_atuin_lifecycle.py`, new `dev/tests/test_atuin_ownership.py` and
`dev/tests/pty_shell.py`, and the history section of `docs/shell/helpers.md`.
Existing `test_history_backend.py` and `test_tool_init_shell.py` coverage is
retained. The pinned 18.14.1 source fixture, runtime dependencies, and tool pins
remain unchanged. Shell startup simplification stays in the benchmark TODO.

### 1. Add regressions using the existing upstream fixture

- Reproduce external initialization with default Ctrl-R enabled. The current
  external-initialization test sets `__atuin_bind_ctrl_r=false`, so it does not
  establish protection of the default search binding.
- Check full `rc.sh` startup and repeated `rcrc` in emacs and vi editing modes.
  Capture Ctrl-R in emacs/vi-insert, the external vi-command `/` binding, and
  existing hooks. Exercise the early fallback call in `20-fzf.sh` as well as
  the call after Atuin initialization in `23-atuin.sh`.
- Extend the fake CLI with an opt-in event log and unique history IDs. Associate
  each start and end with its ID, and support an injected history-end failure.
  Retain existing fixture defaults for focused tests that rely on fixed IDs.
- Exercise history lifecycle with a real PTY and full `rc.sh`, sending separate
  interactive commands and waiting for actual prompt boundaries. Bash 3.2's
  DEBUG-based preexec path requires a terminal; piped interactive input and
  manual callback invocation are insufficient evidence for this repair.
- Reuse the bounded PTY cleanup and execution markers. Keep HOME, XDG paths,
  command responses, and all event files isolated and offline.

### 2. Protect the externally owned integration

- Gate all fzf history-binding mutations inside `remote_fzf_history_bind`, so
  every caller applies the same ownership rule. The rule must work before
  `23-atuin.sh` is first loaded; a check only at that file's final call is too late.
- Distinguish successful remote-ssh initialization, external initialization, and
  a failed remote-ssh initialization that set the upstream guard. Record the
  guard's provenance around our own initializer. Do not infer external ownership
  from `__atuin_initialized=true` alone, because that would suppress the intended
  fzf fallback after a partial initialization failure.
- For external ownership, preserve bindings, callback arrays, helper functions,
  the guard, and pending history state. Do not initialize or adopt that
  integration. Classification must not execute Atuin or user wrappers.
- Apply protection across ordinary reloads, `REMOTE_SSH_ENABLE_ATUIN=0`, and an
  unavailable external executable. A stale fzf-bound flag must not cause the
  external Ctrl-R binding to be reset or replaced.
- Retain existing fallback behavior when remote-ssh's own integration is absent,
  disabled, or failed. Keep the existing policy that our Atuin initializer uses
  `--disable-ctrl-r`; this repair does not redesign general Ctrl-R customization.

### 3. Finish the owned history entry at the detach boundary

- Capture an owned pending ID and its timing state before removing registrations.
  Clear the active ID/timing association so reattachment cannot accidentally
  finish that detached entry. Do not touch externally owned history state.
- For graceful disable with a usable executable and completion helper, register
  one temporary precmd finalizer. It runs at the first prompt after the disabling
  command, uses that command's actual exit status, and finishes the captured
  entry through the retained upstream completion helper. This excludes later
  interactive waiting and fallback commands from the recorded duration.
- Capture the incoming status before cleanup statements change `$?`. Restore
  any newer live history state around completion of the saved entry, preserve
  user callbacks, and remove the temporary registration after one invocation.
  Do not replay preexec to synthesize another entry. Treat the upstream
  `__bash_preexec_failure__` sentinel as a sentinel, not a real history ID.
- Keep scheduling and cleanup idempotent: repeated disable/reload must not
  duplicate the finalizer or history-end attempt. If reactivation happens before
  the next prompt in the same compound command, the saved entry is still finished
  once; the regular Atuin callback must not finish it a second time.
- If the executable, completion helper, or prompt infrastructure is unavailable,
  clear the local pending association and continue with Bash/fzf fallback. Do not
  retry that old ID after reinstall or reactivation. A database entry cannot be
  guaranteed closed when its backend is unavailable; document this limitation.
- Make completion best-effort. A failing history-end operation must not block
  fallback, resurrect pending state, or produce repeated attempts on later
  prompts. Preserve the upstream initialization guard and retained helpers.

### Acceptance tests and delivery

- [x] Reproduce both findings before changing runtime behavior.
- [x] Preserve external default Ctrl-R and vi search bindings through full
  startup/reload, both editing modes, the disable toggle, missing executable,
  and a prior fzf fallback. Verify an actual Ctrl-R keypress still reaches the
  external Atuin search integration in a PTY on Bash 3.2 and modern Bash.
- [x] Retain fzf fallback after both CLI initialization failure and a partial
  eval failure that set the upstream guard. Verify that our binding/cleanup calls
  leave external callbacks, bindings, guard, and pending ID unchanged; natural
  completion by the external integration's own prompt hook must still work.
- [x] With unique IDs, prove that graceful disable produces one end event for
  the disabling command before any subsequent fallback command is sent. Assert
  its exit status, cleared pending state, and removal of the temporary hook.
  Use event ordering rather than a fragile elapsed-time threshold.
- [x] Cover repeated inactive reloads, disable/re-enable before a prompt,
  later reactivation, and executable removal/reinstallation. An old ID must
  never be ended twice or reused for a new command; normal active reloads must
  not prematurely finish the current command's entry.
- [x] Cover missing helpers/executable, history-end failure, and the upstream
  sentinel. Verify fallback settings and unrelated hooks survive each path.
- [x] Retain typed binding restoration, conservative legacy takeover, aliases,
  functions, selective stale-hash invalidation, and custom/empty/`/dev/null`
  history settings. Run through Bash 3.2 and modern Bash.
- [x] Run focused lifecycle/history/tool-init tests, `just smoke`, explicit Ruff
  lint/format checks for changed Python files, `git diff --check`, and local
  documentation links. Run socket-dependent tests with the required permissions;
  do not hide a tmux sandbox failure by weakening or skipping its test.
- [x] Update the history docs, review the final diff, and replace this planned
  status with measured implementation results.

The audit preceding that implementation reproduced both findings on Bash 3.2
and 5.3 while the existing focused suite passed **130 tests, with 16 skips**. The earlier
**454-pass/16-skip** full-suite result below is a historical baseline, not proof
of these repairs. Do not run `just test-assets-live` for this work.

### Implementation and verification on 2026-10-21

- Before runtime edits, the new default external-binding test failed on startup,
  and the first-prompt test timed out waiting for the missing history-end event.
  Both use the unmodified upstream Bash source and actual PTYs.
- `remote_fzf_history_bind` checks ownership before every binding mutation,
  including early startup calls. A guard set by a failed remote-ssh initializer
  has a separate provenance marker and continues to allow fzf fallback.
- Detach saves the owned pending ID/timestamp and clears their live association.
  When completion is possible, one temporary precmd callback consumes that state
  at the first prompt, forwards the command's original status to the upstream
  completion helper, restores any newer live state, and removes itself.
- Missing backend/helpers or prompt dispatch discard the local association.
  Removal after scheduling is checked again before completion. Failure never
  retries an old ID on later reactivation. The history docs explain that backend
  unavailability may leave a database entry unfinished.
- The new developer-only PTY helper preserves command exit status while using
  execution markers, and closes the terminal before bounded child cleanup.
  Optional fake-CLI events record unique start/end IDs and completion attempts.
- New ownership/history tests: **48 passed** in 33.99 seconds on Bash 3.2 and
  5.3. They include real external Ctrl-R keypresses in both editing modes,
  previous fzf state, the disable toggle, missing executable, CLI/partial init
  failures, zero/nonzero completion status, repeated/compound toggles, newer
  live history, normal active reloads, missing/removed helpers and executables,
  missing prompt dispatch, history-end failure, and the upstream sentinel.
- Earlier lifecycle/history/tool-init tests: **130 passed, 16 skipped** in
  38.89 seconds. Legacy binding preservation retains its PTY coverage.
- `just smoke`: **502 passed, 16 skipped** in 126.59 seconds. Bash syntax,
  ShellCheck, Ruff, and mypy passed. The full run used permission to create the
  tmux test's local Unix socket. The 16 skips remain modern binding-dump cases
  on legacy Bash; all 48 new PTY cases ran on both Bash versions.
- Explicit Ruff lint/format checks for the Python tests/helper,
  `git diff --check`, local documentation links, and final diff review passed.
  No runtime dependencies or tool pins changed; the live asset checker was
  not run.

## Atuin lifecycle and binding restoration

Created: 2026-10-21. Both P2 repairs are implemented and verified. The checklist
below records the agreed scope; verification results follow it.

| Finding | Required behavior |
| --- | --- |
| Atuin cannot reactivate after disable/reload because its upstream initialization guard remains set | Enable, disable, and re-enable in the same shell restore exactly one set of owned registrations. |
| Cleanup loses a user's previous `bind -x` binding | Restore the original binding with its type and command, or preserve an unreadable binding by avoiding takeover. |

Scope: `shell/rc.d/23-atuin.sh`, `dev/tests/test_history_backend.py`,
`dev/tests/test_atuin_lifecycle.py`, a developer-only fixture under
`dev/tests/fixtures/atuin/`, and the history section of `docs/shell/helpers.md`.
Runtime dependencies and the pinned Atuin version remain unchanged. The earlier
alias/function and stale-hash fixes are retained.

### 1. Establish an upstream integration fixture

- Check in the unmodified Bash integration source from Atuin 18.14.1 as a local
  test fixture. Record its source URL, tag, SHA-256, and upstream license. It
  must stay below `dev/`; remote sessions must not source this copy.
- Have a fake Atuin CLI return that source with the initialization flags emitted
  by the real CLI. Supply deterministic local responses for UUID/history calls;
  exercise the actual upstream guard, hook registration, and Readline macros.
- First reproduce both failures against this fixture. Keep the small existing
  fakes for focused failure injection, but do not use them as the sole evidence
  for lifecycle or binding restoration.
- Use forwarding wrappers for upstream-source tests with aliases/functions:
  upstream code itself calls `atuin`. Existing sentinel wrappers remain useful
  for proving that our availability checks do not execute wrappers.

### 2. Preserve binding types and handle older Bash conservatively

- Represent a tracked binding as its keymap, key, type, and serialized value.
  Cover Readline functions, macros, shell commands, known unbound keys, and
  unknown states. An unreadable binding must never be recorded as unbound.
- Detect `bind -X` support once. Where available, capture shell-command bindings
  alongside `bind -p` and `bind -s`. Restore shell bindings with `bind -x` using
  their serialized records, without evaluating those records as shell code.
- Compare both type and value with the installed Atuin binding before cleanup.
  Preserve keys changed or explicitly unbound by the user while Atuin was active.
  Keep command payloads containing quotes, pipes, backslashes, or newlines intact.
- Bash 3.2 cannot enumerate `bind -x` commands. If any tracked arrow/`k` binding
  cannot be captured, pass `--disable-up-arrow` and leave the whole group under
  user control. Retain the existing `--disable-ctrl-r` policy. History hooks may
  still use Atuin; do not require a newer Bash or a new runtime tool.
- Only restore keys actually taken over by this integration. On older Bash,
  retain the same conservative takeover policy when reactivating the session.
  Document the capability-dependent behavior in the history helper docs.

### 3. Separate initialization from active registrations

- Track whether this integration successfully initialized Atuin in this shell
  and whether its registrations are currently active or detached. Preserve
  upstream initialization state and implementation helpers across disable.
- Do not blindly unset `__atuin_initialized` or rerun the complete upstream
  initializer on every re-enable. Reattach the captured owned hook names and
  managed bindings instead; validate required functions before declaring the
  integration active. A failed reattachment must retain working Bash history.
- Capture additions to `preexec_functions`, `precmd_functions`, and `BLE_ONLOAD`
  relative to their previous contents. Detach/reattach only owned registrations,
  without duplicates or removal of user callbacks. Do not add a ble.sh dependency.
- Before each takeover, save the user's current tracked bindings as the next
  restoration target. Reuse the retained Atuin binding definitions, applying the
  binding-capability policy above. Preserve ordinary active reload idempotence.
- Keep `HISTFILE` disabled only after successful activation. Disable, removal,
  failed initialization, and failed reattachment must preserve saved fallback
  settings and enable the available fzf fallback. Never reset an upstream guard
  or tear down registrations initialized independently by the user.

### Acceptance tests and delivery

- [x] Reproduce toggle/reactivation and lost shell bindings with the pinned
  upstream source before changing runtime behavior.
- [x] Implement typed binding snapshots and conservative legacy takeover.
- [x] Implement owned registration detach/reattach without replaying upstream
  initialization; preserve aliases, functions, and unrelated command hashes.
- [x] Test multiple full `rcrc` enable/disable cycles and removal/reinstallation
  on Bash 3.2 and modern Bash. Assert active state, functioning callbacks, stable
  hook/onload counts, and a single upstream initialization per shell.
- [x] Verify original bindings, user edits while active or disabled, and quoted
  shell-command round trips. On Bash without `bind -X`, use an isolated PTY to
  press a test key such as vi-command `k` and verify the original command still
  runs; an empty dump alone is insufficient evidence of preservation.
- [x] Cover failed reattachment and externally initialized Atuin without deleting
  user state. Retain fallback persistence, custom/empty/`/dev/null` settings,
  alias/function lookup, and stale-hash regressions.
- [x] Run focused history/tool-init tests, `just smoke`, explicit Ruff checks
  for changed Python tests, `git diff --check`, and local documentation links.
- [x] Review the final diff and replace this planned status with actual results.

Keep fixtures and tests offline with isolated HOME, XDG, CLI responses, and PTYs.
Do not run the live asset checker. Planning probes confirmed the difference in
`bind -X` support and a serialized shell-binding round trip on modern Bash.
The earlier 420-test result is a historical baseline.

### Implementation and verification on 2026-10-21

- The preceding audit reproduced the upstream guard blocking reactivation on
  Bash 3.2 and 5.3. Before this runtime repair, the new upstream-source tests also
  failed on shell-binding restoration and leaked `BLE_ONLOAD` registrations.
- The fixture retains the unmodified Atuin 18.14.1 integration and MIT notice.
  Tests verify its SHA-256 and its correspondence to the pinned tool version.
- Initialization is separate from activation. Only captured additions to
  `preexec_functions`, `precmd_functions`, and `BLE_ONLOAD` are detached or
  reattached. Required helper functions are validated before reattachment;
  the upstream guard and implementation helpers are retained.
- Typed snapshots distinguish shell commands, Readline functions, macros,
  unbound keys, and unreadable states. Shell commands are restored with
  `bind -x`, without evaluating serialized records. User changes are preserved,
  and each reactivation captures the current fallback bindings.
- Tests cover three full `rcrc` toggle cycles, executable removal/reinstallation,
  a single initialization, working history callbacks, preserved user callbacks,
  and stable hook counts. Failure cases include missing callbacks/helpers,
  rollback after a partial binding reattachment, partial initialization, and
  independently initialized Atuin.
- PTY tests press vi-command `k` on Bash 3.2.57 and Bash 5.3.20. They cover both
  an initially unreadable shell command and a shell binding introduced while
  Atuin is detached after an earlier readable takeover. Synchronization uses
  execution markers rather than prompt redraws; cleanup closes the terminal
  before reaping the child and has a bounded wait. All four PTY cases also
  passed outside the sandbox after that cleanup correction.
- Focused history/tool-initialization tests: **130 passed, 16 skipped** in
  39.90 seconds. The skips are modern `bind -X` cases on Bash 3.2; its binding
  preservation is verified separately through actual PTY keypresses.
- `just smoke`: **454 passed, 16 skipped** in 95.92 seconds; Bash syntax,
  ShellCheck, Ruff, and mypy passed. The full run used execution outside the
  sandbox because the tmux integration test needs a local Unix socket.
- Explicit Ruff lint/format checks for both Python test files,
  `git diff --check`, final diff review, and local documentation links passed.

The tests use isolated HOME, XDG paths, fake CLI responses, and PTYs. No runtime
dependencies were added, and `just test-assets-live` was not run.

## Atuin lookup regression: aliases or functions

Priority: P2. Status: repaired and verified on 2026-10-21.

The subsequent implementation audit found that `remote_atuin_available` treated
every successful `command -v atuin` result as a file path. An alias produces an
alias description and a function produces its name, so the integration switched
to Bash history even when `command atuin init bash` could run the external tool.
The regression was reproduced under Bash 3.2 and Bash 5.3.

Scope: `shell/rc.d/23-atuin.sh` and regression tests in
`dev/tests/test_history_backend.py`. Keep this a focused correction to the
availability check; reuse the existing initialization and cleanup flows.

Implementation order:

1. Add failing interactive-shell regressions for an alias and a function named
   `atuin`, with a working external executable still present in `PATH`. Cover
   both a wrapper defined before startup and one introduced after activation,
   followed by reload.
2. Replace both `command -v atuin` path lookups in `remote_atuin_available` with
   `builtin type -P atuin`. This selects the external executable consistently
   with initialization through `command atuin`, without changing or invoking
   the user's alias/function.
3. Retain the regular-file/executable checks and invalidate only Atuin's stale
   hash entry in the parent shell before retrying lookup. `type -P` still honors
   a cached path: changing the lookup alone would not preserve the removal fix.
   Keep successful reloads free of new `atuin init` or version probes.
4. Verify that an alias/function without an external executable does not count
   as a working backend. Preserve Bash history restoration, available fzf
   fallback, initialization-failure handling, and the disable toggle.

Regression coverage and acceptance criteria:

- A working external Atuin remains active with either kind of wrapper; Bash
  file writes remain disabled while that integration owns history. Repeated
  reloads retain one set of owned hooks and one initialization call. Assert the
  wrapper remains defined and is never invoked by integration setup or checks.
- With only a wrapper and no external executable, reload restores the saved
  `HISTFILE` and removes only owned hooks/bindings. Existing custom, empty, and
  `/dev/null` history settings must retain their behavior.
- Keep the current removal, broken-link, and permission-loss tests. Add wrapper
  coverage for stale-cache rejection and for selecting an executable later in
  `PATH`. Verify a real external call reaches the replacement: merely finding
  its path in a subshell does not prove the parent hash was repaired.
- Preserve unrelated command hash entries and user hooks/bindings. Include a
  full isolated `rcrc` scenario with a wrapper, alongside the current
  removal/reactivation test. Disable network hooks and auto-import in fixtures.
- Run the cases through `runtime_bash` for Bash 3.2 and modern Bash, including
  child interpreter lookup. Use temporary HOME/XDG/tool paths and local fakes.

Delivery checklist:

- [x] Reproduce alias/function failures in regression tests.
- [x] Correct external executable lookup without losing stale-hash handling.
- [x] Run focused history and tool-initialization tests, then `just smoke`.
- [x] Run explicit Ruff lint/format checks for changed Python tests and
  `git diff --check`; review the resulting diff and record actual results here.

Validation on 2026-10-21:

- Before the fix, the new startup/reload cases reproduced eight failures for
  working external executables masked by aliases/functions across Bash 3.2.57
  and Bash 5.3.20. The corresponding eight cases with no executable already
  used the expected Bash fallback.
- Both availability lookups now use `builtin type -P atuin`; file validation
  and selective parent-shell hash invalidation remain intact.
- Focused history and tool-initialization tests: 96 passed in 13.05 seconds.
  Coverage includes unchanged/uninvoked wrappers, preserved user hooks/bindings,
  saved history settings, full `rcrc` removal/reactivation, and an actual call
  to the alternative executable after removal of the cached one.
- Stale-cache fixtures populate the external command hash before defining a
  function, because Bash's `hash` command skips function names. Assertions
  verify that the intended stale entry exists before reloading the integration.
- `just smoke`: 420 passing tests in 67.83 seconds, Bash syntax, ShellCheck,
  Ruff, and mypy. The previous 380-test result below is the historical baseline.
- Explicit Ruff lint/format checks for `test_history_backend.py`,
  `git diff --check`, and local documentation links passed.

Tests stayed offline with isolated HOME, XDG, and executable paths. No new
runtime dependencies were added; `just test-assets-live` was not run.

## Implementation-audit repairs

The follow-up audit identified three P2 issues in the initial implementation.
All three were repaired and verified on 2026-10-21. This section records their
implementation scope and regression criteria; validation results follow below.

| Order | Finding | Main files | Acceptance criterion |
| --- | --- | --- | --- |
| 1 | P2: default SSH connections unexpectedly ignore system configuration | `scripts/ssh_find.py`, `shell/rc.d/30-ssh-pick.sh` | Default resolution and connection omit `-F`; an explicit config uses the same `-F` path in both operations. |
| 2 | P2: a cached path to removed Atuin keeps Bash history disabled | `shell/rc.d/23-atuin.sh` | Reload after removal restores Bash persistence, removes owned hooks, and enables the available history fallback. |
| 3 | P2: a bundle directory can be published as the executable | `tools/lib/install-tool/install.sh` | Invalid candidates fail before publication and leave the previous executable and aliases usable. |

### 1. Preserve default OpenSSH configuration loading

`ssh -F` suppresses the system-wide SSH configuration even when its argument
is the ordinary user config path. See the [OpenSSH manual](https://man.openbsd.org/ssh#F).
The audited producer attached a config path to every OpenSSH record, so the
consumer changed ordinary `ssh alias` behavior.

Implementation:

- Resolve the config selection once as a path plus whether it was explicitly
  selected. Preserve precedence: nonempty `SSH_FIND_SSH_CONFIG`, then nonempty
  `SSH_CONFIG`, then the automatic user config path.
- Use that same selection for offline resolution and record creation. Automatic
  selection calls `ssh -G alias` and produces no config override for connection;
  explicit selection calls `ssh -G -F path alias` and carries that path to
  `ssh-pick`. Do not infer selection mode by comparing paths: explicitly setting
  the default path still requests `-F` semantics.
- Keep the first seven record fields unchanged. Use the optional eighth field
  only for an explicit config override. Existing seven-field records continue
  to connect without `-F`; direct bssh records retain their current behavior.
- Update [helper documentation](../../docs/shell/helpers.md) to explain default
  versus explicit selection and the meaning of the optional field.

Regression tests in `test_ssh_helpers.py` and `test_ssh_pick_records.py`:

- Exercise the backend through `ssh-find` and `ssh-pick`, asserting argv for
  both resolution and connection. The automatic case must omit `-F` in both;
  each explicit selector must retain it, including paths with spaces.
- Cover selector precedence, empty selector values, and an explicit override
  whose path equals the automatic path.
- Use a local fake SSH executable to model system defaults that disappear with
  `-F`, and assert matching resolution/connection behavior. Keep the existing
  real, offline `ssh -G -F` check for custom-config resolution.
- Keep tests isolated: changing `HOME` alone does not redirect OpenSSH's lookup
  of the account's home directory. Default-mode argv tests must not depend on
  or modify the developer's SSH files or `/etc/ssh/ssh_config`.
- Preserve empty-column, seven-field, cancellation, backend-error, and remote
  argument forwarding tests.

### 2. Restore history after Atuin disappears

The audited availability guard trusted `command -v`. Bash can retain a hashed
path after the executable is removed. With Atuin already marked active, reload
then skipped initialization and disabled Bash file history again.

Implementation:

- Check that the resolved external executable still exists as an executable
  file before trusting `REMOTE_SSH_ATUIN_ACTIVE`.
- If lookup returns an invalid cached path, invalidate only Atuin's command
  hash entry and retry lookup. An executable available later in `PATH` should
  remain usable. Do not flush unrelated command hashes or change `PATH`.
- When no usable Atuin remains, reuse the existing cleanup flow: remove only
  hooks and bindings owned by this integration, clear active state, restore
  the saved `HISTFILE`, and invoke the fzf fallback when available.
- Keep successful reload idempotent. Availability checks should use shell
  builtins; do not run `atuin init` or a version probe on every reload.

Regression tests in `test_history_backend.py`:

- Activate a fake Atuin, populate its command hash in the parent interactive
  Bash, remove the executable, and reload the integration without changing
  `PATH` or clearing the hash in the fixture. Also cover a broken symlink and
  loss of executable permission.
- Assert inactive state, restored history path, removal of owned hooks and
  bindings, preservation of user hooks/bindings, and fzf fallback when present.
- Confirm ordinary fallback persistence by reading a recorded command in a
  second isolated shell. Preserve custom, intentionally empty, and `/dev/null`
  history settings.
- Cover repeated reload, reinstallation/reactivation, and an alternative
  executable later in `PATH`. Hook counts must not accumulate and unchanged
  working integration must not be initialized again.
- Include one isolated full `rcrc` reload scenario so rc load order cannot hide
  the failure. Disable network-capable hooks and auto-import in the fixture.

### 3. Validate the bundle executable before publication

The audited bundle branch bypassed the single-binary `find -type f` lookup. Its
`-x` check also succeeded for searchable directories, allowing a package containing
a directory at `bin/nvim` to replace a working installation.

Implementation:

- In `install.sh`, require the selected source candidate to be a regular,
  non-symlink executable file. Report the actual candidate path on failure.
- Validate the staged candidate as well, before writing ownership metadata,
  publishing the release directory, or switching binary/alias links. Keep this
  candidate check local; the release ownership validator requires a published
  release name and is not a staging validator.
- On validation failure, return nonzero and clean up any staging directory.
  Preserve the old release contents, binary link, and all alias links. Retain
  the existing archive path/link checks and pinned package layout.

Regression tests in `test_install_bundle.py`, using the public installer with
local archive fixtures and fake downloads:

- Reject a directory at `bin/nvim`, a missing candidate, and a regular file
  without executable permission. Retain archive symlink/hardlink rejection.
- For each failure, assert nonzero status, unchanged old link targets and
  executable output, no new published release, and no leftover staging paths.
- Add alias coverage with a temporary test definition so aliases also keep
  pointing at the previous working executable after failure.
- Retain the successful nested executable/runtime layout test and coverage of
  the single-binary install path. Production tool definitions, pinned versions,
  and checksums do not need changes for this repair.

### Delivery and verification

- [x] Repair default versus explicit SSH selection with tests and helper docs.
- [x] Repair Atuin removal/reload handling with state-transition tests.
- [x] Repair bundle candidate validation with public installer regressions.
- [x] Run targeted tests for each repair under the existing `runtime_bash`
  fixture, selecting Bash 3.2 and modern Bash explicitly, including child
  interpreter lookup.
- [x] Run `just smoke`, explicit Ruff checks for changed Python tests (the
  smoke lint step excludes tests), `git diff --check`, and local doc-link checks.
- [x] Review the final diff against these three acceptance criteria and update
  this section with actual results and completion status.

Validation on 2026-10-21:

- `just smoke`: 380 passing tests in 66.54 seconds, Bash syntax, ShellCheck,
  Ruff, and mypy. The earlier baseline was 330 tests.
- New regressions reproduced default SSH `-F` injection, stale Atuin command
  hashes, and directory-as-executable publication before their corresponding
  fixes. The repaired cases pass under Bash 3.2.57 and Bash 5.3.20.
- SSH selection tests verify resolution and connection argv, selector precedence,
  explicit default-path overrides, and optional record fields. Real OpenSSH is
  used only for the isolated custom-config `-G -F` check.
- History tests cover removal, broken links, permission loss, fallback
  persistence, preserved user settings/hooks/bindings, an alternative executable,
  and reactivation through full `rcrc` reloads without duplicate initialization.
- Bundle regressions preserve the old executable and aliases, reject invalid
  source candidates and a candidate changed during staging, and verify staging
  and download cleanup through the public installer.
- Explicit Ruff lint and format checks for the affected Python files,
  `git diff --check`, and local documentation links passed.

Regression tests stayed offline with temporary HOME, XDG, install, and SSH
fixtures. `just test-assets-live` was not run.
Shell startup optimization remains deferred in [the benchmark TODO](../todo-bench.md).

## Initial implementation and validation (2026-10-16)

The first implementation pass addressed the nine findings below; the three
gaps found subsequently were closed as recorded above. The existing
`reset --hard` policy is retained; changing it remains a separate CLI decision.

- `just smoke`: 330 passing tests, Bash syntax, ShellCheck, Ruff, and mypy.
- Additional Ruff checks include the Python regression tests; `git diff --check`
  and local documentation links also pass.
- Installer, empty-state public CLI, history, and SSH regressions explicitly
  select system Bash 3.2 and modern Bash 5.3, including child interpreter lookup.
- The pinned Neovim 0.11.5 macOS ARM64 package was installed into temporary
  paths and passed headless startup, bundled vimrc, runtime lookup, and help
  access. Unsafe synthetic archive cases fail before extraction.
- An isolated tmux 3.8 server passed shell launch from a checkout with spaces
  and an apostrophe, configuration reload, canceled restart, and confirmed
  restart. User sessions were not used for these checks.
- Old unmarked releases remain protected. New ownership records are required
  for recursive removal, and active nested executables or custom aliases
  protect the whole release.

`just test-assets-live` was not run. General archive hardening outside bundle
mode, missing pinned hashes, and shell simplification remain follow-up work.

## Findings and delivery order

The rows describe the initial implementation scope and its regression criteria.
The follow-up plan above refines these criteria, particularly default versus
explicit SSH configuration selection. Keep each test with its corresponding
fix when reviewing or committing the work.

| Order | Finding | Scope | Completion criterion |
| --- | --- | --- | --- |
| 1 | P1: failed SHA-256 verification still permits installation | Download, checksum, extraction, temporary files | A failed step returns nonzero and leaves the working installation intact. |
| 2 | P1: empty arrays fail under macOS Bash 3.2 with nounset | Installer and affected public commands | The same supported cases pass under Bash 3.2 and modern Bash. |
| 3 | P1: failed fetch still permits reset and reports success | Update command and bootstrap error propagation | Failed fetch prevents reset, installation, and success-cache writes. |
| 4 | P1: tool-name prefixes are treated as proof of ownership | Installer metadata, prune, uninstall | Unmarked or invalidly marked directories are never recursively deleted. |
| 5 | P1: Neovim loses its runtime during installation | Explicit bundle layout in the pinned definition | Installation preserves the package layout and active bundles survive prune. |
| 6 | P2: optional Atuin leaves sessions without durable history | History backend selection and fzf fallback | History remains usable when Atuin is absent, disabled, or fails to initialize. |
| 7 | P2: empty SSH fields break record parsing | SSH record producer and consumer | Missing user or port does not shift columns or prevent a valid connection. |
| 8 | P2: selected custom SSH config is lost when connecting | SSH record transport and ssh-pick | The selected alias is connected using the same config file used to resolve it. |
| 9 | Unsafe restart shortcut and fixed checkout paths in tmux | Bundled tmux config and shell integration | Restart requires confirmation and shell launch/reload use the actual checkout. |

## Installer failures and Bash compatibility

Relevant code: `tools/lib/install-tool/{download,main,install,defs}.sh` and
`tools/lib/common/extract.sh`.

- Check the result of every required step explicitly. Do not depend on
  `set -e` inside functions or subshells called through `if`, `!`, or `||`.
- Stop on failed curl, failed checksum calculation, mismatched checksum, missing
  checksum tooling for a pinned hash, or failed extraction. Keep definitions
  without a pinned checksum supported by the existing contract.
- Use a task-specific temporary-directory variable and clean it on failure;
  preserve the caller's `TMPDIR` setting.
- Exercise the real installer entrypoint with local fake downloads, both raw
  executables and archives. Assert exit status, unchanged symlinks and previous
  binary contents, no new active release, and temporary-file cleanup.
- Cover empty `CHECKSUMS`, empty `BINARY_ALIASES`, zero tool arguments, and
  rollback with no prior links. Fix the affected array expansions instead of
  broadly disabling nounset.
- Run the regression cases with an explicitly selected Bash 3.2 and a modern
  Bash. Ensure spawned `#!/usr/bin/env bash` scripts use the intended interpreter
  too. Helper tests must use the entrypoint's `set -euo pipefail` settings where
  they model that entrypoint; do not impose these settings on interactive rc.

Tests: `test_install_tool_core.py`, `test_install_binary.py`,
`test_install_expected_tools.py`, `test_entrypoint.py`, and affected command
tests under `dev/tests/`.

## Update failures

Relevant code: `tools/lib/commands/update.sh`, its cache integration, and
`runme.sh`.

- Return immediately when fetch or reset fails. Do not install or mark the
  checkout current after either failure.
- Cover fetch failure, reset failure, successful refresh, and subsequent
  installation failure. Keep informational `update check` non-mutating.
- Use a temporary local Git remote for at least one public-command regression;
  supplement it with injected failures rather than only checking command logs.
- Review the handoff after reset so installation uses the refreshed code,
  rather than mixing old loaded functions with new files on disk.
- Update `test_update.py` and `test_runme.py` together with the affected flow.

The existing reset policy is documented and tested. Fix error propagation
without silently changing that policy. The recommended separate behavior change
is to refuse dirty or locally diverged checkouts by default, with an explicit
force option for discarding changes. Decide that CLI contract before implementing
it, then update help, install docs, bootstrap behavior, and tests together.

## Ownership and safe removal

Relevant code: release staging, installation detection,
`tools/lib/commands/{prune,uninstall}.sh`, and shared release-path helpers.

- Write a small versioned ownership record inside the staging directory before
  publishing it. Record the tool, pinned version, installation layout, and
  relative executable path. Parse the record as data, never by sourcing it.
- Require a valid ownership record and a direct child directory of the canonical
  install prefix before recursive deletion. Validate tool identity and paths;
  a directory name or a marker filename alone is insufficient.
- Resolve binary and alias targets to their release root, including targets
  nested at `release/bin/nvim`. Protect that whole active release during prune.
- Keep existing unmarked releases usable and report them as legacy/protected.
  Do not infer ownership or create markers merely from `<tool>-*` names. A
  successful reinstall can create a new marked release; old unmarked directories
  remain for manual review.
- Apply the same ownership rules to uninstall, including which symlinks it may
  remove. Preserve symlinks to unrelated tools inside or outside the prefix.
- Test `rg-personal-notes`, an unmarked version-looking directory, malformed
  metadata, mismatched tool identity, relative links, aliases, nested bundle
  targets, and paths outside the prefix. Test actual apply behavior only inside
  temporary directories. Retain prune's dry-run default and uninstall prompts.

Tests: `test_prune.py`, `test_uninstall.py`, `test_install_binary.py`, and their
fixtures. Update old fixtures to identify managed releases explicitly.

## Neovim package layout

Relevant code: `tools/defs/nvim.sh`, definition loading, release staging, and
installed-tool status. The [upstream installation instructions](https://github.com/neovim/neovim/blob/master/INSTALL.md)
preserve the unpacked package layout.

- Extend the exact manifest contract with an explicit bundle mode and relative
  executable path; keep single-binary installation as the default.
- Preserve the selected package root, including `bin`, `share`, and any packaged
  libraries. Before unpacking bundle archives, validate member paths and link
  destinations so extraction cannot write outside staging. Add this prerequisite
  before enabling bundle mode. Do not choose an arbitrary first matching binary.
- Reuse staging and symlink switching. A failed bundle install must preserve
  the previous working release.
- Treat an old single-file Neovim install as incomplete even when its version
  matches, so a normal reinstall can repair the layout.
- Use local archive fixtures for layout, failure, alias, status, and prune tests.
  Validate a real pinned package when it is available locally: headless startup,
  bundled vimrc, runtime lookup, syntax/filetype loading, and help access.
  Synthetic fixtures alone do not establish that the upstream package works.
- Update `test_tool_assets.py` and `docs/tools.md` for the manifest extension;
  adjust the live checker only if its assumptions require it.

Deliver this after ownership protection, because bundle executables are nested
below the release root. Keep the pinned version and selected assets unchanged.

## History and SSH helpers

For history, coordinate `06-bash-history.sh`, `20-fzf.sh`, and `23-atuin.sh`:

- Select the backend based on successful integration activation, not merely
  whether an Atuin executable exists. Disable Bash file writes only when Atuin
  actually owns persistent history.
- Preserve an explicit user `HISTFILE`, including an intentional empty value or
  `/dev/null`; provide ordinary Bash persistence when no backend was configured.
- Keep reload behavior consistent, without accumulating duplicate hooks. Enable
  fzf fallback when Atuin is installed but disabled or initialization fails.
- Test interactive startup and reload with Atuin absent, disabled, working,
  and failing, plus user-provided history settings. Verify a second shell can
  read history from the fallback backend in an isolated HOME.

For SSH, coordinate `scripts/ssh_find.py`, `bin/ssh-find`, and `30-ssh-pick.sh`:

- Define one record format that preserves empty columns. Keep the current
  seven fields stable and carry the selected SSH config path explicitly.
- Pass an explicitly selected config path to `ssh -F` for config-backed records.
  Automatic selection must retain ordinary OpenSSH config loading; see the
  follow-up plan above. Direct bssh records retain optional user and port behavior.
- Test empty user, empty port, both empty, paths containing spaces, selector
  cancellation, backend failure, and forwarding remote-command arguments.
  Assert the exact ssh arguments and use local `ssh -G` to verify custom-config
  resolution without opening a network connection.

Tests: `test_tool_init_shell.py`, `test_shell_helpers.py`, and
`test_ssh_helpers.py`. Update helper documentation with any record-contract or
history-policy change. Startup optimization remains deferred.

## Tmux configuration

- Preserve the restart action behind `confirm-before` so `prefix+q` cannot kill
  the pane process immediately.
- Derive shell-launch and reload paths from the actual checkout. Check both the
  standard install location and an alternate checkout with spaces in its path.
- Confirm the chosen Bash matches the compatibility policy. Configuration
  loading should work on Linux and macOS without requiring Homebrew Bash.
- Validate in an isolated tmux server with temporary HOME and a separate socket;
  never reload or kill the user's active server. Cover canceled and confirmed
  restart behavior using a disposable pane.

Keep `aggressive-resize`, scrollback size, split conventions, and other personal
keybinding preferences outside the correctness fix. Do not add automatic tmux
or Zellij startup.

## Verification and boundaries

- Run targeted regressions while implementing each change, then `just smoke`.
  The audit baseline was 242 passing tests; it did not cover the failure cases
  listed above.
- Keep routine regression tests offline with isolated HOME, XDG directories,
  installation paths, and temporary Git repositories.
- Do not run `just test-assets-live` unless explicitly requested. A pinned
  upstream-package check is a separate validation step from mocked regressions.
- Keep exact asset selection, runtime dependency limits, expected-tools user
  configuration, and install confirmation semantics intact.
- General archive hardening for the remaining install paths and missing pinned
  checksum coverage remain additional work in [TODO](../../docs/TODO.md).
  Bundle extraction requires the path and link validation described above.
