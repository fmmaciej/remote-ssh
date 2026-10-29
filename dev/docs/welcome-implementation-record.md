# Welcome implementation record

Created: 2026-10-28
Baseline: `39226a2d9074acf08279e7c3edde6a51cc2a629c`
Current status: **R1 ACCEPTED by the independent implementation auditor.**

Back: [Developer tooling](../README.md)
Related: [Accepted plan](welcome-implementation-plan.md),
[independent plan audit](welcome-plan-audit.md),
[measurement sources and evidence](welcome-measurements/README.md)

The user explicitly approved implementation on 2026-10-28 after independent
plan acceptance R1. The approved plan SHA-256 is
`e55d02e7b374500c25d7418a4939d5ca55c5add81861c08bdf47823e033fb6d6`.
This is execution approval for the complete plan, its correctness checks and
measurements. It does not authorize commits, pushes, live asset tests, or new
configuration keys. The question about section configuration was informational.

The implementer started from the pinned baseline with only the two untracked
plan/audit documents. Their contents and earlier config-loader evidence are
preserved. Initial independent implementation audit is R0; concrete repairs
require a separate repair planner, with at most R1 through R3.

## Checkpoints

- Baseline runtime materialized with `git archive` of the full SHA in
  `/private/tmp/remote-ssh-welcome-baseline-39226a2` before runtime edits.
- Actual interpreters: `/bin/bash` 3.2.57 and `/opt/homebrew/bin/bash` 5.3.20.
- Frozen harness SHA-256:
  `6ae3e4a291a06e9a63b233d054584da3c6b75a45a09cd586eaa8d13536b6dfcc`;
  frozen fixture SHA-256:
  `93ea13874f28c0f49b9a78360f26002bf8dd7cdce60162245e50d49f5c6c6f71`.
- Before runtime edits: 12 complete expected screens, 276 successful baseline
  samples (3 warmups + 20 measured per principal/control cell), and 72
  compatibility cases retained in the evidence directory.
- Renderer extraction with external execution: all 72 compatibility cases
  match baseline stdout/stderr/status byte for byte; existing focused welcome
  tests pass (36 tests). Source fingerprint and runtime diff are retained as
  `extracted-external-source.json` and `extracted-external-runtime.patch`.
- Worker prototype: all 72 baseline compatibility captures still match exactly;
  the original 36 focused welcome tests pass. The new behavior coverage lives
  in a separate `test_welcome_bundled.py` to keep the existing configuration,
  provider and status tests readable.
- R0 pre-measurement focused verification outside the macOS sandbox:
  **125 passed, 1 skipped** (Bash 3.2 does not expose `BASHOPTS`). Root retained
  the full output and seven runtime file hashes in
  [focused-root-unsandboxed.log](welcome-measurements/focused-root-unsandboxed.log).
  The sandbox denies `/dev/tty` even to a child with a controlling PTY, so that
  permission boundary was removed for the real terminal tests and final paired
  timings. The preliminary baseline samples are retained as preliminary data,
  separately from the final matched outside-sandbox comparison.
- Final runtime R0 frozen in
  `/private/tmp/remote-ssh-welcome-candidate-r0` before the final paired samples.
  Its source/mode aggregate is
  `f9fc66f5936a0aec6f31a46e60bfba272c9cae9702310cde414cbb95659d723b`;
  the snapshot equals the working runtime. See
  [candidate-r0-frozen.json](welcome-measurements/candidate-r0-frozen.json) for
  the full per-file hashes, base commit, tracked diff and new source contents.
- Untimed execution trace on both actual interpreters: the normal group starts
  one worker and then the external user module; the forced external route starts
  the three wrappers and then the user module. All four runs return zero and
  match the complete frozen healthy screen, with one added user line. Full
  stdout and Bash xtrace stderr are retained alongside
  [execution-trace.json](welcome-measurements/execution-trace.json). Timed runs
  keep a direct `bash` symlink; the untimed trace uses a documented executable
  logging probe that immediately execs the selected real interpreter.
  [Trace review](welcome-measurements/trace-review.json) confirms one actual
  welcome-library load, three renderer captures/dispatches and three output-file
  cleanup calls inside each worker, with hashes of both raw traces.

## Rejected first paired attempt

The first outside-sandbox paired run stopped on its full-screen assertion after
139 successful records, at the first candidate Bash 3.2 actionable PTY warmup.
The baseline said `git config missing`; the candidate said `git config invalid`.
This attempt is rejected as a performance comparison. Its
[partial JSONL](welcome-measurements/paired-r0-attempt-1.jsonl) and
[complete failure log](welcome-measurements/paired-r0-attempt-1.log) are retained.

Read-only diagnosis found that the candidate's initial `copytree` materialization
included the workspace's pre-existing ignored `dots/git/user.local`, while the
pinned `git archive` baseline contained no such file. The full rc Git identity
hook correctly consumed those different inputs. Isolated welcome used the
exported status instead. The comparison also exposed a harmless source-mode
difference in `tools/defs/atuin.sh` (baseline 0644, candidate 0600; identical
content). Outside the seven intended runtime files, these were the only source
manifest differences. No user configuration or runtime source was edited to
hide the mismatch. The independent auditor and separate repair planner received
this evidence before any materialization repair or new timing series.

The rejected sample's full screen is present in the assertion log, and it had
already passed return-code, timeout and marker checks. Harness R0 raised before
writing that sample's timing metadata; this evidence limitation is explicit.
No result from the partial attempt establishes measured performance acceptance.

## R1 repair and final source

The independent R0 audit was **NOT ACCEPTED**, with W0 (asymmetric measurement
materialization) and W1 (incomplete required library accepted by preflight).
The separate [repair plan](welcome-repair-plan.md), SHA-256
`65386aee5fddc3170b6209f6e067d72e288b614ba038e3943e17c7cfdfa75857`,
authorizes one combined R1. It does not reset the R1–R3 repair limit.

W1 was reproduced before the worker edit: all eight new regression cases failed
on R0, covering a missing `hw.sh`, a missing low-level helper while renderers
still exist, and one parent recovery in quiet/debug mode on each interpreter.
The worker now verifies the fixed required welcome/update library files and
declared helper surface before any capture. It still loads the library once,
does not invoke providers for preflight, and leaves `status.lib.sh` lazy inside
the first renderer. Only worker bytes changed from the seven-file R0 snapshot.
The focused post-repair set passed **30 tests**, including normal worker routing,
pre-display fallback, renderer exit 125 and post-display failure containment.
See [red](welcome-measurements/r1-w1-red.log) and
[green](welcome-measurements/r1-w1-green.log) output.

W0 was repaired through a new materialization, leaving the workspace's private
configuration and file modes untouched. The retained
[materializer](welcome-measurements/materialize-r1.py) creates fresh baseline
and candidate trees from the full pinned Git archive, then overlays only the
seven reviewed welcome source paths with explicit modes. Its R0 red gate names
the two unauthorized differences; its R1 green gate verifies exactly the seven
authorized changes across complete path/kind/link/byte/mode manifests.
[candidate-r1-frozen.json](welcome-measurements/candidate-r1-frozen.json)
contains those complete manifests and the unchanged frozen-input hashes.

The final trees are `/private/tmp/remote-ssh-welcome-baseline-r1` and
`/private/tmp/remote-ssh-welcome-candidate-r1`. Their runtime aggregates are
`366a4aaab30a5bc7864c91680e953f9509aaafc31b0f8bab5fb037dff825c066` and
`0703139284173f0358ac13431875f23b7035fbfcb1b83b104fdada6ba1c9e58b`.
The [complete seven-file diff](welcome-measurements/r1-complete-runtime.patch)
includes the two new files. The
[runtime/test freeze](welcome-measurements/r1-runtime-tests-final-freeze.json)
is the final R1 source for checks, timings and independent re-audit.

The unchanged frozen `sample()` rechecked the previously rejected Bash 3.2
actionable PTY cell on both new trees: both complete screens match the same
golden output and hash. These two
[diagnostic samples](welcome-measurements/r1-former-failure-diagnostic.json)
are excluded from principal results. The 139 old records and rejected-sample
limitations remain separately accounted for in
[r1-rejected-r0-accounting.json](welcome-measurements/r1-rejected-r0-accounting.json).

The final-source [R1 trace](welcome-measurements/r1-trace/execution-trace.json)
and [trace review](welcome-measurements/r1-trace/trace-review.json) retain the
one-worker/one-library-load/three-capture boundary on both interpreters and
actual external wrapper/user execution in fallback. Its driver changes only
the candidate path and uses byte-identical copies of frozen inputs in a separate
evidence directory, preserving every R0 trace. Explicit syntax checks passed
for all seven files with each interpreter (14 checks); shellcheck passed for
the same seven files. The full results are in
[r1-explicit-syntax-shellcheck.json](welcome-measurements/r1-explicit-syntax-shellcheck.json).

The independent [R1 recheck](welcome-implementation-audit.md#r1-recheck-before-timings)
closed W1: both original missing-file probes return 125 with empty stdout, and
all four real-provider parent recovery comparisons match the external reference.
Its 19 independent behavior comparisons match pinned baseline; the coordinator's
outside-sandbox controlling-PTY probes pass 4/4 on baseline and 4/4 on R1. The
auditor independently confirmed the clean complete manifests and original frozen
input hashes. At this pre-timing checkpoint, W0's measurement requirement and
overall acceptance still awaited the final smoke and full paired series.

## Verification launch conditions

Outside-sandbox access is required for a real `/dev/tty` test. The verification
process itself must also have no inherited controlling terminal: ordinary
subprocess tests intentionally capture stdout, while dedicated PTY tests create
their own terminal. This preserves both transport cases without changing runtime
or existing tests.

Two earlier full-suite launches do not establish final smoke acceptance. An
auxiliary run on the changing tree was interrupted while a Bash 3.2 history
test with welcome disabled was still running (511 passed, 57 skipped at
interruption). Its [partial log](welcome-measurements/smoke-r0-auxiliary-interrupted.log)
is retained as auxiliary evidence. A subsequent run inherited a controlling TTY:
welcome correctly displayed there, and twelve existing stdout-capture assertions
failed (850 passed, 58 skipped). The retained
[attempt record](welcome-measurements/smoke-r1-inherited-tty-attempt.json)
explicitly warns that the tool-returned output was truncated; it is not a
complete raw log or a passing verification.

ROOT's one-off [verification driver](welcome-measurements/run-verified-checks.py)
runs the fixed commands with `start_new_session=True`, `/dev/null` stdin, a
600-second bound, and complete raw file logging plus SHA-256 metadata. The three
problematic launch cases passed its initial targeted probe.

The final detached **`just smoke` passed: 862 passed, 58 skipped, exit 0**
(pytest 310.60 seconds). It includes the complete welcome suites on both actual
interpreters and the repository's syntax, shellcheck, Ruff and mypy checks.
The [complete raw log](welcome-measurements/r1-detached-smoke.log) has SHA-256
`8d62489bc65b1e9e804bf2e967cb329aa58401e6258c7537b351cd07cfabb199`;
its [metadata](welcome-measurements/r1-detached-smoke.metadata.json) records the
command, detached stdin/session conditions, driver hash and runtime/test-freeze
hash. The complete paired comparison is reported below; smoke success establishes
verification, separately from measured performance.

## Existing limits preserved

The 72 baseline comparisons include ordinary and direct strict calls, private
and exported banner/color/column/provider state, empty/nonempty `BASH_ENV`, and
exported shell options on both actual interpreters. Bash 3.2's pre-existing
empty issue-array `nounset` diagnostic in strict actionable runs is preserved;
the optimization does not claim to repair it. The runner still has no timeout
for a slow module. Module temporary-file failure skips that module, and an issue
temporary-file failure may omit `next` while retaining status text.

## Decisions and results

The final R1 paired run completed with **exit 0 and 920/920 successful complete
output assertions**, zero timeouts and zero nonzero sample return codes. It
contains 736 principal records and 184 control records, including 120 discarded
warmups and 800 measured samples. Every principal cell has two paired batches;
each tree/cell/batch has three warmups and twenty measured samples in alternating
order. Controls have one paired batch. All HOME/config/tool/cache setup occurs
before the timer. The fixed update-cache bytes remained fresh and unchanged.

The [complete raw samples](welcome-measurements/paired-r1.jsonl),
[metadata](welcome-measurements/paired-r1.metadata.json),
[process log](welcome-measurements/paired-r1.log) and
[full statistical summary](welcome-measurements/paired-r1-summary.json) are
retained. The summary reports median, p95, minimum, maximum and absolute/percentage
change for both ready and total time in every cell. The
[before](welcome-measurements/r1-checkpoint-before-timings.json) and
[after](welcome-measurements/r1-checkpoint-after-timings.json) timing checkpoints confirm the
same runtime/modes, complete trees and original frozen measurement inputs.
The coordinator's [final source check](welcome-measurements/root-final-source-check.json)
also verifies all ten frozen runtime/test/conftest hashes and modes, the exact
successful `just smoke` command and raw-log/driver/freeze hashes. Final tracked
whitespace validation passes. The
[documentation/source check](welcome-measurements/final-doc-source-checks.json)
also checks owned new untracked source files and local Markdown links while
preserving raw transcript bytes.

All figures below are milliseconds, rounded to two decimals; changes are
calculated from the unrounded medians. These are local measurements on the
recorded host and fixtures, without a numerical promise for other machines.

### Isolated welcome

This workload includes a fresh noninteractive process, library loading, worker,
capture/replay and actual status work, with no controlling terminal.

| Batch | Bash | Fixture | Baseline median | R1 median | Change ms (%) | p95 baseline → R1 |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| 1 | 3.2 | healthy | 210.60 | 194.82 | −15.78 (−7.49%) | 233.16 → 217.89 |
| 1 | 3.2 | actionable | 204.09 | 185.49 | −18.61 (−9.12%) | 228.57 → 225.97 |
| 1 | 5.3 | healthy | 231.85 | 203.90 | −27.95 (−12.05%) | 249.99 → 222.26 |
| 1 | 5.3 | actionable | 229.57 | 200.31 | −29.26 (−12.74%) | 250.79 → 215.20 |
| 2 | 3.2 | healthy | 214.93 | 195.57 | −19.36 (−9.01%) | 246.51 → 210.62 |
| 2 | 3.2 | actionable | 208.03 | 186.71 | −21.33 (−10.25%) | 247.38 → 205.24 |
| 2 | 5.3 | healthy | 218.73 | 193.50 | −25.23 (−11.53%) | 250.89 → 235.12 |
| 2 | 5.3 | actionable | 217.05 | 192.34 | −24.71 (−11.38%) | 237.30 → 207.98 |

### Full PTY first-command-ready

This is `remote-ssh-default-preseed` with fresh HOME and its existing once-per-HOME
state preseed. The marker follows rc execution and the complete welcome panel;
it does not measure PS1 rendering or SSH transport.

| Batch | Bash | Fixture | Baseline median | R1 median | Change ms (%) | p95 baseline → R1 |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| 1 | 3.2 | healthy | 323.78 | 310.53 | −13.25 (−4.09%) | 348.51 → 323.89 |
| 1 | 3.2 | actionable | 325.69 | 287.17 | −38.52 (−11.83%) | 383.12 → 317.32 |
| 1 | 5.3 | healthy | 319.40 | 296.67 | −22.74 (−7.12%) | 356.12 → 339.97 |
| 1 | 5.3 | actionable | 324.15 | 293.81 | −30.35 (−9.36%) | 378.70 → 324.83 |
| 2 | 3.2 | healthy | 327.39 | 301.82 | −25.57 (−7.81%) | 378.80 → 318.60 |
| 2 | 3.2 | actionable | 312.75 | 300.75 | −11.99 (−3.83%) | 331.51 → 346.10 |
| 2 | 5.3 | healthy | 331.17 | 314.47 | −16.70 (−5.04%) | 383.78 → 368.16 |
| 2 | 5.3 | actionable | 323.78 | 296.42 | −27.36 (−8.45%) | 379.04 → 329.89 |

All sixteen principal medians are lower: isolated welcome by 7.49–12.74%, and
full PTY ready time by 3.83–11.83% (11.99–38.52 ms). Total-time medians also
decrease in every principal cell; they remain a secondary diagnostic.

### Controls and tail variation

| Bash | Control | Baseline median | R1 median | Change ms (%) | p95 baseline → R1 |
| --- | --- | ---: | ---: | ---: | ---: |
| 3.2 | bash-baseline | 11.65 | 11.94 | +0.28 (+2.43%) | 12.93 → 13.21 |
| 3.2 | remote-ssh-min | 95.99 | 96.81 | +0.83 (+0.86%) | 106.70 → 108.18 |
| 5.3 | bash-baseline | 16.42 | 16.65 | +0.24 (+1.44%) | 17.27 → 18.12 |
| 5.3 | remote-ssh-min | 96.23 | 96.73 | +0.50 (+0.52%) | 113.11 → 103.50 |

The small positive control deltas also occur in `bash-baseline`, which does not
source repository runtime. Baseline/candidate control ranges overlap, with
spreads larger than these median differences; all min/max values are preserved
in the linked summary. The independent auditor also reviewed pairwise effects
and IQRs, finding no reproducible control regression beyond the observed spread.

Median improvement does not imply that every launch is faster. Bash 3.2
actionable PTY batch 2 has a higher candidate p95 (346.10 versus 331.51 ms), and
some candidate maxima are higher despite the lower medians. The raw output and
all samples are retained, including those tails. No cells or outliers were
removed. The auditor compared the same cell's two batches and accepted this
retained tail caveat without finding a repeatable tail regression.

**Final independent verdict: R1 ACCEPTED.** W0 and W1 are closed; R2 is not
required. The [audit report](welcome-implementation-audit.md) and
[final evidence review](welcome-audit-evidence/r1-final-evidence-review.json)
independently verify all 920 raw records, complete screens and statuses,
recomputed statistics, final source/modes, trace and full smoke log. User
approval, implementation verification, measured median improvement and final
independent acceptance are separately recorded. Runtime and tests remained
frozen through this verdict. No staging, commit, push or live asset check occurred.
