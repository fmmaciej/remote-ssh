# Flyline R5 release promotion plan

Created: 2026-11-10
Status: completed; implementation and validation passed
Repository baseline: `06d0fee`
Scope: developer generator and promotion of the already published Flyline R5.

## Published input

- Repository: `fmmaciej/flyline`.
- Tag: `remote-ssh-v1.10.0-pr974.aae68bb4.r5`.
- Source commit: `d037c075ed30a61080873985ea2621d743ddfc64`.
- Artifact version: `1.10.0-pr974.aae68bb4.r5`.
- Asset: `flyline-1.10.0-pr974.aae68bb4.r5-aarch64-apple-darwin.tar.gz`.
- SHA-256: `38a7c65eb6e3c8c7458cdebea36607ae2e5577279b96ce2f6e2907b5ff9afaf3`.
- Member: `libflyline.dylib`.
- Library SHA-256: `ac989a041026f49df1d3b544290ee3e67b497a0d3f82fe4785cd3c106e431d57`.
- [Published prerelease](https://github.com/fmmaciej/flyline/releases/tag/remote-ssh-v1.10.0-pr974.aae68bb4.r5).
- Qualification: local macOS arm64, Homebrew Bash 5.3.20.

The six public attachments, their hashes, the archive members and source commit
were verified before this operation. Recheck the release input at generation.
Use the existing binary; this operation does not rebuild or modify the fork.

## Commit 1: artifact version override

Proposed title: `feat(generator): support artifact versions independent of release tags`.

1. Add `--artifact-version <version>` to `tools/generate-def.sh`.
2. Keep `--version` as an alias of `--tag`; preserve behavior without the new flag.
3. Apply the validated override to `VERSION` after tag normalization and before
   asset matching. Preserve `RELEASE_TAG` and the GitHub request target.
4. Reject a missing, empty or unsafe override before any API request. Accept
   a leading ASCII letter/digit followed by ASCII letters/digits or `_.:+-`.
5. Exercise the full CLI with offline release fixtures on system and PATH Bash:
   downstream tag, library member, exact asset/digest, tag alias, latest selector,
   ordinary tags and invalid arguments.
6. Document the flag and save this accepted plan in `dev/docs/`.

## Commit 2: promote the public R5 definition

Proposed title: `feat(flyline): enable installation from published R5 release`.

1. Generate a temporary definition from the published tag:

   ```bash
   tools/generate-def.sh fmmaciej/flyline \
     --tool flyline \
     --tag remote-ssh-v1.10.0-pr974.aae68bb4.r5 \
     --artifact-version 1.10.0-pr974.aae68bb4.r5 \
     --library-member \
       'flyline-1.10.0-pr974.aae68bb4.r5-aarch64-apple-darwin.tar.gz|libflyline.dylib'
   ```

2. Compare the generated field values with the prepared candidate, rather than
   requiring identical comments, quoting or field order. Promote only exact,
   complete values (no placeholder assets) to `tools/defs/flyline.sh`.
3. Update catalog snapshots and reset layout-specific state between definitions.
   Explicitly verify unsupported Flyline platforms and preserve executable
   musl-first selection independently of library selection.
4. Test the production definition's pinned source/tag/version, platform, member,
   checksum and exclusion from default profiles.
5. Update current install/shell/developer/release documentation and the current
   status of older plans. Preserve historical measurements and evidence files.
   The prepared candidate remains identified as historical; `tools/defs`
   becomes the authoritative install definition.
6. Run `just smoke` plus formatting/lint checks for changed tests.
7. Install the public archive using the production definition in an isolated
   prefix/configuration on qualified Bash. Verify check/list, fresh-shell
   activation and basic Vim operations, same-version reinstall, uninstall and
   rollback to Readline. Record exact binary hashes and results.
8. Keep Flyline opt-in and outside all install profiles. Carapace and other
   platform qualification remain separate work.

## Acceptance and delivery

- The new generator regression fails before the implementation and passes after.
- Existing generator selectors retain their meaning.
- The checked-in definition is generated and matches the verified R5 payload.
- The full smoke suite and isolated public-release lifecycle pass.
- Current documentation accurately distinguishes published R5 from historical
  local pilots and does not extend platform claims.
- Deliver the two coherent local commits after reviewing their diffs.
  Pushing the repository is a separate external action.

## Execution

Implementation and validation completed on 2026-11-10. Results follow below.

### Generator completion

- Regression before implementation: six downstream-library cases failed on
  Bash 3.2 and Bash 5.3.20 because `--artifact-version` was unknown.
- After implementation: generator tests **36 passed**; ShellCheck and Ruff passed.
- Full `just smoke`: **1585 passed, 56 skipped** (356.06 s); Bash syntax,
  ShellCheck, Ruff and mypy passed.
- The generator fetched the public R5 tag and emitted an exact semantic match
  to the prepared candidate across all eight manifest fields.

### Public release promotion

- Generator delivery commit: `b2b6ff3`.
- Generated `tools/defs/flyline.sh` directly from the public release API using
  the accepted artifact-version override; all candidate values match.
- Catalog and library tests: **85 passed** on system/PATH Bash.
- The [public input](flyline-release-promotion-evidence/release-input.json)
  confirms the tag still points at the pinned source and all six assets are uploaded.
- The [native lifecycle report](flyline-release-promotion-evidence/public-release-lifecycle.json)
  passes **22/22 checks** using the production definition, real public downloads,
  qualified Bash and isolated prefix/configuration.
- Checks include fresh active/disabled shells, Vim replacement/undo/redo/dot-repeat,
  Bash history, Tab completion, idempotent CLI install, forced immutable reinstall,
  checksum rejection preserving the active library, uninstall and Readline recovery.
- Reinstall semantics follow the existing contract: the public CLI skips a valid
  pinned installation; `tools/install-tool.sh flyline` forces reinstall.
- No native rebuild or runtime editor/installer behavior change was needed.
  Existing native performance and startup evidence remains historical and unchanged.
- The final full-project result is recorded under Completion below.

### Catalog-dependent uninstall test adaptation

The first full post-promotion smoke run reported **1581 passed, 6 failed,
56 skipped** (351.82 s). All failures were the old binary-only discovery fixture:
it used the real tool catalog, which now correctly contains the Flyline library.
The accepted F3 contract requires automatic discovery to reject an invalid
`.active` when library definitions exist.

The fixture now deliberately supplies only executable definitions for binary-only
discovery, while explicit selection continues against the real production catalog.
Six additional library-aware discovery controls verify nonzero exit and preservation
of the binary, active path, sentinel and expected-tools configuration.
The complete selection/path matrix is **18 passed** on both Bash builds.
No uninstall runtime logic was changed or relaxed. The final full smoke result follows below.

### Completion

- Final `just smoke`: **1593 passed, 56 skipped** in 347.94s (0:05:47).
  Bash syntax, ShellCheck, Ruff and mypy passed.
- Changed test files pass Ruff lint and formatting checks.
- Native public-release lifecycle: **22/22 passed**. The tested definition's
  fingerprint matches the generated, checked-in production manifest.
- [Validation summary](flyline-release-promotion-evidence/validation.json) and
  [full smoke log](flyline-release-promotion-evidence/full-smoke.log) retain the
  final result and source fingerprints. Current Markdown links resolve.
- The generator is delivered in `b2b6ff3`; the production definition, catalog
  adaptation, documentation and this close-out form the second planned commit,
  `feat(flyline): enable installation from published R5 release`.
- Flyline remains opt-in, outside all install profiles. Local macOS arm64 with
  Homebrew Bash 5.3.20 is the native support boundary of this verification.
  The existing R5 binary, runtime editor/uninstall code and prior evidence are unchanged.
- Repository push remains a separate external action.

Temporary public downloads, isolated installations and diagnostic attempts remain
in the ignored Kei runtime `00-system/var/cache/kei-tools/flyline-release-promotion/20261110-6qyf9vbs/`.
The durable plan, source and selected evidence were saved in this project under
the user's explicit instruction. Runtime contents are public code/artifacts and
synthetic test data; cleanup can remove this exact run after review.
