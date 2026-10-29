# Welcome measurement evidence

Back: [Execution record](../welcome-implementation-record.md)

`harness.py` is the frozen one-off developer harness. It imports the fixed copy
of the existing benchmark in `frozen_bench/`, uses its scenario environment,
arguments and PTY runner, and changes only the runtime repository argument.
`fixtures.json` records fixed probe, tool, config and cache bytes. Each sample
has a fresh isolated HOME prepared before timing. Normal samples unset
`BASH_ENV` and do not export shell option variables. No network is required.

The baseline is always the full commit named in the execution record, never
floating HEAD. Full successful output, return status, timeout, output hash,
ready and total time are retained in JSONL. Expected screens are frozen from
the baseline before runtime edits and asserted byte for byte in every sample.
The marker follows the full screen. PTY timings mean first-command-ready,
not first PS1 rendering. A separate detached workload measures welcome alone.

The partial first R0 paired attempt is rejected; its 139 complete records and
the assertion failure are retained with explicit rejected-sample accounting.
R1 uses a fresh full pinned archive plus a seven-path source/mode allowlist.
`materialize-r1.py` and `candidate-r1-frozen.json` retain its red/green gates and
complete tree manifests. `verify-r1.py` rechecks the fixed inputs, seven reviewed
working runtime files and materialized trees around final checks and timings.
Test source hashes/modes are retained in `r1-runtime-tests-final-freeze.json`
and checked by the independent audit's input gate and final coordinator check.

Real terminal checks run outside the sandbox. The top-level verification process
is detached from an inherited controlling terminal; dedicated PTY cases create
their own. `run-verified-checks.py` records complete raw logs and hashes for the
fixed verification commands. Earlier interrupted or inherited-TTY smoke attempts
are supporting history and do not establish final verification acceptance.

The frozen fixtures retain the full banner and status panel at 100 columns,
with `LC_ALL=C`, `TERM=xterm-256color` and colors disabled. Healthy has managed
`rg` 15.1.0 and `fd` 10.3.0, all four script helpers available, a current update
cache, a successful simulated `ssh-add` probe and valid exported Git-session
status. Actionable omits `fd` and the `bssh` requirement, has an available update
and missing Git identity, and prints one final `remote-ssh doctor` suggestion.
Only external machine probes/tool presence are shimmed; renderer, inventory,
status, issue and cache APIs execute normally. Exact bytes are in `fixtures.json`
and all twelve golden transcripts are in `screens/`.

The final R1 series is [paired-r1.jsonl](paired-r1.jsonl), with
[metadata](paired-r1.metadata.json), [process log](paired-r1.log) and
[complete statistics](paired-r1-summary.json). It completed with exit 0:
920 full-output assertions, 920 zero return codes, no timeouts. That is 736
principal and 184 control records, including 120 discarded warmups and 800
measured samples. Two batches cover isolated welcome/full PTY × healthy/actionable
× Bash 3.2/5.3; one control batch covers `bash-baseline` and `remote-ssh-min` on
both interpreters. Each tree/cell/batch uses 3 warmups and 20 measured samples,
alternating baseline/candidate order. The summary's p95 is the nineteenth sorted
value among twenty measured samples; raw samples retain the full distribution.

Every principal median is lower in both batches: isolated welcome by 7.49–12.74%
and full PTY first-command-ready by 3.83–11.83% (11.99–38.52 ms). Total time is
reported separately. Controls have small positive median deltas (0.24–0.83 ms)
within overlapping observed ranges, and Bash 3.2 actionable PTY batch 2 has a
higher candidate p95. See the [execution record](../welcome-implementation-record.md)
for every comparison and the independent audit for their acceptance. These
numbers describe this host and frozen fixture set.

Final verification is the complete detached
[`just smoke` log](r1-detached-smoke.log): 862 passed, 58 skipped, exit 0, with
[hash metadata](r1-detached-smoke.metadata.json). Runtime, complete-tree and frozen
input fingerprints pass before and after timings. The
[final coordinator check](root-final-source-check.json) also verifies all ten
runtime/test/conftest source hashes/modes against final R1 freeze.

**Final independent audit: R1 ACCEPTED; W0/W1 closed, no R2 required.** The
[report](../welcome-implementation-audit.md) and
[final evidence review](../welcome-audit-evidence/r1-final-evidence-review.json)
verify the complete raw series, recomputed statistics, controls/tail caveat,
final source/modes, execution trace and successful full smoke log.
