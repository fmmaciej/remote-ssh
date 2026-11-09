# Tool Checksums

Approved by the human on 2026-11-02 after review in chat.
Workflow: [multi-agent implementation](../multi-agent-workflow.md).

## Approved Plan

### Goal and Current Behavior

Complete pinned SHA-256 coverage wherever verified upstream hashes are available
for the nine definitions identified in TODO. The runtime already verifies a
selected checksum before extraction or installation; these nine definitions
currently omit `CHECKSUMS`.

The planner checked official GitHub release metadata for the exact pinned
versions. Seven releases provide SHA-256 digests for all 33 declared assets:

| Tool | Pinned release and source | Assets to cover |
| --- | --- | ---: |
| bat | [v0.26.1](https://api.github.com/repos/sharkdp/bat/releases/tags/v0.26.1) | 6 |
| eza | [v0.23.4](https://api.github.com/repos/eza-community/eza/releases/tags/v0.23.4) | 3 |
| fd | [v10.3.0](https://api.github.com/repos/sharkdp/fd/releases/tags/v10.3.0) | 6 |
| fzf | [v0.67.0](https://api.github.com/repos/junegunn/fzf/releases/tags/v0.67.0) | 4 |
| nu | [0.112.2](https://api.github.com/repos/nushell/nushell/releases/tags/0.112.2) | 6 |
| nvim | [v0.11.5](https://api.github.com/repos/neovim/neovim/releases/tags/v0.11.5) | 4 |
| zoxide | [v0.9.9](https://api.github.com/repos/ajeetdsouza/zoxide/releases/tags/v0.9.9) | 4 |

For [navi v2.23.0](https://api.github.com/repos/denisidoro/navi/releases/tags/v2.23.0)
and [yazi v25.5.31](https://api.github.com/repos/sxyazi/yazi/releases/tags/v25.5.31),
the checked releases have `digest: null`, no checksum assets, and no hashes in
their release descriptions. Their ten declared assets remain explicit
exceptions. This describes the checked official sources, not proof that no
other hashes exist anywhere.

The other twelve definitions already cover 56 assets. The expected repository
result is 89 of 99 declared assets covered and ten documented exceptions.

### 1. Add Pinned Checksums

Add 33 `CHECKSUMS` entries to `tools/defs/{bat,eza,fd,fzf,nu,nvim,zoxide}.sh`.
Recheck the exact repository, release tag, asset name, and `assets[].digest` from
the source endpoints above. Accept only `sha256:` followed by 64 hexadecimal
digits and store the hash in the existing manifest format.

Preserve versions, `ASSETS` entries and their order, aliases, and Neovim's bundle
layout. Do not update tool versions to obtain hashes. Do not present a locally
calculated sum alone as trusted evidence of upstream origin.

### 2. Document Sources and Exceptions

Create `docs/tool-checksums.md` recording the verification date, repositories,
release tags, source API URLs, the `digest` field, coverage counts, and the exact
ten asset exceptions for navi and yazi. Link it from `docs/tools.md` and update
the checksum item's completed scope and remaining exceptions in `docs/TODO.md`,
preserving earlier edits.

### 3. Strengthen Manifest Tests

In `dev/tests/test_tool_assets.py`, check valid SHA-256 syntax and references to
declared assets, reject duplicate checksum names/records, and enforce complete
coverage across all definitions except for the explicit ten exceptions.

Bind each exception to repository, release tag, and asset name, so a new version
or newly declared asset cannot inherit an exception automatically. Enforce the
one-to-one asset/checksum contract outside those exceptions.

### 4. Prove Failure Before Extraction

Strengthen the existing bad-checksum scenario in
`dev/tests/test_install_failures.py` with an extractor-call trace. Assert a
nonzero result, no extraction, no publication of the new release, and retention
of the previous working installation.

### 5. Validate the Implementation

Run the relevant offline tests for manifests, checksum handling, installation
failures, bundles, and the generator. Then run `just smoke` and
`git diff --check`, recording actual commands and results.

Do not run `just test-assets-live`, download all release archives, or install
real tools. The direct release-metadata queries needed for provenance are part
of this task; they do not authorize the separate live asset checker.

### 6. Independent Audit

After the implementer hands off, a separate auditor checks plan conformance,
the implementation diff, exceptions, and test coverage. The auditor independently
compares all 33 added values with freshly retrieved official release metadata.
Changed sources, conflicting hashes, or required scope expansion go back to
the planner.

### Scope Boundaries

No changes to runtime, generator, live checker, tool versions, dependencies,
signature verification, archive validation, or test-file organization.

### Acceptance Criteria

- All 33 new values match the exact official release asset digests.
- All existing versions, asset selections, aliases, and bundle layouts remain.
- Sources and all ten exact exceptions are documented.
- Offline tests enforce valid, unique, complete checksum mappings, with only
  release-specific exceptions.
- A bad checksum stops installation before extraction or publication and
  preserves the previous working release.
- Required validation passes and the independent audit returns a pass.

## Execution Record

The coordinator maintains this record without rewriting the approved plan.
The initial implementation and audit are round zero. Up to two automatic
repair rounds may follow. If required fixes remain after repair round 2, the
planner must explain the causes and present a revised plan for human approval
before further implementation.

### Initial Handoff

- Human approval received on 2026-11-02.
- Coordinator owns this plan and workflow/task records.
- Implementer owns the seven definitions, the two test files, and checksum
  documentation/TODO changes described above.
- Pre-existing work includes the TODO cleanup, `docs/multi-agent-workflow.md`,
  and `docs/plans/README.md`; preserve it.
- Status: implementation pending; audit pending; automatic repair rounds used: 0.

### Initial Implementation Clarification: Synthetic Bundle Checksum

- The first focused run returned 82 passed and 2 failed. The valid Neovim
  bundle fixture failed on both Bash versions because it copies the production
  definition but downloads a synthetic archive whose hash differs from the new
  upstream checksum. Invalid bundle cases could also stop at that mismatch
  instead of exercising bundle validation.
- The planner classified the fixture adjustment as maintenance within the
  approved bundle-test validation scope and handed it directly to the
  implementer. Ownership additionally covers `dev/tests/test_install_bundle.py`
  solely for this fixture correction.
- After creating each synthetic archive, calculate its local SHA-256 and set
  `CHECKSUMS` in the isolated test definition to that archive's name and hash.
  Assert `Checksum OK` so invalid-package cases demonstrably reach subsequent
  bundle validation. Preserve existing success and rollback assertions.
- This local hash is test-fixture data, not evidence of upstream provenance;
  production manifests continue using official release digests.
- Rerun bundle tests on both runtime Bash versions, the focused suites, and
  `just smoke`. Initial focused log:
  `/tmp/remote-ssh-checksum-implementation/focused.log` (temporary evidence).
- This completes the initial implementation before its first audit. Automatic
  repair rounds used: 0; audit still pending.

### Initial Validation Progress

- Focused tests after the fixture correction: 84 passed in 13.34 seconds.
  Temporary log: `/tmp/remote-ssh-checksum-implementation/focused-final.log`.
- The first `just smoke` attempt passed Bash syntax and ShellCheck, then stopped
  at Python checks because the sandbox denied creating a temporary file in
  `/Users/fm/.cache/uv`. This attempt is not a passing smoke result.
  Temporary log: `/tmp/remote-ssh-checksum-implementation/smoke.log`.
- An appropriately authorized retry and independent audit are still pending.

### Initial Implementation Handoff

- The implementer added all 33 upstream digests and confirmed that the previous
  contents of the seven definitions are otherwise unchanged. Repository totals
  are 21 definitions, 99 assets, 89 checksums, and ten exact exceptions.
- Focused command:
  `dev/.venv/bin/python -m pytest -q dev/tests/test_tool_assets.py dev/tests/test_install_tool_core.py dev/tests/test_install_failures.py dev/tests/test_install_bundle.py dev/tests/test_generate_def.py`
  returned 84 passed in 13.34 seconds.
- Ruff check and format `--check` passed for the three changed test files.
- The retry with output redirection waited for authorization and was interrupted
  before execution; it produced no log or confirmed running process. A direct
  `just smoke` invocation then used the existing approved command rule and
  completed with exit 0: Bash syntax, ShellCheck, Ruff, and mypy passed, and
  pytest returned 1256 passed, 30 skipped in 442.88 seconds.
- Successful smoke evidence:
  `/tmp/remote-ssh-checksum-implementation/smoke-escalated.log` (temporary).
  `coverage.json` and the nine source API responses are in the same directory.
- Final implementation `git diff --check` returned exit 0.
- No live asset checker, archive downloads, or real tool installations were run.
- Status: implementation complete; independent audit in progress; automatic
  repair rounds used: 0.

### Independent Audit and Completion

- Auditor outcome: **PASS**, with no required fixes. The auditor made no
  repository changes.
- Fresh, independently retrieved metadata for all nine releases confirmed all
  33 added hashes, repository coverage of 89/99, and the exact ten documented
  navi/yazi exceptions. The seven definitions contain only the checksum
  additions; versions, asset mappings, aliases, and layouts are preserved.
- Independent execution of the focused suites returned 84 passed in 12.90
  seconds. Nine mutations in temporary manifest copies were correctly rejected,
  covering missing and duplicate checksums, invalid hashes, unknown assets,
  changed exception tags/repositories, new assets, and obsolete exceptions.
- The auditor confirmed failure before extraction/publication, preservation of
  the working binary and alias, and meaningful bundle validation after the
  synthetic-fixture correction. The full successful smoke log was reviewed;
  no additional smoke run was needed.
- Documentation, local links, and `git diff --check` passed review. Source
  provenance and exceptions are in [pinned tool checksums](../tool-checksums.md).
- Temporary audit evidence: `/tmp/remote-ssh-checksum-audit/audit-result.md` and
  `/tmp/remote-ssh-checksum-audit/independent-report.json`.
- Final status: complete; audit PASS; automatic repair rounds used: 0.
  The earlier fixture clarification belongs to the initial implementation,
  not an audit repair round. No commit or publication was performed.
