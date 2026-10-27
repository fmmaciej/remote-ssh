# Config loader implementation audit

Verdict: **ACCEPTED (implementation R0)**, 2026-10-27.

No blocking correctness, scope, verification, or measurement findings remain.
Repair rounds R1-R3 were not needed; no repair plan was requested.

This report reviews runtime implementation. The separate
[plan audit](config-loader-plan-audit.md) records acceptance of the
[implementation plan](config-loader-implementation-plan.md); that acceptance
does not establish implementation correctness or performance.

## Review criteria

- Preserve literal parser behavior, first-`=` splitting, trimming and outer
  quotes, allowlisting, last duplicate wins, empty values, and the final line
  without LF.
- Preserve set-but-empty environment precedence, absence without default
  exports, disabled loading, reload, manual overrides, and canonical marker
  ownership and inheritance.
- Preserve compatibility lookups and `remote-ssh guide config` attribution.
- Work in Bash 3.2 and modern Bash with `set -euo pipefail`, including the
  invocation-local array output contract and failure paths.
- Read config once per load and remove repeated per-line/per-key subshell work,
  without a global snapshot, persistent cache, or new runtime dependencies.
- Review meaningful tests and independently probe uncovered risks. Confirm a
  successful full `just smoke` for the final reviewed version without needlessly
  rerunning an already evidenced identical check.
- Verify baseline, Stage A, and Stage B measurements of the loader and full PTY
  startup with missing/populated config, matched environments, interpreter
  paths, and raw execution records.

## Review history

| Round | Verdict | Blocking findings | Action |
| --- | --- | --- | --- |
| Implementation R0 | ACCEPTED | None | Implementation and evidence accepted; coordinator informed. |

The review includes the final handoff and completed execution record. Runtime
and test fingerprints were checked again after that handoff; they match the
version used for the code review and independent probes. The maximum of three
repair/review rounds after R0 did not need to be used.

## Reviewed version

Baseline commit: `c41cbc4820594de95e2035cfc5ab896e16db9e70`.

| File | Reviewed SHA-256 |
| --- | --- |
| `shell/config/parse.sh` | `144974b02abba3ed2cabf50fd22474380fba862de0cefb09a99646bd5b2da9cf` |
| `shell/config/load.sh` | `b34d057eb296bee51ff7d60f842a398182c52718a21e55243d60fedc09857bf3` |
| `shell/config/markers.sh` | `7591de066e72d9674f32677f32258ddafca53d149d72a541a3760ba9099dd0af` |
| `dev/tests/test_config.py` | `d8d6f85da375c41dca5a87a9aef5c31dfe0eea7737b7dbd663b2d29636fc953a` |
| `dev/tests/test_guide.py` | `d1fe47c4973a78812aa4f6ff56558d33311216dc171bea58a88664fcdf6e83d2` |

## Code assessment

- `parse.sh` builds the allowlist arrays once per invocation, keeps presence
  separate from empty content, and reads the config through one redirected
  physical-line loop. Trimming, first-`=` splitting, quote removal, unknown-line
  handling, and final lines without LF preserve the existing parser. The loop
  contains no command/process substitution or external parser.
- `load.sh` owns all snapshot arrays/count locally, skips path resolution when
  disabled, and applies values in the existing entry order. The precedence,
  clear-on-removal, manual-override, and equality-based ownership branches match
  the previous loader. Snapshot data does not survive the call.
- `markers.sh` constructs the same canonical names in the current shell,
  preserves presence checks for empty values, exports both markers when marking
  ownership, and preserves helper stdout/status interfaces. Hot marker work no
  longer invokes command substitutions.
- Shared entries, path rules, the library and env call sites, and guide runtime
  code are unchanged. Existing lookup wrappers remain compatible with the guide.
  No dependencies, lasting caches, or unrelated runtime refactors were added.
- The new subprocess tests explicitly select Bash 3.2 and 5.3, use strict mode,
  cover exported child provenance, and complement the existing welcome/guide
  integration coverage. Separating direct loader tests into `test_config.py`
  instead of extending the larger welcome test module is a reasonable bounded
  organizational adjustment to the plan.

## Independent probes

Separate temporary trees were created from HEAD and the reviewed runtime, then
the same probes were run under `/bin/bash` 3.2.57 and
`/opt/homebrew/bin/bash` 5.3.20 with `set -euo pipefail`.

1. Differential parser probe: 31 configurations covering empty/space/tab values,
   repeated `=`, delimiters, comments, backslashes, matched/unmatched quotes,
   quoted interior whitespace, CRLF/no final LF, dollar/backtick syntax, globs,
   inline control whitespace, Unicode, and prior duplicates. Raw outputs/status
   matched HEAD in both interpreters; the command-execution sentinel was absent.
2. Differential lifecycle probe: eight successive load/change/manual-override/
   disable/re-enable/removal/incomplete-marker states. All setting presence,
   values, canonical marker presence/values, and ownership decisions matched
   HEAD in both interpreters.
3. Dynamic-scope probe: a caller's generic `key`, `value`, `source_var`, and
   `loaded_var` locals survived a load. Preexisting scalar globals using the
   private snapshot output names also survived, confirming that the actual
   loader declarations contain the snapshot in their own scope.
4. Directory-path failure probe: both old and new loaders survived. Old Bash
   5.3 direct strict-mode raw lookup aborted on an uninitialized `line`; the new
   raw lookup returned absent and the caller survived, without diagnostics, in
   both interpreters. This is the small documented failure-path correction in
   the execution record, consistent with the plan's initialized/guarded benign
   read failure requirement. It does not alter ordinary config syntax or
   precedence.

No runtime files or implementation tests were edited by the auditor.

## Final verification evidence

The final [execution record](config-loader-implementation-record.md) and
[captured smoke output](config-loader-measurements/smoke-stage-b.txt) were
inspected. `just smoke` exited zero for the reviewed Stage B version: syntax,
shellcheck, ruff, and mypy passed; pytest reported **751 passed, 57 skipped** in
285.39 seconds. The focused config runs passed all 50 cases after Stage A and
again after Stage B, using both actual Bash interpreter paths. Bash 3.2 syntax,
targeted test/harness lint, and documentation link checks are also recorded.

The full smoke run was not repeated: its result applies to the unchanged final
runtime/tests, and separate differential/failure/scope probes addressed risks
independently. A final auditor `git diff --check` also passed. The live asset
checker was not run.

## Measurement evidence

The source of the temporary harness and all 12 baseline/Stage A/Stage B raw JSON
records in [config-loader-measurements](config-loader-measurements/) were
inspected. An independent consistency check verified:

- Every harness and fixture SHA matches the frozen files; each embedded runtime
  source matches its SHA.
- Baseline runtime matches HEAD. Stage A has the reviewed parser/loader with
  HEAD markers. Stage B matches all three reviewed runtime files.
- Each loader result has seven measured samples and each PTY result twenty;
  medians and ranges agree with the raw samples. All recorded PTY samples have a
  ready marker, status zero, and no timeout.
- The PTY harness writes each fixture into the HOME/XDG returned by the existing
  isolated environment helper before timing, selects the absolute interpreter
  and matching env-Bash shim, and uses the same optional-tool path and disabled
  network/user-module settings across checkpoints.

Representative matched medians, in milliseconds:

| Measurement | Bash | Baseline | Stage A | Stage B |
| --- | --- | ---: | ---: | ---: |
| Loader, all nine keys | 3.2 | 361.96 | 34.17 | 8.89 |
| Loader, all nine keys | 5.3 | 341.24 | 47.07 | 14.39 |
| PTY min, all nine keys | 3.2 | 544.64 | 199.94 | 147.30 |
| PTY min, all nine keys | 5.3 | 501.22 | 175.16 | 164.66 |
| PTY welcome, all nine keys | 3.2 | 669.69 | 343.82 | 331.54 |
| PTY welcome, all nine keys | 5.3 | 652.43 | 334.05 | 327.97 |

Final missing/disabled loader medians are also lower than their matching
baseline; all final missing-config PTY medians are lower. These are local
diagnostics with optional user tools absent from PATH, not guaranteed SSH login
times or a cross-machine performance promise.
