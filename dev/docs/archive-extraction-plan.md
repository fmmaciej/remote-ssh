# Archive Extraction Implementation Plan

Created: 2026-10-27
Status: not scheduled

The archive hardening proposal was declined as the next implementation step on
2026-10-27. This document remains a reference, not an active implementation plan.

Validate downloaded archives before extracting their contents, then extract into
a fresh private payload directory. An unsafe archive, an unsupported inspection
mode, or a failed extraction must stop installation without changing the active
release or its aliases. Apply the same validation policy to single-binary and
bundle installs, with an additional declared-root constraint for bundles.

Keep Bash 3.2 support and the existing runtime dependency policy. Cover
`.tar.gz`, `.tgz`, and `.zip`; raw executables keep their current path. Missing
SHA-256 coverage, signatures, binary candidate selection, shell optimization,
and tool version changes remain separate work. Resource limits for decompression
and protection against another process running as the same user are outside
this change's containment guarantee.

## Current implementation

- [extract.sh](../../tools/lib/common/extract.sh) runs `tar xzf` or `unzip -q`
  directly for ordinary archives. Bundle extraction separately inspects paths
  and verbose entry types before creating `payload`.
- [download.sh](../../tools/lib/install-tool/download.sh) verifies a checksum
  when present, then stages the asset in a private download directory. Ordinary
  archives currently share that directory with the downloaded file; bundles
  use its `payload` child.
- [install.sh](../../tools/lib/install-tool/install.sh) copies the candidate
  into a release staging directory before publishing it and switching links.
  Preserve this sequence and its existing rollback behavior.
- [release.sh](../../tools/lib/common/release.sh) validates paths used in
  release metadata. Archive paths also need handling for leading `./`, directory
  markers, entry types, and listing escapes; do not broaden the metadata
  validator merely to accept those archive conventions.
- Existing coverage includes successful staging of each supported format,
  download and extraction failures, and unsafe bundle entries. Ordinary archive
  attacks and ambiguous listing output need dedicated regressions.

## Archive policy

Inspect the entire archive successfully before extracting any member. Treat
unknown entry types, ambiguous output, incomplete inspection, and unsupported
capabilities as errors. A post-extraction scan may add checks, but cannot replace
validation before filesystem writes.

| Entry or condition | Planned behavior |
| --- | --- |
| Ordinary file or directory with a safe relative path | Accept. |
| Leading `./` and trailing directory slash | Normalize for validation and collision checks. Accept `.` or `./` only as a root directory marker. |
| Absolute path, `..` component, internal `.` component, or repeated internal separator | Reject before extraction. |
| Backslash, control character, or name whose listing representation is ambiguous | Reject. Do not decode escapes with `eval`, shell sourcing, or `printf %b`. |
| Spaces and quotes in ordinary relative names | Accept without shell evaluation or word splitting. |
| Symbolic link or hard link, including an internal target | Reject in this first implementation. |
| FIFO, device, socket, or other special entry | Reject. |
| Duplicate file, conflicting entry types, or a file used as a parent directory | Reject. Repeated ordinary directory markers may be accepted. |
| Bundle member outside the declared root | Reject using a component boundary, so `root-other` does not match `root`. |
| Empty, truncated, corrupt, encrypted, or uninspectable archive | Fail without publication or interactive prompts. |

Define the supported name representation during the inspection prototype below.
The initial parser may conservatively reject escaped non-ASCII names when their
exact meaning cannot be established. Document that restriction explicitly; do
not silently validate a different name from the one the extractor will use.

## 1 Prove archive inspection behavior

Create small local fixtures with Python's standard-library `tarfile` and
`zipfile`, then inspect them with the real host commands. Python remains confined
to developer tests. Establish the parser contract before changing extraction.

For tar, exercise GNU tar and BSD tar separately. GNU tar provides explicit
[name quoting](https://www.gnu.org/software/tar/manual/html_node/quoting-styles.html);
BSD tar uses its own
[escaped listing output and link descriptions](https://github.com/libarchive/libarchive/blob/master/tar/util.c).
Verify both name and type information, including hard links: checking only the
first character of a verbose line is insufficient across implementations.

For ZIP, start with inspection through `unzip -Z`, avoiding a separate runtime
dependency on a `zipinfo` executable. The
[ZipInfo manual](https://manpages.debian.org/trixie/unzip/zipinfo.1.en.html)
describes type information and notes that this mode can be omitted at build
time. A names-only listing does not establish whether an entry is a symlink.

The prototype must establish all of the following:

1. Names containing newlines, carriage returns, tabs, backslashes, and literal
   escape sequences cannot forge extra records or hide an unsafe path.
2. Entry names and types can be correlated without splitting names on spaces,
   assuming fixed username widths, or accepting archive comments as entries.
3. Inspection sees the effective names used by extraction, including tar PAX
   path overrides, GNU long names, ZIP Unicode path metadata, and ZIP central
   versus local header differences. Reject unsupported combinations.
4. Absolute names and traversal remain detectable even if a command normally
   strips or sanitizes them. Never enable an unsafe path option for extraction.
5. Locale and documented environment option variables cannot change parsing or
   extraction semantics. Set `LC_ALL=C` and neutralize those option variables in
   the archive command scope without changing the caller's environment.
6. Inspection errors retain their exit status. Avoid process-substitution loops
   or pipelines that conceal the failing producer; check complete output before
   consuming it.

Use format capabilities to select a supported inspection mode. For an
unrecognized implementation, fail with a specific diagnostic rather than fall
back to unchecked extraction. Check ZIP capabilities only when handling ZIP.
If the prototype cannot meet this contract with the allowed tools, record the
specific unsupported combination and resolve its support policy before
promoting the extractor. Do not introduce a shell implementation of the binary
archive formats or a new mandatory runtime dependency as an implicit fallback.

## 2 Implement shared validation

Keep `tools/lib/common/extract.sh` as the extraction facade. Add focused private
helpers for path normalization, entry validation, and format inspection. Split
format helpers into private files only if needed for readability, with explicit
loading from the facade.

Use one archive path policy for both installation layouts. Keep the bundle root
check as an additional constraint. Avoid coupling the common extractor to
release ownership records or changing `remote_ssh_relative_path_valid` for all
its existing callers. New state and loops must work under Bash 3.2 with
`set -euo pipefail`, without associative arrays or additional external parsers.

Diagnostics should identify the archive, rejected entry when representable,
and reason. Escape control characters in diagnostics. For an unsupported
backend, identify the missing inspection capability; for a listing failure,
preserve useful tool error output. Never continue with a partial manifest.

## 3 Isolate extraction and preserve publication

Keep the downloaded archive and inspection files outside a fresh `payload`
directory under `REMOTE_SSH_DOWNLOAD_DIR`. Require the destination to be new
and empty, with no pre-existing links or user files. A member named like the
archive or an inspection file must not overwrite installer inputs.

In `tools/lib/install-tool/download.sh`, retain this order:

1. Download the selected pinned asset into the private directory.
2. Verify its pinned checksum when available.
3. Inspect every archive entry and enforce the common policy and bundle root.
4. Create the payload destination and extract with the validated backend.
5. Return the payload directory to the existing candidate and staging logic.

Point `EXTRACT_DIR` at `payload` for every archive format; bundle root selection
continues relative to it. Derive that path in the parent after successful
staging, since assigning it only inside the existing download subshell would
lose the value. Raw executables continue using the download directory.

Keep failure propagation explicit and retain the download directory's cleanup
trap. A rejected archive must never reach candidate copying, release metadata
creation, or link switching. An extraction failure may leave partial files
only within the temporary payload until cleanup removes the private directory.

## 4 Add regression coverage

Add `dev/tests/test_archive_validation.py` for the inspection and policy matrix,
and `dev/tests/test_install_archives.py` for public installer containment and
rollback. Keep archive builders local to these tests or a focused helper;
extend `conftest.py` only for fixtures actually shared by existing suites.

| Test group | Required cases and assertions |
| --- | --- |
| Valid archives | Both tar suffixes and ZIP; flat and nested executable; leading `./`; explicit directory markers; spaces and quotes; ordinary long names. Installed binary runs and aliases resolve to the new release. |
| Unsafe paths | Absolute name, leading and nested `..`, repeated separators, backslash, and control characters. Include a valid executable before the invalid entry to prove the entire archive is checked first. |
| Entry types | Relative and absolute symlinks; directory symlink followed by a child; hard links in both orders; FIFO and device entries. Reject safe-looking internal links too. |
| Record ambiguity | Embedded newlines resembling valid entries, literal escapes, names containing link-description text, comments, duplicate files, and file/directory collisions. No parser confusion or shell evaluation. |
| Format metadata | PAX and GNU long-name paths; ZIP Unix symlink attributes, Unicode path extras, and header disagreement. Unsafe effective paths fail; supported valid metadata stays usable. |
| Inspection failures | Missing ZIP inspection capability, unsupported output, nonzero listing command after partial output, and corrupt or truncated data. No extraction command is invoked. |
| Extraction failures | Simulated extractor failure after writing part of the payload. No release or alias changes; temporary files are removed. |
| Integration controls | Valid bundle keeps its runtime; declared-root checks remain; valid raw executable and checksum-before-extraction behavior remain covered. |

For public installer failure cases, create an old executable with a primary
link and alias, plus sentinel files outside the payload. Assert nonzero exit,
unchanged sentinels and old file contents, unchanged link targets, successful
execution of the old binary, no new release, and cleanup of download and staging
directories. Add an extraction-call log to distinguish pre-extraction rejection
from protection supplied only by the host's tar or unzip.

Run shell cases through the existing `runtime_bash` fixture, including child
interpreter lookup. Test actual GNU and BSD implementations where available;
stubbed listings supplement these checks but do not prove portability. Record
unavailable combinations as unverified rather than claiming support from a
single host. ZIP fixture creation must not require the `zip` CLI. Include
environment-option overrides in real-command cases so a capability check cannot
pass under one set of options and extraction run under another.

Update the three archive staging tests in `test_install_tool_core.py` for the
payload destination. Preserve existing bundle, failure, and binary-publication
regressions. Tool definitions and asset selection should not need changes; if
implementation requires such a change, also update `test_tool_assets.py` as
required by the repository contract.

## Delivery and verification

Use three focused implementation changes, keeping relevant tests with each:

1. Prove inspection behavior and implement validation with adversarial fixtures.
2. Route ordinary and bundle archives through isolated extraction and add public
   installer rollback tests.
3. Document the accepted archive policy and supported inspection capabilities
   in `docs/tools.md`, then update the archive item in `docs/TODO.md` with results.

Run the focused archive and installer suites during implementation, then
`just smoke` once the changes are complete. Finish with `git diff --check` and
review the accepted-name restrictions, error paths, cleanup, and source loading.
Use local fixtures for routine tests; `just test-assets-live` requires an
explicit user request. Record any real package samples checked separately from
the synthetic fixture results, including the archive identity and extractor
implementation.

Acceptance checklist:

- [ ] All supported archive formats enforce one path and entry-type policy.
- [ ] Unsafe or uninspectable archives fail before any member is extracted.
- [ ] Extraction uses a fresh payload directory, separate from its inputs.
- [ ] Failure preserves the working executable, aliases, and external sentinels.
- [ ] Temporary download and staging directories are cleaned on failure.
- [ ] Valid ordinary archives, bundles, and raw assets still install correctly.
- [ ] Bash 3.2 and modern Bash pass; GNU/BSD and ZIP capability results are recorded.
- [ ] No new runtime dependency or unsafe fallback is introduced.
- [ ] Focused regressions and `just smoke` pass, with actual results recorded here.
- [ ] User documentation describes rejection rules and compatibility limits.
