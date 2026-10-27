# Config Loader Independent Performance Verification

Date: 2026-10-27

A new paired experiment reproduced the large configuration-loader saving while
checking that both versions loaded the same settings and provenance markers.
The measurements below were repeated after the R1 error-status repair; they
cover the repaired runtime, not the earlier R0 implementation.
A separate execution trace explains the scale: the old populated load involved
318 distinct Bash process IDs, including the main shell, versus 4 in the current
implementation. This is performance evidence; the separate
[fresh behavior audit](config-loader-independent-reaudit.md) assesses correctness.

## Independent comparison

The [new measurement source](config-loader-reaudit-evidence/paired_measure.py)
does not call the implementation's earlier measurement script. It constructs
two temporary trees from Git HEAD `c41cbc4820594de95e2035cfc5ab896e16db9e70`.
The after tree differs only in `shell/config/{parse,load,markers}.sh`, copied
from the current worktree. Both trees otherwise contain the same tracked files.
No runtime files in the worktree were edited during this verification.

Each pair alternates its execution order: before/after, then after/before.
Both variants receive the same frozen nine-key fixture, isolated HOME/XDG,
selected Bash interpreter, locale, and fixed system-tool PATH. Fixture setup
and tree creation are outside the timed region. Loader cases use two warmups
and seven measured samples; full PTY startup uses two warmups and five samples.

Every populated loader sample verifies all nine setting values, their set/unset
state, both canonical provenance markers, and marker values before reporting
success. Missing, empty, and disabled cases verify absence. PTY samples verify
the settings, environment precedence, and corresponding provenance before
printing the ready marker. All these assertions passed for both versions.
The assertion code uses direct variable checks, not the loader's helper
functions, and is the same for both variants.

## Reproduced timings

Cells show matched before → after medians in milliseconds. All raw samples and
the source fingerprints are in
[paired results](config-loader-reaudit-evidence/paired-results.json).

| Measurement | Bash 3.2 | Bash 5.3 |
| --- | ---: | ---: |
| Process control | 3.78 → 3.36 | 9.49 → 8.72 |
| Loader disabled | 35.23 → 9.68 | 37.81 → 13.08 |
| Loader missing file | 46.77 → 10.61 | 51.26 → 13.68 |
| Loader empty file | 43.51 → 9.79 | 50.83 → 13.57 |
| Loader all nine keys | 377.68 → 11.52 | 332.59 → 14.62 |
| PTY min, missing config | 128.22 → 87.95 | 118.91 → 81.45 |
| PTY min with all nine keys | 459.78 → 86.51 | 412.33 → 90.72 |
| PTY welcome, missing config | 252.46 → 225.14 | 269.32 → 229.45 |
| PTY welcome with all nine keys | 605.64 → 224.65 | 600.21 → 229.38 |

The matched process controls stayed close while the populated loader saving
remained large. Full startup also improved after configuration postconditions
were added. This rules out an empty or bypassed config as the explanation for
these measured savings.

The absolute startup numbers differ from the first experiment: these are
temporary tracked-file snapshots without the worktree's `.git` directory or
ignored files, and this script adds explicit postcondition checks. Compare
before and after within this experiment; do not combine its absolute timings
with the earlier harness. Optional user tools remain absent from PATH, and
update checks and user welcome modules remain disabled by the chosen scenarios.

## Execution trace

A separate [trace script](config-loader-reaudit-evidence/subshell_trace.py)
uses Bash 5.3 and a dedicated xtrace file descriptor. Old code's internal
`2>/dev/null` redirections therefore cannot hide traced commands. Instrumented
runs are separate from the timed experiment. They use the same populated
fixture and verify the resulting settings and markers.

| Observation | Before | After |
| --- | ---: | ---: |
| Distinct observed Bash PIDs, main shell included | 318 | 4 |
| Maximum Bash subshell nesting | 2 | 1 |
| Traced commands, including verification | 3597 | 577 |
| Config-path lookups | 9 | 1 |
| Allowlist enumeration calls | 82 | 1 |
| Trim helper calls through command substitution | 171 | 0 |

The old implementation scans the config once for each allowed key, regenerates
the allowlist for each candidate line, and uses command substitutions for
trimming and constructing marker names. The current implementation scans once
and performs repeated string operations in the existing shell. Avoiding those
process creations explains the large gain for a tiny config file.

The count is of distinct Bash contexts observed in the trace, not every kernel
process or system call. The full trace and source hashes are retained in
[trace results](config-loader-reaudit-evidence/subshell-trace-results.json),
[before trace](config-loader-reaudit-evidence/subshell-trace-before.txt), and
[after trace](config-loader-reaudit-evidence/subshell-trace-after.txt).

The first trace field inside `paired-results.json` used ordinary stderr and
therefore observed only 48/4 visible Bash contexts. Its raw output is retained;
the dedicated-descriptor trace above supplies the complete observed counts used
for this conclusion. Neither timing series uses tracing.

## Repair checkpoint and retained R0 evidence

The same paired harness and trace were run before and after the R1 repair,
with no heavy tests running concurrently. All samples completed successfully
on the final repaired files. The final paired output contains 140 measured
loader/control samples and 80 PTY samples, excluding warmups. Source fingerprints
were checked against the current files and Git HEAD; both measurement scripts
are byte-identical to their retained R0 copies. Both final result files record
these SHA-256s:

| File | Final R1 SHA-256 |
| --- | --- |
| `shell/config/parse.sh` | `b478dca2f276abd625a721d0a839ada1b793c19764416cb452387ce39cb7465d` |
| `shell/config/load.sh` | `bfee6c32ce4b94cb7526acd5926cf8df6e44fe60b5dc898d3e706d3d6d470dea` |
| `shell/config/markers.sh` | `7591de066e72d9674f32677f32258ddafca53d149d72a541a3760ba9099dd0af` |

The earlier independent R0 results, scripts, and traces are preserved under
[`pre-repair-r0/`](config-loader-reaudit-evidence/pre-repair-r0/), including
[paired samples](config-loader-reaudit-evidence/pre-repair-r0/paired-results.json)
and the [FD 9 trace summary](config-loader-reaudit-evidence/pre-repair-r0/subshell-trace-results.json).
R0 populated-loader medians were 365.70 → 10.94 ms on Bash 3.2 and
412.36 → 16.74 ms on Bash 5.3; its dedicated trace also observed 318 → 4 Bash
contexts. The R1 repeat retains that large saving while restoring the confirmed
enabled-loader error status. Correctness and repair acceptance are assessed in
the [fresh behavior audit](config-loader-independent-reaudit.md).
