# Refactor Audit Stage 3: Install Core

Date: 2026-06-01

This report audits the install core for refactor readiness. It covers
`tools/lib/install/`, `tools/lib/install-tool/`, `tools/install-tool.sh`, the
runtime-facing parts of `tools/lib/common/`, the contract with `tools/defs/`,
and the install-state boundary shared with `check`, `doctor`, `prune`,
`uninstall`, and `tool_status`. It does not apply code changes.

## Findings

### 1. Install idempotency ignores binary aliases

Risk: medium

References:

- `tools/lib/install/install.sh:52-56` loads the tool definition, then skips
  install as soon as `is_tool_installed "$TOOL_NAME" "$VERSION"` succeeds.
- `tools/lib/install/install.sh:5-25` checks only the primary binary symlink.
- `tools/lib/install-tool/install.sh:169-174` installs aliases only during a
  full `install_binary` run.
- `tools/lib/commands/tool_status.sh:95-113` treats aliases as part of tool
  health and marks the tool problematic when an alias is missing or stale.

If a primary binary is already pinned correctly but an alias such as
`nushell` is missing, stale, or unmanaged, `remote-ssh install nu` can skip the
install and leave `remote-ssh check --strict` reporting a problem. The status
surface already models aliases, but the install idempotency gate does not.

Suggested order:

1. Add a test where the primary symlink is correct but an alias is missing or
   stale.
2. Decide whether install should repair aliases in place or force the normal
   staged reinstall path.
3. Keep unmanaged alias protection behavior from `install_binary` intact.

### 2. A failed symlink switch can leave a new inactive release directory

Risk: medium

References:

- `tools/lib/install-tool/install.sh:150-167` creates a staging directory,
  copies the binary, and moves the stage into its final release directory.
- `tools/lib/install-tool/install.sh:94-95` validates link paths inside
  `install_binary_switch_links`.
- `tools/lib/install-tool/install.sh:123-125` rolls back symlinks after a
  partial switch failure.
- `tools/lib/install-tool/install.sh:174` returns failure from
  `install_binary` without removing the newly moved release directory.

The symlink rollback behavior is careful, and existing tests protect the
previous working binary. The release directory created for the failed install
can still remain under `$INSTALL_PREFIX` when link validation or switching
fails after the stage has moved. That is not a broken active install, but it is
extra inactive state created by a failed reinstall.

Suggested order:

1. Add a test that fails after `release_dir` is created and asserts the desired
   cleanup policy.
2. If failed installs should be fully clean, remove only the newly created
   release dir after link switch failure.
3. Preserve old release directories and old symlinks exactly as they are today.

### 3. Managed path classification is duplicated and not fully consistent

Risk: medium

References:

- `tools/lib/install/install.sh:22-25` treats a primary symlink as installed
  when `readlink` matches an absolute `$INSTALL_PREFIX/<tool>-<version>/...`
  pattern.
- `tools/lib/commands/tool_status.sh:26-35` uses a separate version of the
  same absolute target matcher.
- `tools/lib/commands/prune.sh:12-23` canonicalizes symlink target directories
  and handles relative symlinks when protecting active releases.
- `tools/lib/commands/uninstall.sh:67-103` has another managed-link
  classifier, including canonical and broken-target fallback behavior.
- `tools/lib/install/tool_inventory.sh:20-29` detects installed tools through a
  primary-symlink-only absolute target pattern.

The command set now has several definitions of managed install state:
primary-only versus alias-aware, absolute string matching versus canonical
path matching, and active install status versus deletion protection. The
differences are mostly covered by targeted tests today, but they make any
follow-up refactor risky because a behavior fix in one command can easily leave
another command with the old semantics.

Suggested order:

1. Write focused tests for the intended shared model: absolute symlink,
   relative symlink, broken symlink into `$INSTALL_PREFIX`, alias symlink, and
   suffixed release directories.
2. Define one internal ownership helper for "managed link target" and one for
   "release directory owned by a known tool".
3. Convert one command at a time, starting with read-only status/check paths
   before deletion paths.

### 4. Download tempdir cleanup assumes one install-tool process per tool

Risk: low

References:

- `tools/lib/install-tool/download.sh:80-81` assigns global `TMPDIR` and
  installs an `EXIT` trap for cleanup.
- `tools/lib/install-tool/download.sh:98` exposes the temp directory through
  global `EXTRACT_DIR`.
- `tools/lib/install-tool/main.sh:33-35` immediately installs from
  `EXTRACT_DIR`.
- `tools/lib/install/install.sh:56` currently invokes `tools/install-tool.sh`
  as a separate process per tool.

The current CLI path makes this mostly safe because each tool install runs in
its own `tools/install-tool.sh` process. The library is still sourceable,
though, and the global `TMPDIR` plus process-wide `EXIT` trap would be fragile
if future refactors installed multiple tools in one shell process or composed
`download_and_extract` with other traps.

Suggested order:

1. Keep one-process-per-tool behavior unless there is a measured reason to
   change it.
2. Before in-process install refactors, add tests for temp cleanup after
   checksum, extraction, and install failures.
3. Prefer a private temp variable and explicit cleanup ownership if this code
   is made reusable.

### 5. GitHub API helpers are currently outside the runtime install path, but the common aggregator is broad

Risk: low

References:

- `tools/lib/install.lib.sh:10-21` sources only platform, requirements,
  definitions, asset selection, install, dirs, and post-install modules.
- `tools/lib/install-tool.lib.sh:9-19` sources platform, requirements,
  extract, definitions, assets, download, install, and main modules.
- `tools/lib/common/requirements.sh:7-19` checks only the documented core tools
  and records optional `unzip` support.
- `tools/lib/common/extract.sh:14-19` gates `.zip` extraction on
  `ZIP_SUPPORTED`.
- `tools/lib/common.lib.sh:8-12` still sources `tools/lib/common/github.sh`
  as part of the broad common bundle.

The install libraries do not load `tools/lib/common/github.sh`, and the exact
asset manifest path does not use GitHub API discovery, `jq`, Python, package
managers, or source builds. The remaining risk is future accidental use of the
broad `common.lib.sh` aggregator from runtime install code, which would pull
developer-oriented GitHub helpers into the source graph.

Suggested order:

1. Keep install libraries sourcing precise common modules rather than
   `common.lib.sh`.
2. Treat `tools/lib/common/github.sh` as Stage 4 generator/developer scope.
3. Add a lightweight source-graph test only if future refactors touch common
   aggregators.

## Refactor Candidates

- Make install idempotency alias-aware, preserving the existing unmanaged alias
  refusal and symlink rollback rules.
- Clean up a newly created release directory when link switching fails, while
  preserving previous active releases.
- Introduce small install-state helpers for managed symlink targets and known
  release directory names, then migrate status/check before prune/uninstall.
- Keep `download_and_extract` process-local unless a future refactor removes
  the `tools/install-tool.sh` subprocess boundary.
- Keep runtime install code on precise module imports. Do not source
  `common.lib.sh` from install paths unless GitHub helpers are split out first.
- Decide the Stage 2 `prune` dry-run mutation policy before touching shared
  release-directory discovery, because `prune` currently creates
  `$INSTALL_PREFIX` before dry-run discovery.

## Risk

| Area | Risk | Why |
| --- | --- | --- |
| Alias-aware install idempotency | medium | Status/check already treat aliases as required, but install may skip repair when the primary binary is current. |
| Failed install cleanup | medium | Active symlink rollback is covered, but failed attempts can leave new inactive release directories. |
| Shared managed-state semantics | medium | Multiple commands encode similar ownership rules differently, including relative symlink handling. |
| Tempdir/trap ownership | low | Current subprocess isolation contains the risk, but the sourceable library API is fragile for future reuse. |
| Runtime dependency boundary | low | The install path avoids GitHub API helpers today; the broad common aggregator is the main future footgun. |
| Expected tools and profiles | low | Existing tests cover saved expected tools, profile selection, unsupported filtering, and confirmation behavior. |
| Asset selection and checksum contract | low | Exact manifests, pinned versions, platform fallback, and checksum shape have focused tests. |

## Test Coverage Needed

Existing useful coverage:

- `dev/tests/test_install_tool_core.py` covers archive staging, raw executable
  staging, checksum match/mismatch, exact-version rejection, missing asset
  errors, install idempotency, external PATH tools, and stale local versions.
- `dev/tests/test_install_binary.py` covers aliases, symlink rollback on
  failure, and unmanaged alias protection.
- `dev/tests/test_install_expected_tools.py` covers expected-tools read/write,
  selected installs, confirmation, unsupported filtering, profiles, and
  `remote-ssh tool install` not changing expected tools.
- `dev/tests/test_tool_assets.py` covers exact asset manifests, Linux glibc
  fallback, `any` fallback, no-match behavior, and checksum manifest shape.
- `dev/tests/test_check.py` and `dev/tests/test_doctor.py` cover tool status,
  aliases, strict failure statuses, path shadow hints, and missing expected
  config guidance.
- `dev/tests/test_prune.py` and `dev/tests/test_uninstall.py` cover
  conservative deletion, relative symlink protection, alias uninstall, expected
  config updates, and unmanaged path protection.

Targeted tests to add before follow-up refactors:

- `remote-ssh install` should repair or reinstall when the primary binary is
  current but an alias is missing, stale, or unmanaged.
- `install_binary` should either clean up a newly created release dir on link
  switch failure or explicitly document that prune owns that cleanup.
- Shared managed-state helpers should be tested against absolute symlinks,
  relative symlinks, broken symlinks into `$INSTALL_PREFIX`, aliases, and
  suffixed release directories.
- Checksum verification should cover the missing `sha256sum`/`shasum` path
  for assets with pinned checksums and should confirm assets without checksums
  do not require hash tools.
- Zip extraction should cover the selected-zip-without-`unzip` path and keep
  the failure clear.
- If `prune` dry-run becomes strictly informational, add a test that a missing
  `$INSTALL_PREFIX` is not created.
- If `download_and_extract` becomes reusable in-process, add temp cleanup tests
  for download, checksum, extraction, and install failures.

No `just smoke` or `just test-assets-live` was run for this audit-only stage.

## Suggested Order

1. Add focused tests for alias-aware idempotency and failed-release-dir cleanup.
2. Fix alias repair or forced reinstall while preserving unmanaged alias
   protection.
3. Clean up only the new release directory after link switch failures.
4. Define and test shared managed-state helpers for symlinks and release dirs.
5. Migrate status/check and tool list to the shared helpers first.
6. Migrate prune and uninstall after deletion-protection behavior is fully
   covered.
7. Revisit `download_and_extract` temp ownership only if install-tool
   subprocess isolation is changed.
8. Keep GitHub release helpers out of runtime install libraries; audit those
   deeply in Stage 4.
