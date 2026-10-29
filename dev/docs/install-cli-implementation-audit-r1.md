# Installed management CLI — independent implementation audit

Date: 2026-10-28  
Round: **R1**  
Verdict: **ACCEPTED**  
Blocking findings: **none**

R0-B1 is closed by the narrowly scoped semantic test repair. R0-B2 is closed
by a completed, unfiltered `just smoke` on the frozen final R1 sources:
**exit 0; 928 passed, 58 skipped in 340.90s**. The earlier R0 failures and R1
timeout remain unsuccessful attempts in their original evidence. No additional
installer runtime defect was established.

## Independence, inputs and scope

I independently read `AGENTS.md`, the accepted original plan and plan audit,
the accepted batch-failure addendum and its audit, process and implementation
records, the completed R0 implementation audit, and the separately authored R1
repair plan. I reviewed the runtime, relevant tests, documentation, scoped
changes and retained R0 probe implementation/results. I then inspected the
completed R1 retry metadata, raw log, launcher and final implementation record.

The final R1 candidate retains all **12** R0 source entries byte-for-byte and
adds only `dev/tests/test_guide.py` to its manifest. Comparing its preserved
pre-repair snapshot with the final file shows changes only inside
`test_remote_ssh_guide_supports_post_install_section`; every byte before and
after that function is preserved. Its pre-repair SHA-256 matches the coordinator
checkpoint. All **178 protected files** match their pre-implementation hashes.
HEAD remains `39226a2d9074acf08279e7c3edde6a51cc2a629c`.

The R0 audit still equals its saved coordinator snapshot. Original plan/audit,
addendum/audit, repair plan and retained R0 evidence hashes also match my initial
R1 observations. The implementation record now separately records the timeout,
diagnostic and successful retry. [Independent final evidence review](install-cli-implementation-audit-r1-evidence/final-evidence-review.json).

## R0-B1 closure: exact semantics replace a quoting-style assumption

The repaired test extracts exactly one standalone `bash --rcfile` command,
passes that exact text to a fresh Bash with a local argument-capture function,
and asserts the exact NUL-separated arguments:

```text
--rcfile NUL <this checkout>/shell/rc.sh NUL -i NUL
```

This checks argument boundaries, the complete expected rcfile path and the
interactive flag without reproducing `%q`, using `eval`, or interpolating the
expected path into the script. The capture subprocess excludes `BASH_ENV` and
`ENV`. All previous heading, profile, `Commands` and old-marker assertions
remain; the new interactive marker must also be absent. The renderer and
unusual-path real-activation tests are unchanged.

My independent exact-case run passed **1 test in 0.29s**. I also executed the
actual repaired assertion in memory against controlled output variants, with
real Bash parsing on **Bash 3.2.57 and 5.3.20**. All **38 probes** behaved as
expected: equivalent valid quoting passed; missing `-i`, wrong or split rcfile
arguments, extra arguments, duplicate commands, unresolved markers and a missing
heading were rejected. These probes assess assertion strength; the retained
post-install tests exercise real rcfile activation under both Bash versions
and Zsh 5.9. [Probe source, fingerprints and results](install-cli-implementation-audit-r1-evidence/independent-checks.json),
[exact-case result](install-cli-implementation-audit-r1-evidence/exact-case-result.json),
[independent repair diff](install-cli-implementation-audit-r1-evidence/independent-repair.diff).

The implementer's final exact case passed **1/1**, and guide plus post-install
focused tests passed **26/26**. Whole-file Ruff check, scoped formatting of the
repaired function and diff check passed. Whole-file formatter differences remain
in two pre-existing unrelated cases. I compared baseline/final formatter diff
hunks and found them identical after removing the command summary; neither
touches the repaired case. Reversing only the final `capture_env` line wrapping
reconstructs the retained initial R1 hash. The initial snapshot is explicitly
invalidated and retained separately from `r1/final/`; no whole-file format pass
is claimed.

## R0-B2 closure: complete verification, with failed attempts preserved

The [completed retry result](install-cli-coordinator-evidence/r1-smoke-retry-result.json)
records exactly `["just", "smoke"]`, exit **0**, no timeout, outside-sandbox
execution and `start_new_session=True`. The
[launcher](install-cli-coordinator-evidence/retry-r1-smoke.py) uses project
Python, stdin `DEVNULL`, `UV_OFFLINE=1`, `PYTHONUNBUFFERED=1`, and removes
`PYTEST_ADDOPTS`, `BASH_ENV`, `ENV` and `REMOTE_ENV_DIR`. It supplies no pytest
selectors or additional skip/xfail settings. The unchanged smoke recipe invokes
the complete suite. Its [raw output](install-cli-coordinator-evidence/r1-smoke-retry.log)
shows successful syntax, ShellCheck, Ruff and mypy checks followed by
**928 passed, 58 skipped in 340.90s**. The total remains 986 cases, with the same
58 skips as R0 and all four formerly failing cases now passing.

I independently compared every retry before/after source fingerprint with the
frozen manifest and current files: all **13** match. All **178** protected hashes
also match after completion, and my final `git diff --check` returned 0.

The original R0 log still reports **4 failed, 924 passed, 58 skipped**, and its
result JSON still records exit 1. The R1 1200-second timeout remains separately
recorded with its partial log and subsequent termination status 143; it is not
counted as a pass. The earlier five-case tmux/welcome recheck passed, as did the
six-case Atuin diagnostic before retry. Those focused results do not replace
the complete passing run.

No precise single cause of the prior welcome PTY behavior or R1 hang is
established. The retry changed launcher interpreter/stdin/buffering settings;
the available evidence does not isolate one as causal. No tmux, welcome, Atuin,
runtime test or fixture repair was used to obtain the pass.

## Retained implementation contracts

The unchanged runtime was independently assessed against the accepted plan and
addendum; the R0 audit's bounded probes remain relevant retained evidence.

| Contract | R1 assessment |
| --- | --- |
| Ownership and early preflight | Physical absolute source; exact direct-link ownership; files, directories, hard links, broken/foreign/equivalent links are collisions. Preflight precedes confirmation, tools, preparation and expected-tools writes. Existing tests observe preservation and absence of calls/mutations. |
| Safe publication | After confirmation, publication creates/canonicalizes the bin directory, rechecks ownership and uses non-overwriting `ln -s SOURCE BIN_DIR/`, checking status and exact target. Controlled final-entry races preserve entries without nested links. |
| Failure propagation | One full-array batch call remains. Explicit mkdir and per-tool guards stop first/middle failures even in a conditional context. Completed tools and the published CLI survive; later tools, configuration, expected-tools writes and success footer do not follow failure. |
| Paths and bootstrap | Relative destination is anchored to caller PWD; effective checkout override is retained. Portable one-link readlink resolution handles relative/chained paths with physical directories and a 40-link bound. Dispatcher does not load the rcfile. |
| Copyable guidance | Full-path guide/session commands work without PATH. Dedicated `%q` interactive rendering, literal `$PATH` and directory-aware PATH hints are retained. Existing unusual-path tests execute real activation under Bash and Zsh. |
| Activation boundary and runme | Only the management helper is newly published; environment activation remains explicit. Real runme clone/update fixtures retain dispatcher/install routing. Separate ordinary shells check lookup, no marker/prompt/alias/function/helper leakage and unchanged startup files. |
| Lifecycle and scope | Uninstall/prune preserve CLI and checkout; no tool definition or expected-tools entry is added for management CLI. Runtime runme/update/lifecycle sources, shared fixtures, assets and unrelated welcome changes remain preserved. |

## Fingerprints and limits

- Accepted plan: `503e5fb19da5ff45dc3484cc8562dc8169bb7fb6be24e2c712d4f61b9ee38339`.
- Accepted addendum: `ceddfb157e3bb6709d08b09b3d01f6eae1d1c205d7f9c3505749e3e6302bd09f`.
- R1 repair plan: `afc10272f6d7f4567a437d234849d9a5011bfc04b05f61009b9355b9dfcbcb6d`.
- Final 13-source manifest: `d66ef774b5518865f9576e8a3c0b10808743f7d0ddb0b155aedba37bbc3c55f3`.
- Repaired guide test: `8030eaed285b05fc2e4c8833b3573df4f21b3ac75b356d24381c4fb4e609b2d8`.

The linked final evidence review fingerprints the completed record, retry
launcher/log/result and failed-attempt evidence. Publication-race execution
evidence is local macOS/BSD `ln`; no Linux execution is claimed. Git transport
and asset downloads in installation tests use observable local boundaries;
this is not live release-asset validation. Parent-directory replacement races
remain outside the accepted guarantee.

I wrote only this report and its dedicated R1 audit evidence. I did not modify
implementation sources/tests/records, previous reports or accepted plans; run
another complete suite; access the network; install into the real HOME; stage,
commit, push or delegate to another agent. No further repair round is required
for the audited R1 candidate.
