# Binary Selection

Approval: the human accepted the plan presented in this conversation.
Workflow: [multi-agent implementation](../multi-agent-workflow.md).

## Approved Plan

### Goal and Current Behavior

Make single-binary selection deterministic after extraction, allow an explicit
path when a package layout needs one, and preserve working installations on
selection failure.

The current selector uses `find -maxdepth 4 -type f -name ... | head -n1`.
The planner reproduced two problems on Bash 3.2 and modern Bash: a binary name
such as `demo[1]` matches `demo1` as a pattern, and a producer that prints a
candidate before failing can be treated as successful. Selection also depends
on traversal order when multiple matching executables exist.

`load_defs` already defaults `BINARY_PATH` to `BINARY_NAME` for ordinary
installations. Preserve that existing contract while distinguishing an
explicit path from its default with internal state.

### 1. Automatic Selection Contract

- Preserve the current search limit of `maxdepth 4`.
- Compare each candidate basename literally with `BINARY_NAME`; do not interpret
  `*`, `?`, or `[]` as patterns.
- A valid candidate is a regular executable file with an allowed relative path
  and no symlink in that relative path, including its final component.
- Exactly one valid candidate succeeds, even when other matching entries are
  non-executable files, directories, or symlinks.
- Multiple valid candidates fail with an ambiguity diagnostic and their paths.
- No valid candidate fails with the matching paths and rejection reasons, or
  a clear not-found diagnostic when no matching entry exists.
- Never resolve ambiguity by choosing the first match.

### 2. Explicit Binary Paths

- Support an explicitly declared `BINARY_PATH` for ordinary installations.
- Keep the existing default `BINARY_PATH=BINARY_NAME`. In `load_defs`, compute
  an internal marker identifying whether the definition supplied the path;
  reset that marker on every load so it cannot leak between tools.
- The explicit path is relative to the extraction directory. It may be deeper
  than the automatic search limit and may have a different basename. Ordinary
  installation still publishes the selected file as `BINARY_NAME`.
- An explicitly empty, unsafe, absent, or invalid path fails without falling
  back to automatic discovery.
- Reject absolute paths, traversal, invalid separators, control characters,
  and symlinks in any component of the relative path, including symlinks whose
  target is inside the package. Preserve spaces and apostrophes.

### 3. Complete Results and Error Propagation

- Write the complete `find ... -print0` output to a private temporary file and
  check its exit status before examining candidates.
- Read NUL-delimited records using Bash-compatible facilities. Do not use
  `head`, whitespace splitting, or process substitution that hides the
  producer's status.
- Any scanning failure, including failure after partial output, stops selection.
- Render paths safely in diagnostics, for example with `printf %q`. Selector
  stdout contains only the selected relative path.
- Clean up the temporary file on success and failure without interfering with
  the existing download-directory cleanup trap.

### 4. Raw Assets, Bundles, and Publication

- Retain raw-asset preparation of the `BINARY_NAME` file. Literal matching must
  not count a differently named original download as another candidate.
- Bundles continue using declared `BINARY_PATH` relative to `BUNDLE_ROOTS`,
  without automatic discovery.
- Finish selection and source validation before creating or publishing a new
  release. Preserve validation of the staged executable, metadata, staging,
  alias switching, and rollback.
- This is validation after extraction, not protection against writes performed
  while unpacking an archive. Archive hardening remains a separate task.

### 5. Files and Scope

- `tools/lib/install-tool/defs.sh`: explicit-path state and reset behavior.
- `tools/lib/install-tool/install.sh`: selection, path validation, diagnostics,
  temporary-result cleanup, and failure propagation. Keep helpers here unless
  implementation evidence justifies a different organization.
- `dev/tests/test_install_binary.py`: public-installer regressions using local
  synthetic assets and the available `runtime_bash` variants.
- `dev/tests/test_tool_assets.py`: explicit/default path contract and state
  isolation between definitions.
- `docs/tools.md` and the relevant `docs/TODO.md` item: document the resulting
  selection contract and completed scope.

No changes to production tool definitions, versions, `ASSETS`, checksums,
generator, live checker, dependencies, or test-file organization. No changes
to `download.sh` or `main.sh` are currently required. Preserve all previous
checksum work and the existing documentation cleanup.

### 6. Regression Coverage and Validation

Cover these observable behaviors:

- Unique flat and nested executables; one valid candidate alongside matching
  non-executable, directory, and symlink entries.
- Multiple valid executables, no match, and only rejected entries.
- Explicit-path disambiguation; invalid explicit paths despite an available
  alternative; and an explicit path deeper than the automatic limit.
- Literal metacharacters, spaces, apostrophes, rejected control-character
  paths, and symlinked parent directories.
- A scanner that emits a candidate and then fails, and the depth 4/5 boundary.
- Raw assets, bundle behavior, aliases, the previous release, and cleanup on
  failure.

Use available Bash 3.2 and modern Bash variants. Run the focused binary, core,
failure, bundle, and asset tests, followed by `just smoke` and
`git diff --check`. Use local fixtures; do not query release services, download
real release archives, or run `just test-assets-live` for this task.

### Acceptance Criteria

- Every selection obeys the automatic or explicit contract above independently
  of traversal order.
- Invalid paths and incomplete scans cannot publish a new release or alter
  the previous working binary and aliases.
- Internal explicit-path state does not leak between definitions.
- Temporary selection data is removed on success and failure, preserving
  download cleanup.
- Raw assets, bundles, staging, metadata, and existing checksum behavior remain
  covered by passing regressions.
- Required checks pass and a separate auditor confirms correctness and
  conformance to this plan.

## Execution Record

The coordinator maintains this record without rewriting the approved plan.
The first implementation and audit are round zero. At most two automatic
planner/implementer/auditor repair rounds may follow. Required fixes remaining
after repair round 2 require an explanation and a revised plan approved by the
human before further implementation.

### Initial Handoff

- Human approval received in chat before saving this plan.
- Coordinator owns this plan, the plans index, and workflow/task records.
- Implementer owns the six implementation/test/documentation files listed
  in the approved scope.
- Earlier checksum changes, TODO cleanup, and workflow files remain in the
  uncommitted worktree and must be preserved.
- Temporary pre-task evidence:
  `/tmp/remote-ssh-binary-selection-baseline-_n632rdi/` contains tracked-file
  hashes, the pre-existing diff/status, and copies of the six scoped files.
  Compare with this baseline when auditing this task's changes rather than
  attributing the whole current diff to the new implementation.
- Status: implementation pending; audit pending; automatic repair rounds used: 0.

### Concurrent Worktree Changes

- During the initial implementation, the coordinator observed a separate change
  to `dev/docs/flyline-implementation-plan.md`, absent from the baseline snapshot.
  It is outside this task's ownership and must be preserved, not attributed to
  the binary-selection implementation merely because it appears in the diff.
- A later baseline comparison also found a concurrent change to `dev/README.md`.
  Preserve that documentation change as well; the implementer owns neither file.
- Associated concurrent flyline pilot records/evidence later appeared under
  `dev/docs/`. They are also outside this task and must be preserved.

### Initial Implementation Handoff

- The implementer changed the six scoped files only. Existing checksum work
  and concurrent documentation edits were preserved.
- Focused command:
  `dev/.venv/bin/python -B -m pytest -q -p no:cacheprovider dev/tests/test_install_binary.py dev/tests/test_install_tool_core.py dev/tests/test_install_failures.py dev/tests/test_install_bundle.py dev/tests/test_tool_assets.py`
  returned 155 passed in 18.08 seconds. Ruff check/format, ShellCheck, and
  `git diff --check` also passed.
- The first full `just smoke` invocation returned exit 0 without escalation:
  static checks passed, with 1328 passed and 30 skipped in 331.08 seconds.
- Temporary evidence is in
  `/tmp/remote-ssh-binary-selection-implementation/`: `focused.log`,
  `smoke-sandbox.log`, `implementation.diff`, and `source-hashes.json`.
  The six scoped file hashes remained unchanged throughout and after smoke.
- After handoff the implementer reported an unverified edge case: an unsafe
  destination `BINARY_NAME='../escaped'` combined with a valid explicit
  `BINARY_PATH='bin/demo'` might allow copying outside the staging directory.
  The coordinator forwarded it to the independent auditor for confirmation;
  no source changes were made after validation to address it silently.
- Status: initial implementation complete; independent audit in progress;
  automatic repair rounds used: 0. Passing tests do not yet constitute an
  audit pass.

### Initial Audit: Required Destination-Name Validation

- Outcome: **FINDINGS**. In a delivered audit message, the auditor independently
  confirmed that explicit source selection can bypass the effective validation
  previously supplied by automatic name matching. An invalid destination name
  can write outside staging or create malformed release metadata. The auditor
  reproduced the regression on both Bash versions and compared it with the
  pre-task baseline, which did not perform those writes.
- Source locations identified in that audit were `install.sh` lines 231, 236,
  and 245, and definition loading that validates `BINARY_PATH` only. The required
  fix is destination-basename validation before copying or any related write.
- Temporary confirmed evidence:
  `/tmp/remote-ssh-binary-selection-audit/destination-probes.json`.
  The audit also confirmed the implementation's source hashes and full smoke
  result; it did not deliver a completed overall audit pass.
- The auditor's attempted final response failed twice with an orchestration
  message flagging possible cybersecurity risk. The coordinator retained the
  already delivered findings and evidence, stopped retrying those probes, and
  requested a bounded defensive repair from the planner. The failed final
  responses are not recorded as passes or as additional completed audits.
- Status: repair round 1 requested; final independent audit remains required.

### Repair Round 1: Approved-Scope Defensive Fix

- The planner classified destination-name validation as a necessary correction
  within the original staging, metadata, and failure-preservation contract.
  This is automatic repair round 1 of the two allowed rounds.
- Add a shared validator within the scoped runtime files: `BINARY_NAME` must be
  one allowed relative path component, with no `/`. Reuse the existing path
  checks for invalid components and control characters. Preserve literal spaces,
  apostrophes, and metacharacters rather than introducing an alphanumeric-only
  allowlist.
- Apply it in `load_defs` after existing binary-name defaulting, and again at
  the start of `install_binary`, before scanning, staging, copying, or other
  writes that depend on the destination name.
- Add public-installer and direct-helper input-validation regressions. They
  must confirm rejection before download/copy operations and preservation of
  existing links, executable contents, release metadata, and test sentinels.
  Preserve positive coverage for allowed literal names.
- Do not rerun the earlier audit probe scripts. Use bounded regression tests
  for the corrected input contract, followed by the relevant focus, static
  checks, one required `just smoke`, and `git diff --check`.
- The planner hands the repair directly to the existing implementer. File
  ownership remains the same six scoped files; the coordinator owns this record.
- Status: repair round 1 implementation authorized; subsequent independent
  audit pending. No extra human approval is required for this in-scope round.

### Repair Round 1 Validation Progress

- The implementer added the shared name validator in `defs.sh`, used it after
  loader defaulting and at `install_binary` entry, and added bounded regression
  tests whose operation stubs have no filesystem side effects. Positive tests
  preserve allowed literal destination names.
- The repaired focused suite returned 233 passed in 23.09 seconds. Ruff
  check/format, ShellCheck, and `git diff --check` passed.
- Temporary evidence under
  `/tmp/remote-ssh-binary-selection-implementation/` includes
  `repair1-focused.log`, `repair1-source-hashes.json`, and
  `repair1-implementation.diff`. A full post-repair `just smoke` is in progress;
  the implementer froze the six scoped files before that run.
- A fresh independent review of the repaired version is required. The earlier
  reviewer could not deliver its final report, so completion must not rely on
  the earlier interrupted audit alone.

### Repair Round 1 Handoff

- The post-repair `just smoke` returned exit 0: Bash syntax, ShellCheck, Ruff,
  and mypy passed; pytest returned 1406 passed, 30 skipped in 309.89 seconds.
  The focused command recorded above returned 233 passed in 23.09 seconds.
- The final `git diff --check` passed. Scoped file hashes stayed unchanged
  during and after validation. Separate temporary logs and hashes are
  `repair1-focused.log`, `repair1-smoke.log`, `repair1-implementation.diff`, and
  `repair1-source-hashes.json` in the implementation evidence directory.
- A new independent reviewer received the full approved contract, the original
  pre-task baseline, and the final repair evidence. This replaces the reviewer
  whose formal response could not be delivered. The new review uses static
  inspection and standard local regressions rather than rerunning the earlier
  investigative scripts.
- Status: repair round 1 implementation and validation complete; independent
  review of the final version in progress. No second repair round has begun.

### Final Independent Audit and Completion

- Outcome: **PASS** after repair round 1, with no required fixes or optional
  remarks. The new reviewer assessed the entire approved contract and current
  implementation, not only the destination-name correction.
- The audit confirmed validation after loader defaults and at installer entry,
  before operations depending on the name. It also confirmed literal matching,
  unique-valid selection, the depth limit, binding explicit paths, component
  and symlink checks, complete checked NUL scanning, and isolated cleanup.
- The independent focused run returned 233 passed in 22.40 seconds on Bash
  3.2.57 and 5.3.20. `git diff --check` returned exit 0.
- The reviewer inspected the successful post-repair smoke log: 1406 passed,
  30 skipped, with static checks passed. Full smoke was not repeated.
- All six scoped file hashes matched the final implementation evidence. The
  baseline comparison confirmed preservation of earlier checksum work and
  concurrent documentation changes. The reviewer made no repository edits.
- Temporary final audit report:
  `/tmp/remote-ssh-binary-selection-final-audit.json`.
- Final status: complete; independent audit PASS; automatic repair rounds used:
  **1 of 2**. No further repair is required. No commit or publication occurred.
