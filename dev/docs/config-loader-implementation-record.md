# Config loader implementation record

Date: 2026-10-27
Status: original implementation accepted at its initial R0 audit. A fresh
independent re-audit identified R0-F1; corrected R1 implementation and final
verification are complete, with fresh independent **R1 ACCEPTED**. R0-F1 is
closed; no further repair round is required.

Related: [accepted implementation plan](config-loader-implementation-plan.md),
[plan audit](config-loader-plan-audit.md),
[implementation audit](config-loader-implementation-audit.md),
[startup benchmark](bench-shell.md).

## Changes and boundaries

Stage A changed `shell/config/parse.sh` and `shell/config/load.sh`. Each load
builds three invocation-local indexed arrays from the shared entries, scans the
optional file once, and applies the existing ownership/precedence rules. The
single-key raw/gated lookup APIs use their own short-lived snapshot. The public
trim/unquote stdout helpers remain available. Parsing in the file loop uses
parameter expansion rather than command substitution.

Stage B changed `shell/config/markers.sh`. Canonical names are built in the
current shell with private locals. Ownership still requires a set setting, a
`config` source marker, and a present loaded marker equal to the current value;
empty values and exported child-process provenance retain their meaning.

`entries.sh`, `path.sh`, `config.lib.sh`, `env.sh`, guide runtime code, public
benchmark commands, and unrelated working-tree changes were left unchanged.
There is no persistent cache, format change, or new runtime dependency.

The focused regression cases live in `dev/tests/test_config.py` to keep literal
parsing, strict-mode failure paths, and ownership lifecycles separate from the
existing welcome-rendering integrations. `dev/tests/test_guide.py` adds child
guide reporting before/after file changes, reload, removal, empty values, and
the existing literal-delimiter display behavior.

## Baseline and correctness evidence

The new tests were first run against the old runtime, before any runtime edit:
49 passed and one failed. The failure exposed an existing Bash 5.3 strict-mode
edge case: direct raw lookup of a config path that is a directory aborted on an
uninitialized `line` variable after `read` failed. Loader calls already caught
that failure in their command substitution. Stage A's initialized reader and
guarded read/open path also make the direct raw API return an absent result,
as required by the plan's benign-failure contract. No parsing or precedence
expectations were weakened to make the baseline pass.

After Stage A, the same focused command passed all 50 config cases on the two
actual interpreter paths (10.95 s). After Stage B it again passed all 50 (5.80 s):

```bash
cd dev
uv run pytest -q tests/test_config.py tests/test_welcome.py tests/test_guide.py -k config
```

The new direct cases explicitly enable `set -euo pipefail`. They cover all
shared keys, found-empty versus missing values, literal shell syntax with a
nonexecution sentinel, whitespace/CRLF/quotes/duplicate/last-line rules, XDG and
HOME lookup, missing/empty/unavailable/directory paths, set-empty environment
precedence, incomplete/stale/legacy markers, `NO_COLOR`, repeated reload cycles,
disable/re-enable, manual changes/unsets, and inherited markers in an env-Bash
child. The interpreter fixture runs `/bin/bash` 3.2.57 and the resolved Homebrew
Bash 5.3.20. Integration children use a temporary `bash` symlink to that selected
interpreter. New fixture environments remove inherited `REMOTE_SSH_*` and
`NO_COLOR` values and markers.

Syntax checks with both actual Bash interpreters and targeted shellcheck passed
after both stages. Ruff passed for the modified tests and measurement source.
Final `just smoke` passed: Bash syntax, shellcheck, ruff, mypy (12 source files),
and **751 passed, 57 skipped** in pytest (285.39 s). The live asset checker is
outside scope and was not run. The command, exit code, and captured verification
output are saved in [smoke evidence](config-loader-measurements/smoke-stage-b.txt).

## Reproducible measurements

The same frozen [measurement source](config-loader-measurements/measure.py) and
[nine-key fixture](config-loader-measurements/ninekeys.conf) were used at baseline,
after Stage A, and after Stage B. Baseline completed before the first runtime
edit; Stage A completed before marker edits. Each raw JSON records the harness
hash, fixture bytes/hash, exact interpreter/version, OS, environment overrides,
tool availability, runtime source snapshots/hashes, warmup/sample counts, and
every measured sample. These records permit reconstruction of each checkpoint.

The fixture was generated once from `remote_ssh_config_entries`, using current
defaults and an empty value for `[unset]`. All measured commands use
`LC_ALL=C`, `TERM=xterm-256color`, and a fixed
`PATH=<temporary selected-Bash shim>:/usr/bin:/bin`. Optional user tools are
absent on this path. Inherited runtime settings/markers and shell startup
injection variables are removed. Network checks are disabled by the existing
min/welcome scenario overrides, and user welcome modules are disabled or the
whole welcome hook is disabled.

The loader measurement times process creation through exit with a monotonic
clock: a fresh `bash --noprofile --norc`, sourcing `config.lib.sh`, and one load
(or just `:` for the process baseline). Each case gets an isolated HOME/XDG,
one warmup and seven samples. Fixture setup is outside timing. This is not the
duration of an SSH connection or full login.

Full startup uses the existing `scenario_environment`, `scenario_args`, and
`run_pty_sample` APIs with three warmups and twenty samples per scenario and
config. Each sample gets a fresh HOME/XDG; its config fixture is created after
`scenario_environment` and before timing. Both missing and populated config are
measured for `bash-baseline`, `remote-ssh-min`, and `remote-ssh-welcome`. Ready and
total time, median, range, p95, status, and captured output are preserved.

Run one checkpoint/interpreter/mode using the frozen source, for example:

```bash
cd dev
uv run python docs/config-loader-measurements/measure.py stage-b --mode loader --bash /bin/bash
uv run python docs/config-loader-measurements/measure.py stage-b --mode pty --bash /opt/homebrew/bin/bash
```

Those commands measure the current checkout; use the stored runtime source
snapshots when reproducing an older checkpoint. The source is execution evidence,
not a new supported benchmark CLI.

### Raw records

| Checkpoint | Loader Bash 3.2 | Loader Bash 5.3 | PTY Bash 3.2 | PTY Bash 5.3 |
| --- | --- | --- | --- | --- |
| Baseline | [JSON](config-loader-measurements/baseline-loader-bash32.json) | [JSON](config-loader-measurements/baseline-loader-bash53.json) | [JSON](config-loader-measurements/baseline-pty-bash32.json) | [JSON](config-loader-measurements/baseline-pty-bash53.json) |
| Stage A | [JSON](config-loader-measurements/stage-a-loader-bash32.json) | [JSON](config-loader-measurements/stage-a-loader-bash53.json) | [JSON](config-loader-measurements/stage-a-pty-bash32.json) | [JSON](config-loader-measurements/stage-a-pty-bash53.json) |
| Stage B | [JSON](config-loader-measurements/stage-b-loader-bash32.json) | [JSON](config-loader-measurements/stage-b-loader-bash53.json) | [JSON](config-loader-measurements/stage-b-pty-bash32.json) | [JSON](config-loader-measurements/stage-b-pty-bash53.json) |

### Original Stage B results (historical)

Loader cells show median (minimum–maximum), in milliseconds. Every comparison
uses the matching config fixture and interpreter.

| Bash | Case | Baseline | Stage A | Stage B |
| --- | --- | ---: | ---: | ---: |
| 3.2 | Process only | 2.68 (2.60–3.18) | 3.45 (2.76–3.90) | 2.70 (2.53–3.70) |
| 3.2 | Disabled | 31.59 (30.64–34.26) | 34.70 (31.63–37.31) | 8.10 (7.27–9.16) |
| 3.2 | Missing | 47.80 (43.34–57.96) | 34.35 (31.96–43.42) | 8.26 (8.03–9.45) |
| 3.2 | Empty | 43.35 (42.01–47.78) | 35.14 (32.18–45.71) | 8.43 (8.27–11.55) |
| 3.2 | Nine keys | 361.96 (352.90–392.99) | 34.17 (33.65–35.89) | 8.89 (8.66–9.55) |
| 5.3 | Process only | 6.97 (6.52–7.26) | 8.05 (7.52–8.65) | 7.08 (6.47–7.21) |
| 5.3 | Disabled | 36.76 (36.43–55.74) | 42.82 (40.49–44.69) | 10.81 (10.66–13.91) |
| 5.3 | Missing | 53.88 (49.73–55.45) | 43.54 (41.18–47.47) | 11.70 (11.41–12.24) |
| 5.3 | Empty | 51.71 (50.55–59.21) | 43.22 (41.82–44.63) | 12.02 (11.35–14.85) |
| 5.3 | Nine keys | 341.24 (331.15–360.54) | 47.07 (44.25–56.48) | 14.39 (13.22–19.08) |

PTY cells show **ready median / p95; total median / p95**, in milliseconds.

| Bash | Scenario / config | Baseline | Stage A | Stage B |
| --- | --- | ---: | ---: | ---: |
| 3.2 | Control / missing | 5.72 / 6.80; 6.03 / 7.14 | 5.89 / 13.04; 6.21 / 13.40 | 5.25 / 6.63; 5.52 / 7.02 |
| 3.2 | Control / nine keys | 5.86 / 7.15; 6.19 / 7.48 | 5.33 / 6.06; 5.66 / 6.37 | 4.50 / 4.80; 4.79 / 5.12 |
| 3.2 | Min / missing | 188.49 / 205.87; 188.81 / 206.19 | 206.72 / 224.90; 207.05 / 225.28 | 149.74 / 161.21; 150.05 / 161.54 |
| 3.2 | Min / nine keys | 544.64 / 668.39; 544.96 / 668.78 | 199.94 / 217.03; 200.29 / 217.42 | 147.30 / 165.33; 147.60 / 165.74 |
| 3.2 | Welcome / missing | 354.60 / 547.07; 354.98 / 547.57 | 370.89 / 403.64; 371.39 / 404.10 | 292.79 / 316.91; 293.17 / 317.33 |
| 3.2 | Welcome / nine keys | 669.69 / 789.90; 670.09 / 790.35 | 343.82 / 370.80; 344.22 / 371.20 | 331.54 / 479.22; 331.92 / 479.70 |
| 5.3 | Control / missing | 9.86 / 12.68; 10.32 / 13.43 | 8.83 / 10.48; 9.22 / 10.94 | 8.84 / 9.96; 9.23 / 10.34 |
| 5.3 | Control / nine keys | 9.14 / 10.66; 9.55 / 11.16 | 9.23 / 10.34; 9.71 / 10.83 | 9.06 / 10.20; 9.48 / 10.68 |
| 5.3 | Min / missing | 194.12 / 210.91; 194.68 / 211.37 | 176.25 / 193.10; 176.70 / 193.60 | 158.14 / 180.03; 158.62 / 180.55 |
| 5.3 | Min / nine keys | 501.22 / 522.19; 501.81 / 522.69 | 175.16 / 187.84; 175.69 / 188.29 | 164.66 / 181.60; 165.19 / 182.12 |
| 5.3 | Welcome / missing | 360.64 / 432.49; 361.26 / 433.17 | 353.05 / 421.83; 353.61 / 422.39 | 350.79 / 438.52; 351.40 / 439.31 |
| 5.3 | Welcome / nine keys | 652.43 / 695.10; 652.99 / 695.64 | 334.05 / 374.55; 334.58 / 375.10 | 327.97 / 380.67; 328.57 / 381.44 |

Populated loader medians fell by about 98% (Bash 3.2) and 96% (Bash 5.3), with
nonoverlapping before/after sample ranges. Final missing, empty, and disabled
loader costs also fell substantially. Populated full-startup ready medians fell
from 545/501 ms to 147/165 ms for min and from 670/652 ms to 332/328 ms for welcome
(Bash 3.2/5.3). These are local startup measurements, not SSH connection timings.

Small full-startup differences remain noisy: Stage A missing-config startup on
Bash 3.2 was slower despite its faster isolated loader, while final Stage B was
faster than the matching baseline. Bash 5.3 welcome/missing has only a small
median reduction and overlapping tails (p95 is about 6 ms higher). The evidence
supports the large populated-config saving; it does not establish an improvement
for every individual full-startup sample or tail percentile. All raw observations
are retained, including that noise.

## Final checks and handoff

Structural review confirms one reader call before the loader's apply loop, one
redirected config input loop, no per-line command/process substitutions, and no
command substitutions in marker operations. The four snapshot output variables
are declared only by their callers and disappear when those calls return.

The original Stage B source fingerprints match every Stage B measurement
record. R1 changes are recorded separately below; these historical records have
not been overwritten.

| File | SHA-256 |
| --- | --- |
| `parse.sh` | `144974b02abba3ed2cabf50fd22474380fba862de0cefb09a99646bd5b2da9cf` |
| `load.sh` | `b34d057eb296bee51ff7d60f842a398182c52718a21e55243d60fedc09857bf3` |
| `markers.sh` | `7591de066e72d9674f32677f32258ddafca53d149d72a541a3760ba9099dd0af` |

At the initial R0 handoff, Bash 3.2 syntax and `git diff --check` passed, and all
local Markdown links in this record and `bench-shell.md` resolved. Runtime/test
edits stopped for that review. No stage/commit/push was run.

The independent [implementation audit](config-loader-implementation-audit.md)
accepted R0 after checking the code, smoke evidence, all 12 raw JSON records and
their hashes/stage boundaries, differential parser probes over 31 fixtures,
eight ownership/lifecycle states, and local/global scope in both Bash versions.
No blocking findings or planner-assigned repair were needed.

A helper command to summarize JSON through `uv` encountered a sandbox cache-lock
permission error after `just smoke` had already started. Its escalated retry
waited for approval and was interrupted by the coordinator; this delayed status
communication but did not affect the code, measurements, or successful smoke
run. The JSON summary was subsequently read with the existing local Python
environment, without accessing that cache. No dependency or permission change
was necessary.

## Repair R1 after the fresh independent re-audit

The [fresh re-audit](config-loader-independent-reaudit.md) found R0-F1 (P3):
failed catalog initialization was masked by the initializer's count assignment
and explicit success, then accepted by the loader. On Bash 3.2 after enabling
POSIX mode, the catalog process-substitution input redirection fails. The old
enabled loader returned one; Stage B incorrectly returned zero with unchanged
settings/markers. This concerns error reporting in an already unsupported mode,
not a request to add POSIX-mode loading support.

The separate planner provided the [R1 repair plan](config-loader-repair-plan.md).
Its minimal runtime change guards the consuming catalog loop before assigning
the count, then stops both callers on initialization failure before path
resolution/read/application. Raw lookup returns that actual error. The loader
saves it immediately and follows the existing enable gate: enabled loading
returns the error; disabled loading returns zero with prior state intact.
Optional config-file failures remain benign; the literal parser, snapshot
reader, ownership rules, markers, and raw-directory improvement are unchanged.

The first R1 plan mistakenly assumed the old disabled strict call aborted and
temporarily requested uniform error propagation. The fresh auditor's frozen-R0
gate comparison disproved this: both ordinary and standalone strict disabled
calls returned zero and preserved existing values/markers. Root requested exact
preservation of that behavior, and the planner corrected the same R1 before
final verification. The earlier red/green evidence is retained below as
superseded history, not as the final compatibility oracle. There is no
POSIX/Bash-version special case or process-substitution producer-status protocol.

New regression cases were added and run before changing runtime. They exercise
fresh load, reload after changing the file, and disabling after an initial load,
with both ordinary and strict standalone calls on both actual Bash interpreters.
They save the loader's own status immediately, assert the actual value and both
canonical markers, and use an EXIT-trap checkpoint plus a following sentinel to
verify strict termination. A raw-lookup test separately proves that a failed
initializer prevents config path resolution. Bash 3.2 must fail and preserve
prior state when enabled; its disabled failure must return zero, preserve prior
state, and reach the following sentinel even in strict mode. Bash 5.3 must
succeed and actually load/clean up the expected state.

| R1 verification | Result | Evidence |
| --- | --- | --- |
| Initial, superseded expectations on Stage B | 7 failed / 7 passed (includes two incorrect disabled expectations) | [Original red](config-loader-measurements/repair-r1-red.txt) |
| Initial, superseded repair | 14 passed / 34 deselected, 0.27 s | [Original green](config-loader-measurements/repair-r1-green.txt) |
| Initial, superseded focused run | 64 passed / 38 deselected, 6.06 s | [Original focused](config-loader-measurements/repair-r1-focused.txt) |
| Corrected expectations against frozen Stage B/R0 | 5 failed / 9 passed, 0.45 s | [Corrected red](config-loader-measurements/repair-r1-corrected-red.txt) |
| Corrected final R1, same regressions | 14 passed / 34 deselected, 0.48 s | [Corrected green](config-loader-measurements/repair-r1-corrected-green.txt) |
| Corrected final R1, all focused config cases | 64 passed / 38 deselected, 8.41 s | [Corrected focused](config-loader-measurements/repair-r1-corrected-focused.txt) |
| Syntax, both actual Bash versions | Passed | `/bin/bash -n` and `/opt/homebrew/bin/bash -n` on all three config modules |
| Targeted ShellCheck and Ruff | Passed | All three config modules; `dev/tests/test_config.py` |
| Diff whitespace | Passed | `git diff --check` |
| Corrected final R1, `just smoke` | Exit 0; 765 passed / 57 skipped, 308.64 s | [Full smoke output](config-loader-measurements/repair-r1-smoke.txt) |

The red/green command was:

```bash
./dev/.venv/bin/python -m pytest -q -p no:cacheprovider dev/tests/test_config.py -k 'catalog_failure or catalog_initialization'
```

The focused command used the same local Python environment and disabled pytest's
cache provider, with all three config/welcome/guide test files and `-k config`.
No cache approval or new dependency was needed.

The corrected red run rebuilt a temporary minimal tree from the three frozen
runtime source snapshots in `stage-b-loader-bash32.json`, plus the unchanged
config catalog/path/library and the corrected tests/fixture. Its evidence
records each runtime/test SHA, exact command, output, and process status. The
shared worktree was not temporarily reverted. The
[final R1 runtime delta](config-loader-measurements/repair-r1-corrected-runtime.diff)
is separate from the retained superseded first-attempt diff.

R1 source fingerprints:

| File | SHA-256 |
| --- | --- |
| `parse.sh` | `b478dca2f276abd625a721d0a839ada1b793c19764416cb452387ce39cb7465d` |
| `load.sh` | `bfee6c32ce4b94cb7526acd5926cf8df6e44fe60b5dc898d3e706d3d6d470dea` |
| `markers.sh` (unchanged) | `7591de066e72d9674f32677f32258ddafca53d149d72a541a3760ba9099dd0af` |
| `test_config.py` | `7d3bcaacbc8a038451b8e83baf5c5d2318c077762bbe69a6430240a967acbb47` |

All original baseline/A/B measurements and the original smoke evidence remain
historical. The coordinator's final R1
[independent paired measurements and FD 9 trace](config-loader-reaudit-performance.md)
completed before the heavy smoke suite, avoiding concurrent timing/test workload.
They cover 140 loader/control and 80 PTY samples, check actual values/markers,
and preserve the large populated-config saving. The separate trace again
observed 318 versus 4 distinct Bash contexts. Its source hashes match the final
R1 fingerprints above; the performance report distinguishes these final results
from retained R0 evidence.

The new `just smoke` completed successfully on these corrected R1 files, with
765 passed and 57 skipped (308.64 s), plus successful syntax, ShellCheck, Ruff,
and mypy checks. Its full captured output, command, exit status, and runtime
fingerprints are in the separate R1 log above. No full tests are repeated for
documentation-only updates.

The [final R1 checkpoint](config-loader-measurements/repair-r1-checkpoint.json)
preserves final runtime/test source snapshots and SHA-256 values for the corrected
red/green/focused output, runtime delta, and complete R1 smoke log.

The [fresh independent auditor accepted R1](config-loader-independent-reaudit.md)
after checking the new smoke log and final fingerprints. Its independent probes
covered 224 differential pairs, 24 generic initialization-status-7 cases, and
64 focused pytest cases. Enabled failure propagation, legacy disabled success,
actual setting/marker state, and stopping before file lookup/application all
passed. R0-F1 is closed, with no new blocking finding or further repair round.
