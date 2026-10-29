# Welcome Implementation Audit

Current verdict: **R1 ACCEPTED — compatibility, final verification, and measured
performance meet the accepted plan.** W0 and W1 are closed. No R2 is required.
The partial R0 paired run remains rejected and separate from accepted evidence.

Date: 2026-10-28  
Auditor role: fresh implementation auditor, independent of the plan auditor,
repair planner, and implementer  
Accepted plan: R1, SHA-256
`e55d02e7b374500c25d7418a4939d5ca55c5add81861c08bdf47823e033fb6d6`  
Pinned baseline: `39226a2d9074acf08279e7c3edde6a51cc2a629c`

Back: [Developer tooling](../README.md)  
Plan: [Welcome implementation plan](welcome-implementation-plan.md)

## Scope and independence

This report owns only this document and `welcome-audit-evidence/`. Runtime,
tests, implementation evidence, the accepted plan, and the config-loader
history are read-only to the auditor. No staging, commit, push, network check,
live asset check, or runtime edit is authorized by this audit. Temporary copies
are used for fault injection and pinned-baseline probes.

The initial criteria below were established from the accepted plan, current
welcome contract, pinned sources, and existing tests before receiving an
implementation report. The previous plan audit is separate evidence and does
not substitute for this audit. A passing suite is supporting evidence, not a
proof of equivalence.

## Independent acceptance criteria

1. Exact screen bytes and order remain equivalent for populated healthy and
   actionable fixtures: banners and color, host/update/tools/scripts/hardware/
   software, blank lines, and one final `next` selected from current allowed
   issues. Actual provider and inventory APIs must execute.
2. Fresh executable-state boundaries survive the worker: private caller state
   is not imported, each renderer is captured separately, status loading does
   not leak to sibling renderers, and user modules keep their actual external
   executable and interpreter. Mutations, failure, and `exit` do not reach the
   next renderer, user module, or caller.
3. Qualification accepts only exact registered, regular executable nonsymlink
   wrappers with exact case-sensitive bytes, final LF, no NUL, and bounded
   reads. It is bound to the physical loaded tree. Any ambiguous member selects
   external execution for the whole already-discovered group.
4. Nonempty `BASH_ENV` and exported option variables select the old external
   route. That route preserves its old `nullglob` iteration scope and per-module
   `set +e`, while preserving caller options and export attributes. Unset and
   empty `BASH_ENV`, and ordinary unexported options, are distinguished.
5. Capture/replay preserves `/dev/null` module stdin, `/dev/tty` display with
   stdout fallback, text with spaces/backslashes/CR/blank lines and a final
   unterminated line, stderr quiet/debug behavior, continuation, temporary-file
   cleanup, fresh issues, and standalone wrappers including renamed symlinks.
6. Reserved preflight status is emitted only before any display. Renderer exit
   with that value cannot cause replay, and an unexpected post-display worker
   failure still permits user modules and the caller's next command.
7. Bash 3.2 and 5.3 ordinary and direct strict-mode calls are verified without
   conditional wrappers that mask `errexit`; existing unsupported modes are
   compared to baseline rather than silently expanded into new requirements.
8. Final source/mode fingerprints, smoke log, focused tests, syntax checks,
   trace, and all raw samples refer to the reviewed final candidate. The trace
   proves one worker and executable fallback/user paths.
9. A frozen single harness and fixed `dev/bench` copy measure pinned baseline
   and candidate with identical effective settings and fresh isolated HOME.
   Every populated principal cell on both Bash versions must show repeatably
   lower isolated and full PTY first-command-ready medians in two paired
   batches. Complete panel output, return codes, no truncation, all samples,
   p95/spread, and controls are examined. This is not a PS1 measurement.

## Baseline probes and observations

The independent source
[`probe_baseline.py`](welcome-audit-evidence/probe_baseline.py) materializes the
full pinned commit with `git archive`, creates fresh isolated HOME and PATH for
each actual interpreter, and runs no timing loops. Its
[complete results](welcome-audit-evidence/baseline-probes.json) retain script,
stdout, stderr, return code, interpreter version, and output hash for **19
passing probes**. They cover populated provider output and issue selection,
ordinary/strict execution, stdin EOF, exact CR/backslash/blank/no-LF replay,
failure continuation, debug/quiet stderr, issue deduplication, cleanup,
nonexported state boundaries, `BASH_ENV` startup hooks, and exported options.

The actual interpreters are `/bin/bash` 3.2.57 and Homebrew Bash 5.3.20. Every
env-Bash child selects the same interpreter through an isolated `bash` symlink.
Host probes are deterministic; provider/inventory functions remain real.

Known baseline limitation, not an implementation finding: a direct populated
actionable `set -euo pipefail` call on Bash 3.2 prints the status panel but reports
`REMOTE_SSH_WELCOME_ISSUES[@]: unbound variable` while collecting the first issue,
and omits `next`. The outer call still returns zero. The ordinary case prints
one final `next:    remote-ssh doctor`; Bash 5.3 strict matches the ordinary case.
The accepted plan preserves existing option-specific limits rather than
expanding scope to fix this one.

The exported-option probes independently confirm that old external captures
see `errexit` off; on Bash 5.3 with exported `BASHOPTS`, modules see `nullglob`
on. The caller keeps `errexit` on, `nullglob` off, and its export attributes.

## R0 history — not accepted

Reviewed frozen candidate:
`/private/tmp/remote-ssh-welcome-candidate-r0`, implementation aggregate
`f9fc66f5936a0aec6f31a46e60bfba272c9cae9702310cde414cbb95659d723b`.
The R0 review covered the seven intended runtime files, new regression suite,
frozen harness/fixtures/screens, focused verification log, trace, and rejected
paired attempt. At that checkpoint, final smoke verification was incomplete.
No acceptance was inferred from the implementer's 125 passing focused tests or
the preliminary compatibility results.

### W0 — asymmetric materialization invalidates paired performance inputs

The auditor's read-only
[snapshot comparison](welcome-audit-evidence/snapshot-r0-review.json), generated
by [review_snapshots.py](welcome-audit-evidence/review_snapshots.py), confirms
exactly nine differences: the seven authorized runtime paths, an additional
ignored `dots/git/user.local` in candidate only, and `tools/defs/atuin.sh` mode
0600 rather than baseline 0644 with identical content. Private configuration
contents were not printed.

The first outside-sandbox paired attempt stopped after 139 successful JSONL
records. Baseline Bash 3.2 actionable PTY printed `git config missing`; candidate
printed `git config invalid`. The full rc identity hook consumes the additional
configuration, so the effective fixtures were unequal. This is a measurement
input blocker, not evidence of a welcome runtime regression. The
[failure log](welcome-measurements/paired-r0-attempt-1.log) retains the full
rejected screen. The frozen harness asserts before returning/writing its record,
so numerical ready/total time for that one rejected sample was not preserved;
its return-code/timeout/marker checks had already passed. The 139 earlier
records are retained as rejected partial data and cannot support performance
acceptance.

Minimum repair: retain the old artifacts, build a new candidate from the pinned
archive plus only authorized source/mode changes, verify the complete manifest
has no other differences, and repeat unchanged harness, fixtures, screens,
assertions, two full paired principal batches, and controls in one consistent
outside-sandbox context. The original workspace's ignored configuration stays
untouched. A separate repair planner received this finding for R1.

### W1 — missing required provider passes worker preflight and displays output

Reproducer:

```text
python3 dev/docs/welcome-audit-evidence/probe_worker_preflight.py \
  --candidate /private/tmp/remote-ssh-welcome-candidate-r0 \
  --output dev/docs/welcome-audit-evidence/worker-preflight-r0.json
```

The probe makes a disposable copy and removes only that copy's
`shell/welcome/hw.sh`. It invokes the real worker directly with the three
canonical wrapper paths, isolated HOME, no `BASH_ENV`, and unexported options.
On both actual Bash versions the library reports a source error, but its final
source/unset operations mask that status. Worker preflight checks the
orchestration functions, which still exist, then returns **0** after displaying
a partial panel without hardware. The
[complete results](welcome-audit-evidence/worker-preflight-r0.json) retain both
stdout/stderr and status. No worktree or frozen snapshot was modified.

The accepted plan requires library/preflight failure to return reserved status
125 **before any display**, allowing the parent to choose the external group
once. The current function-presence check does not establish that the required
library surface is loaded. Minimum repair: reject this incomplete load with
125 and empty stdout; prove parent fallback happens once before display; retain
normal rendering, renderer exit-125 containment, and no post-display replay.
Keep the repair within loader/worker validation, without provider or hook
semantics changes. The separate planner received this finding for the same R1.

### Supporting evidence and remaining checks

The auditor ran the same 19 untimed independent probes against frozen R0.
[Candidate results](welcome-audit-evidence/candidate-r0-probes.json) and
[comparison](welcome-audit-evidence/candidate-r0-comparison.json) show **19/19
exact stdout and return-code matches** with pinned baseline. Sixteen stderr
results also match byte for byte; the remaining three are expected diagnostics
whose temporary/runtime paths differ (Bash 3.2's known strict-array limitation,
and the external-debug cases on both interpreters). This check independently
covers real populated status APIs and both fresh-worker and external paths.

Source review confirms bounded builtin canonical-wrapper reads with NUL and LF
rejection, case-sensitive equality, registered paths, physical-tree binding,
whole-group fallback, the conservative exported-option gate, and separate
renderer captures. The worker trace records one executable worker plus an
external user module on each Bash; the forced route records all three wrappers
plus that user module. The regression suite covers renamed symlinks,
non-Bash user execution, state mutations, failure/125 containment, issues and
cleanup, and terminal transport. These observations support the design but do
not close W0/W1 or establish measured gain.

The local sandbox denies `/dev/tty` even with a controlling PTY. An independent
baseline terminal probe hit that restriction; the coordinator owns further
privileged executions. The auditor's approval-waiting command was interrupted,
with no running command/session left. This environmental restriction is not
counted as a runtime finding. Terminal tests and final timings must use the same
real terminal permissions for both versions.

## Repair rounds

R1 repairs W0 and W1 together under the separate
[repair plan](welcome-repair-plan.md), SHA-256
`65386aee5fddc3170b6209f6e067d72e288b614ba038e3943e17c7cfdfa75857`.
R1/R2/R3 are the maximum repair rounds; later findings do not restart this limit.
An unresolved R3 is escalated with evidence; there is no R4.

### R1 recheck before timings

Reviewed candidate: `/private/tmp/remote-ssh-welcome-candidate-r1`, runtime
aggregate `0703139284173f0358ac13431875f23b7035fbfcb1b83b104fdada6ba1c9e58b`.
The worker is the only one of the seven R0 source paths whose bytes changed;
the final worker SHA-256 is
`bb870d5ea1479b1d6d14ede338a404e0bb775c800cb3e6ee673d2028a547fcc0`.
Provider, status, rc-hook, config, Atuin, and public benchmark code remain
unchanged. The worker now checks required readable files and the complete
declared welcome/update helper surface before its first render. The checks use
builtins, do not invoke providers, do not load status eagerly, and do not add a
second welcome-library load.

**W1 closed:** the auditor's original
[fault probe on R1](welcome-audit-evidence/worker-preflight-r1.json) now returns
125 with empty stdout on both actual Bash versions. A separate independent
[parent recovery probe](welcome-audit-evidence/probe_parent_recovery.py) retains
[four full result pairs](welcome-audit-evidence/parent-recovery-r1.json): after a
worker-only lower-level helper omission, the parent attempts one worker and
executes exactly the three external wrappers once in order. Its complete actual
provider output matches a forced-external reference, appears once, continues to
an actual non-Bash user executable and the caller command, retains quiet/debug
stderr policy, and leaves no temporary files. The added implementation tests
have retained red/green evidence for missing files/functions, recovery, renderer
exit 125, and post-display failure.

**W0 materialization repaired; measurement completion pending:** the auditor's
[complete physical-tree comparison](welcome-audit-evidence/snapshot-r1-complete-review.json)
finds exactly the seven authorized paths and no other content, file-kind,
symlink-target, directory, or mode differences. Both trees lack the private
configuration, and both retain the pinned Atuin definition mode. The independent
[input verifier](welcome-audit-evidence/verify_review_inputs.py) and
[pre-timing result](welcome-audit-evidence/r1-inputs-pre-timing.json) verify the
fresh full pinned archive hash, both complete frozen manifests, the candidate
aggregate, current working runtime/test SHA-256 and modes, original frozen
harness/fixture/benchmark/12 screen hashes, and unchanged rejected R0 artifacts.
This uses a read-only check rather than trusting the materializer's green label.

The same [19 independent candidate probes](welcome-audit-evidence/candidate-r1-probes.json)
again [match all pinned-baseline stdout and return codes](welcome-audit-evidence/candidate-r1-comparison.json).
The coordinator executed the auditor's controlling-PTY probe outside the
sandbox: [baseline 4/4](welcome-audit-evidence/baseline-pty.json) and
[R1 4/4](welcome-audit-evidence/candidate-r1-pty.json), with identical terminal
text, redirected stdout, preserved caller input, and expected quiet/debug
diagnostics. These are untimed behavior checks.

The auditor reported R1 ready for final verification and timings. The R0 smoke
is supporting history because runtime changed during it; only the final frozen
R1 smoke can satisfy acceptance. No timing result from the earlier prototype,
preliminary baseline, or rejected partial R0 attempt proves the final R1 gain.

### Final R1 verification and performance decision

**ACCEPTED.** The final candidate is still runtime aggregate
`0703139284173f0358ac13431875f23b7035fbfcb1b83b104fdada6ba1c9e58b`, with
the same reviewed seven runtime files and final test sources. The auditor's
[post-timing input verification](welcome-audit-evidence/r1-inputs-post-timing-final.json)
rechecks physical complete manifests, source/modes, original fixed inputs, the
fresh pinned archive hash, and retained rejected R0 evidence. All pass. The
before/after timing checkpoints and paired metadata identify this same source.
W0 is now closed by both symmetric inputs and a complete replacement series.

The independent [final evidence review source](welcome-audit-evidence/review_final_evidence.py)
validates every raw record and saves its
[full statistics and checks](welcome-audit-evidence/r1-final-evidence-review.json).
It confirms:

- 920 unique records: 800 measured samples and 120 discarded warmups. Each
  version/cell has three warmups and 20 measured samples, in the exact planned
  alternating order. Both principal batches and all four first-batch controls
  are complete; no R0 sample was reused.
- All 920 return codes are zero, with no timeout, one ready marker, complete
  untruncated output, correct output hashes/lengths, and exact equality with
  the 12 original frozen screen files. No reduced panel or omitted provider
  workload accounts for the gain.
- All published median, p95, minimum, and maximum values were recomputed
  independently from raw samples and match. Both ready and total statistics,
  IQR/MAD, paired deltas, and per-cell sample counts are retained.
- Final-source traces on both Bash versions each contain one library load,
  three renderer captures, three dispatches, and three cleanup calls. Normal
  execution lists one worker plus the external user module; fallback lists
  the three wrappers plus that user module. Trace raw hashes and candidate
  fingerprint match.

All 16 populated principal comparisons have a lower ready median. The table
shows baseline → candidate milliseconds and percentage change:

| Bash | Fixture | Workload | Batch 1 | Batch 2 |
| --- | --- | --- | --- | --- |
| 3.2 | Healthy | Isolated | 210.60 → 194.82 (−7.49%) | 214.93 → 195.57 (−9.01%) |
| 3.2 | Healthy | Full PTY | 323.78 → 310.53 (−4.09%) | 327.39 → 301.82 (−7.81%) |
| 3.2 | Actionable | Isolated | 204.09 → 185.49 (−9.12%) | 208.03 → 186.71 (−10.25%) |
| 3.2 | Actionable | Full PTY | 325.69 → 287.17 (−11.83%) | 312.75 → 300.75 (−3.83%) |
| 5.3 | Healthy | Isolated | 231.85 → 203.90 (−12.05%) | 218.73 → 193.50 (−11.53%) |
| 5.3 | Healthy | Full PTY | 319.40 → 296.67 (−7.12%) | 331.17 → 314.47 (−5.04%) |
| 5.3 | Actionable | Isolated | 229.57 → 200.31 (−12.74%) | 217.05 → 192.34 (−11.38%) |
| 5.3 | Actionable | Full PTY | 324.15 → 293.81 (−9.36%) | 323.78 → 296.42 (−8.45%) |

Thus the final worker reduces isolated median time by 15.78–29.26 ms and full
PTY first-command-ready median time by 11.99–38.52 ms on this machine. The full
PTY marker follows rc execution and the complete welcome panel; PS1 rendering
and SSH transport are outside this measurement. Secondary total medians are
also lower in every principal cell (−3.81% to −12.71%).

The controls and tails were reviewed rather than accepted from the principal
medians alone. `bash-baseline` median ready differences are +0.283 ms (3.2) and
+0.236 ms (5.3), against baseline/candidate IQRs of 0.846–1.169 ms. This control
does not execute welcome code. `remote-ssh-min` marginal medians differ by
+0.825 ms and +0.496 ms, against IQRs of 5.004–8.470 ms; its paired median
deltas are −0.273 ms and −1.046 ms, with candidate faster in 11/20 pairs for
each interpreter. These small mixed paired effects do not establish a
reproducible control regression beyond the observed spread.

One principal ready p95 is higher: Bash 3.2 actionable full PTY batch 2 rises
331.51 → 346.10 ms (+14.59 ms), while its median falls 312.75 → 300.75 ms and
13/20 paired samples are faster. The other batch's same cell has p95
383.12 → 317.32 ms and 19/20 faster pairs. Candidate spread is visibly larger
in the second batch; this is retained as a tail caveat, without a repeatable
tail regression across batches. Other principal ready/total p95 values are
lower. The evidence supports the planned repeatable median improvement and
does not establish that every percentile or every individual login improves.
No additional timing run or R2 repair is warranted under the accepted criteria.

### Final smoke and execution conditions

The final full command is **`just smoke`**, exit 0: **862 passed, 58 skipped**
in 310.60 seconds, after syntax, ShellCheck, Ruff, and mypy success. The
[complete raw log](welcome-measurements/r1-detached-smoke.log) SHA-256 is
`8d62489bc65b1e9e804bf2e967cb329aa58401e6258c7537b351cd07cfabb199`.
The auditor independently verifies that log hash, the driver hash, and its
final runtime/test freeze hash in the saved final evidence review. Explicit
syntax checks also pass for all seven files on both actual Bash versions.

The [verification driver](welcome-measurements/run-verified-checks.py) runs the
exact full command with `start_new_session=True`, stdin `/dev/null`, and all
stdout/stderr written directly to a raw binary log. Its smoke mode has no
pytest filter, extra skip, output mock, or altered assertion. Creating a new
parent session prevents an inherited controlling terminal from redirecting old
stdout-assuming subprocess tests to `/dev/tty`; real PTY children created by the
tests remain allowed outside the sandbox. The same detached conditions pass
the three diagnostic tests and the complete suite. This is a valid correction
to the test launch environment.

Earlier interrupted/hanging or inherited-terminal attempts are historical
diagnostics, with the truncated inherited-terminal output explicitly marked.
They are not substituted for the full successful final log. No runtime/test
change or excluded failing test was used to obtain the final result. The
pre-existing Bash 3.2 strict issue-array limitation and absence of module
timeouts remain recorded limits, not newly claimed fixes.
