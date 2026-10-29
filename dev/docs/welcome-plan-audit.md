# Welcome Optimization Plan Audit

**Current verdict: ACCEPTED after R1.** R0 F1, F2 and F3 are closed, and no plan
findings remain open. This accepts the implementation proposal; runtime changes
still require the user's explicit approval.

The runtime baseline is commit
`39226a2d9074acf08279e7c3edde6a51cc2a629c`. The implementation proposal belongs in
[Welcome Implementation Plan](welcome-implementation-plan.md). This audit owns
only this report.

## Current behavior

These requirements were derived from the current sources and tests before
reading the implementation proposal.

| Surface | Behavior that the plan must preserve or explicitly bound |
| --- | --- |
| Entry and status | The rc hook and `remote_ssh_welcome_main` skip noninteractive shells. Interactive main absorbs welcome failures and returns zero. `remote_ssh_welcome_run` also works without `REMOTE_SHELL_DIR`; direct module execution remains supported by existing tests. |
| Selection and order | Each directory uses its glob order and selects existing executable files. Bundled modules run before user modules; disabled user modules do not run. Missing directories and nonexecutable files are skipped. |
| Output | Each module's completed stdout is replayed line by line, including output produced before a nonzero exit, blank lines, and a final line without a newline. Each replayed line first targets `/dev/tty`, with stdout as fallback. Stdout content never acts as an issue protocol. |
| Failures and stdin | Modules receive `/dev/null` as stdin. Their stderr is hidden normally and visible in debug mode, with a diagnostic for a nonzero module status. A failed module does not prevent later modules or shell startup. Temporary-output allocation failure skips that module. |
| Isolation | Executable modules currently run as separate processes. Their shell variables, functions, cwd, options, and traps do not mutate the calling shell or later modules. Any narrower boundary for trusted bundled rendering must be explicit and tested. |
| Issues | The runner ignores inherited issue state, creates its own issue file, accepts only `update`, `tools`, `scripts`, `sw`, and `doctor`, deduplicates issues, and removes its temporary state. The inherited file remains untouched. The two internal issue variables are unset after interactive main or direct run. |
| Status content | Host, update, tools, scripts, hardware, SSH agent, and Git status stay visible in the same order. Disabled or absent update cache state and agent status alone do not create an actionable `next` line. Single issues map to the existing commands; multiple issues map to `remote-ssh doctor`. |
| Configuration | The current welcome, user-module, banner, color, and debug toggles retain their meanings, including `NO_COLOR`. Config-loader precedence and reload behavior are outside this optimization. |

The main evidence is [the runner](../../shell/welcome/runner.sh),
[the library loader](../../shell/welcome.lib.sh),
[bundled executable modules](../../shell/welcome.d),
[welcome regression tests](../tests/test_welcome.py), and
[the documented panel contract](../../docs/shell/welcome.md).

## Review criteria

The plan must fit Bash 3.2 and 5.3 without a new runtime dependency, cache,
status policy, or broad loader refactor. It must describe a small execution
boundary that preserves module selection, observable streams and failures,
stdin handling, and shell isolation. Existing unsupported shell modes do not
need to become supported.

Correctness verification must exercise the proposed optimized route and its
fallbacks, retain direct bundled-wrapper coverage, and assert concrete output,
status, issue, and state results. A successful marker or zero exit alone cannot
establish that welcome ran.

Performance evidence must compare against the full baseline SHA above using
identical harness sources, fixtures, environment, Bash selection, and workload
on both sides. It must retain their source fingerprints and raw samples, assert
the expected status content, and measure both full PTY startup and the welcome
component separately. The existing
[PTY runner](../bench/pty_runner.py) and
[scenario definitions](../bench/scenarios.py) provide useful machinery, but the
current public benchmark only requires a ready marker and process status.

## R0 findings

### R0 F1 Preserve the external launch environment

The [worker design](welcome-implementation-plan.md#one-fresh-worker-for-a-qualified-bundled-group)
replaces external module launches with a worker but does not specify how its
launch reproduces the old capture's option changes. The current
`runner.sh` enables `nullglob` during directory execution at line 90, then
disables `errexit` at line 62 before executing each module. Exported option
variables can carry those choices into the new executable Bash. A fresh Bash
launched directly after discovery does not necessarily receive the same state.

A small local probe on unchanged runtime sources exported `SHELLOPTS` and
`BASHOPTS`, enabled `errexit`, disabled `nullglob`, and called the existing
`remote_ssh_welcome_run_dir` with an executable reporting its options. It then
launched a fresh Bash directly from the caller. Both interpreters showed
`errexit` absent inside the old module and present in the direct fresh Bash.
Bash 5.3 also showed `nullglob` enabled in the module and disabled in the direct
fresh Bash. Bash 3.2 does not expose the same `BASHOPTS` behavior.

| Interpreter | Old module | Direct fresh Bash |
| --- | --- | --- |
| `/bin/bash` 3.2.57 | `errexit` off, `nullglob` off | `errexit` on, `nullglob` off |
| `/opt/homebrew/bin/bash` 5.3.20 | `errexit` off, `nullglob` on | `errexit` on, `nullglob` off |

The R0 instruction that the worker must not activate `nullglob` also needs to
distinguish accidental worker glob setup from a value the old executable would
inherit. This finding concerns two concrete exported-option cases, not support
for every Bash mode.

**Required revision:** specify a small worker-launch scope that reproduces the
old executable's observable option environment without changing caller state,
or explicitly choose external fallback for the affected exported-option cases.
Add baseline/candidate assertions for exported `SHELLOPTS` with `errexit` on
and, on Bash 5.3, exported `BASHOPTS` with caller `nullglob` off. The ordinary
unexported-state fast path must still run.

**Closed in R1:** the plan chooses whole-group external fallback when either
option variable has an export attribute, with conservative fallback for an
ambiguous inspection. Its shared external execution helper retains the old
`nullglob`-on scope and per-capture `set +e`. The
[exported-options verification](welcome-implementation-plan.md#behavioral-verification)
requires both observed baseline/candidate cases and an ordinary case proving
the worker runs, while asserting caller options and attributes remain intact.

### R0 F2 Bind the worker to the selected bundled tree

The [qualification design](welcome-implementation-plan.md#shared-renderers-and-standalone-wrappers)
receives a selected directory, but the worker's lookup path is unspecified.
The current [bundled directory resolver](../../shell/welcome/base.sh) uses
`REMOTE_SHELL_DIR` when provided, and the selected wrappers load their library
from that tree. Canonical wrapper bytes alone cannot establish that a worker
from the currently sourced library tree will use the same providers as the
selected wrappers.

**Required revision:** define how the worker path and library root are derived
from, or verified against, the selected bundled directory. A different tree
must either use its corresponding compatible worker/library or execute the old
external path. Add a two-tree fixture with identical canonical wrapper bytes
and distinguishable library/provider output, plus the standalone unset
`REMOTE_SHELL_DIR` case. The assertion must prove which tree actually rendered.

**Closed in R1:** the plan requires the physical loaded-library shell directory
to match the selected bundled directory's physical parent. It derives the
worker and its library from that associated tree and otherwise uses external
fallback. The required A/B sentinel fixture proves B renders externally when
the library was loaded from A; the unset-variable fixture proves A can use the
worker. These rules appear in
[Shared renderers and standalone wrappers](welcome-implementation-plan.md#shared-renderers-and-standalone-wrappers).

### R0 F3 Keep the measurement harness within welcome scope

The [measurement section](welcome-implementation-plan.md#reproducible-measurements)
requires a separate first-PS1 adapter that preserves integration-specific PS1
rewrites and string/array `PROMPT_COMMAND` behavior, in addition to a broad
scenario matrix. That is a new prompt-instrumentation project with additional
correctness risks. It is unnecessary to establish that the same complete
welcome work finishes sooner and the first command runs sooner.

**Required revision:** use the existing full PTY first-command-ready measurement
with asserted complete panel output, and label it accurately without claiming
to measure PS1 rendering. Specify a finite principal matrix: isolated welcome
and one representative full PTY login workload, with populated healthy and
actionable fixtures on both actual interpreters and repeated paired batches.
Use a small matched set of Bash/minimum-startup controls. Verify external user
and fallback execution in correctness tests and small diagnostics as warranted;
do not multiply every fixture, control, optional scenario and prompt mode into
a mandatory Cartesian matrix. Retain the pinned baseline, identical frozen
harness/fixtures/environment, exact output/status assertions, source hashes,
execution trace, and raw samples.

**Closed in R1:** the principal matrix is now isolated welcome plus full PTY
`remote-ssh-default-preseed`, each with healthy/actionable fixtures on Bash 3.2
and 5.3 in two paired batches. Bash/minimum-startup controls use one separate
batch and one fixture. User/fallback timings are targeted diagnostics when a
specific concern warrants them. The
[measurement section](welcome-implementation-plan.md#reproducible-measurements)
keeps PS1 and `PROMPT_COMMAND` untouched and labels the observed PTY metric as
first-command-ready.

## Preflight and fallback assessment

The proposed reserved preflight status is feasible without a new IPC protocol.
All validation and library checks must precede the first renderer. Only that
phase may return the reserved fallback status. After the first renderer starts,
worker failure must never trigger external replay of the group; it must leave
the parent able to run user modules, collect issues, and continue startup.
Focused failure fixtures must prove both sides of that boundary and check for
duplicate or missing panel lines. The per-renderer capture subshell remains the
boundary for normal renderer nonzero exits and `exit` statements.

R1 also requires a renderer exiting with the reserved preflight number to remain
a per-module failure rather than trigger group replay. This makes the fallback
boundary independently testable without a more elaborate protocol.

## Accepted plan commitments

The following are implementation and verification requirements, not results of
an implemented optimization.

| Requirement | Accepted plan coverage |
| --- | --- |
| Small runtime change | Three shared renderers, one fresh worker, bounded qualification, and explicit external fallback. Providers, rc hooks, status policy, public commands, and `dev/bench` stay unchanged; no new runtime dependency, cache, background job, or configuration key. |
| Module compatibility | Existing discovery/order and executable eligibility remain. Modified, unknown, symlinked, different-tree, startup-hook, and exported-option cases retain external execution. Every user module stays external, including canonical-looking files with reserved names. |
| Streams and failures | Reuse per-module capture/replay, stdin EOF, `/dev/tty` with stdout fallback, debug stderr, output after nonzero exit, blank lines, and final-line normalization. Preserve issue ownership, allowlist, deduplication, cleanup, and one final `next`. |
| Isolation and Bash support | Fresh worker supplies the default inbound process boundary; each renderer has a capture subshell, so status-library and renderer state do not cross modules. Explicit interpreter selection covers Bash 3.2/5.3, strict direct calls, empty arrays, standalone wrappers, unusual inbound state, and outward mutations. |
| Real execution evidence | Assert healthy/actionable output, counts, statuses, issues, exit codes and transport. A trace must prove one worker on the normal route and actual executable launches on fallback/user routes. A ready marker alone is insufficient. |
| Reproducible performance | Full pinned baseline SHA, fixed common harness and `dev/bench`, identical fixtures and effective environment, actual interpreter paths, source/mode fingerprints, retained complete transcripts and raw samples, paired order, repeat batches, and populated actual status work. |
| Completion decision | Focused behavior and syntax checks on both Bash versions, `just smoke`, final diff/trace review, and a fresh implementation audit follow approval. Retain the worker only after repeatable measured improvement in isolated welcome and full PTY first-command-ready time without missing work or a reproducible control regression. |

The plan is feasible within those boundaries. Actual equivalence and any timing
benefit remain to be demonstrated by the approved implementation and its audit.

## Review history

| Round | Plan fingerprint | Verdict | Result |
| --- | --- | --- | --- |
| R0 | SHA-256 `ee3c158e42464121f59a06f2ffcbbab089d8223e47c401c36072161d1c671a28` | NEEDS REVISION | R0 F1, F2 and F3 require a plan revision. |
| R1 | SHA-256 `e55d02e7b374500c25d7418a4939d5ca55c5add81861c08bdf47823e033fb6d6` | ACCEPTED | All three R0 findings closed. Full revised plan reviewed; no new plan findings. |

R0 reviewed the full draft, current runtime sources, welcome and benchmark tests,
and the documented contract. It used only the small isolated option-environment
probe above; it ran no timing loop, smoke suite, network or live asset check.
R1 reread the full revised plan against the independently established contract
and checked the three revisions plus the strengthened preflight-status test.
It required no additional runtime probe or test run. Only the two planning
Markdown files are new in the working tree; this auditor edited only this
report. The report records plan-level feasibility, not implementation
correctness or a measured performance result. R2 and R3 were not needed.
