# Managed fzf retirement plan

Created: 2026-11-10
Status: phase 1 implemented and verified; phase 2 awaits host migration
Accepted scope: retire the managed fzf package in favor of skim, retaining Navi's private protocol adapter.
Baseline and recovery revision: `c5fa54c70fba2ca931af5b241f166fb6bec98a06`.

## Boundary

Skim is already used by quick/full profiles, SSH selection, zoxide selection,
the Bash history fallback and the managed Navi adapter. The remaining package
definition is `tools/defs/fzf.sh` (fzf 0.67.0, four pinned assets/checksums).

Keep `shell/navi-bin/fzf`, its process-tree isolation and Navi's fzf-named options.
That executable translates the pinned Navi protocol into real skim calls.
Explicit external finder choices continue to pass through to Navi. No global
`fzf=sk` alias or general compatibility layer is introduced.

The expected-tools file and independently installed fzf belong to the user.
No update automatically edits configuration, removes software or changes finder
preferences. No SSH connection or fleet-wide inspection is part of phase 1.

## Phase 1: prepare migration

Commit: `chore(fzf): prepare retirement and document migration`.

1. Save this accepted plan and link it from developer documentation.
2. Add read-only doctor diagnostics when expected-tools contains fzf or a valid
   managed fzf installation exists. Warn even when skim is already installed;
   do not warn merely because an external fzf executable is on PATH.
3. Keep the diagnostic informational: it must not alter otherwise healthy doctor
   status, expected-tools bytes, managed links/releases or external executables.
4. Keep the legacy definition installable/uninstallable during migration and
   preserve all four exact asset/checksum mappings. Mark its transitional status.
5. Document installation/check of skim, manual expected-tools/finder adjustment,
   fresh-session verification and explicit removal of managed fzf only.
6. Document recovery from the exact baseline revision for a host that later
   skips the migration window. Override REMOTE_ENV_DIR when invoking that checkout
   so an inherited current-checkout setting cannot redirect recovery.
7. Exercise doctor decisions and simulated skipped-window recovery offline on
   both system and PATH Bash. Verify that only owned fzf is removed, skim and
   external fzf remain, and existing unrelated .active paths are untouched.
8. Run targeted tests, changed-test lint/format checks and full `just smoke`.
   Preserve the Navi dispatcher/adapter bytes and existing tests.

## Host migration gate

After phase 1 is available, each used installation must:

1. Use its existing INSTALL_PREFIX, INSTALL_BIN_DIR and XDG configuration.
2. Run `remote-ssh tool install sk` and `remote-ssh check --strict sk`.
3. Change an existing fzf entry in expected-tools to sk, avoiding duplicates and
   preserving unrelated entries. If configuration is absent, choose the desired
   tool set deliberately rather than creating/replacing it automatically.
4. Review an explicit NAVI_FINDER=fzf and custom picker flags. Navi's
   NAVI_FZF_OVERRIDES names remain valid; arbitrary FZF_DEFAULT_OPTS are not
   automatically translated into skim options.
5. Verify the used pickers in a new remote-ssh shell: Navi snippets/parameter
   input/Enter/Tab/cancel, zoxide selection, SSH host selection and Bash history
   fallback when that backend is selected.
6. Run `remote-ssh uninstall fzf` after successful skim verification, then check
   the saved tool set. Keep independently managed/system fzf when desired.

The human must confirm the used installations have migrated before phase 2.
The two delivery commits are separate deployment stages, not one combined push.
Phase 1 does not claim that host migration has already happened.

## Phase 2: retire the active definition

Commit: `chore(tools): retire managed fzf package`.

1. Remove tools/defs/fzf.sh and current package/catalog/checksum support claims.
2. Update asset snapshots and tests whose unrelated fixtures happened to use fzf.
   Keep migration, ownership protection, private protocol and native pass-through
   isolation tests. Preserve historical reports and measurements.
3. Keep a clear recovery guide for old expected-tools entries and managed fzf.
   Do not relax release ownership validation to delete unknown directories.
4. Verify the existing unknown-tool behavior: a saved mixed set can still
   install its known tools with a diagnostic; a set containing only retired fzf
   has no supported selection. Explicit fzf installation is rejected.
5. Verify all managed pickers without a real fzf executable in PATH, including
   a bounded real Navi/skim PTY run, and run `just smoke`.
6. Publish/deploy this second stage only after the host migration gate.

## Acceptance and records

Phase 1 is done when its read-only diagnostics, retained definition, recovery
procedure and full checks pass and its local commit is created.
Phase 2 is intentionally deferred until the explicit host migration confirmation.
No Git push, host configuration edit or installed-tool cleanup is implicit.

## Execution

Phase 1 implemented and verified on 2026-11-10.

- New doctor regression before implementation: **8 failed, 6 passed**; missing
  migration output was the cause of the eight expected failures.
- Targeted doctor, retained-definition and recovery tests: **87 passed** on
  system Bash 3.2 and Homebrew Bash 5.3.20.
- Full `just smoke`: **1615 passed, 56 skipped** in 383.70s (0:06:23).
  Bash syntax, ShellCheck, Ruff and mypy passed. Changed test files also pass
  Ruff lint and formatting checks.
- The actual documented Git revision was cloned locally and checked out in
  detached HEAD. Its cleanup passed on both Bash versions with a custom prefix,
  proving preservation of skim, external fzf and the unrelated .active sentinel.
- The private Navi dispatcher/adapter remain byte-identical to baseline.
  All seven fzf manifest fields remain semantically identical.
- [Evidence and reproduction](fzf-retirement-evidence/README.md) records the
  source, recovery outputs and final verification fingerprints.
- No used host was inspected or migrated; no user configuration was edited.
  The fzf definition remains available, and phase 2 requires the agreed host
  migration confirmation before removal.
- Phase 1 is delivered as the planned local commit; repository push and host
  deployment remain separate external actions.

Temporary local clones and synthetic installations remain in the ignored Kei
runtime `00-system/var/cache/kei-tools/fzf-retirement/20261110-stage1-8jqnltfr/`.
They contain public project code and synthetic tool/configuration data. The
durable plan and selected evidence were saved in the project under the accepted
implementation scope. Cleanup can remove this exact run after review.
