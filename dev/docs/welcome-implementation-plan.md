# Welcome Implementation Plan

Created: 2026-10-28
Revision: R1
Status: planning only; implementation requires explicit user approval after
independent plan acceptance
Baseline: `39226a2d9074acf08279e7c3edde6a51cc2a629c`

Back: [Developer tooling](../README.md)
Related: [Welcome contract](../../docs/shell/welcome.md),
[independent plan audit](welcome-plan-audit.md),
[startup benchmark](bench-shell.md),
[deferred optimization notes](../todo-bench.md),
[completed config optimization](config-loader-implementation-record.md)

## Goal and scope

Reduce the time until an interactive remote-ssh shell has displayed its current
welcome panel and runs its first command. Keep the panel's content,
ordering, colors, status checks, suggested commands, and user module behavior.
Support Bash 3.2 and Bash 5.3 without adding remote runtime dependencies.

Use one fresh Bash worker for the standard bundled modules instead of three
fresh Bash interpreters. The worker loads the welcome library once and renders
each bundled module in its own subshell. Keep the existing external executable
path as the compatibility fallback and for every user module. A small prototype
must demonstrate equivalent output and a real improvement before this design
is retained.

This plan covers welcome execution and the tests and measurements needed to
verify it. It does not change cache policy, update checking, status semantics,
Atuin, the installer, default tools, prompt integrations, the config loader, or
whether welcome is enabled. Keep detailed tools, scripts, hardware, and software
information on the screen; do not shorten the panel or move its work elsewhere.
The historical timings and targets in `dev/todo-bench.md` are context, not the
baseline or acceptance target for this change.

Runtime implementation begins only after the user explicitly approves the
independently audited plan. The plan author edits only this Markdown file.

## Current execution and compatibility boundary

`shell/rc.d/08-welcome.sh` loads `shell/welcome.lib.sh` only for interactive
shells, then calls `remote_ssh_welcome_main`. The library loads update-check
helpers and all welcome helpers into the calling shell. `remote_ssh_welcome_run`
creates an isolated run, a fresh issue file, and a fresh issue array. It executes
bundled files from `shell/welcome.d`, then enabled user files, collects allowed
issues, and prints at most one `next` command.

Each executable module currently gets a capture subshell and output temporary
file. Executing the three bundled scripts starts another Bash three times; each
script resolves its directory and reloads the full welcome library. The first
script separately loads the minimal `tools/lib/status.lib.sh` surface for tools
and scripts. The runner replays each captured text line to `/dev/tty`, falling
back to stdout when no controlling terminal is available. It preserves blank
lines and a final line without LF, adding LF during replay.

A subshell alone protects the caller from outward mutations, but it still sees
the caller's nonexported variables, functions, aliases, options, and dynamically
scoped locals. The existing fresh executable Bash sees exported state. Therefore
calling the renderers directly in the interactive shell's capture subshell would
change such cases as a nonexported `REMOTE_SSH_WELCOME_BANNER`, `NO_COLOR`,
`COLUMNS`, a private `hostname` function, or a stale status-library loaded flag.
The fresh worker preserves this environment boundary without a general shell
state normalizer.

Preserve these existing contracts:

| Area | Required behavior |
| --- | --- |
| Entry and toggles | Noninteractive hook calls are silent. Keep the current accepted toggle spellings, config/environment precedence, banner widths, `NO_COLOR`, color, and debug behavior. |
| Discovery | Use the existing bundled directory resolution, XDG user directory precedence and HOME fallback, glob order, and regular executable eligibility. Bundled modules precede user modules. |
| User modules | Always execute the actual file with its shebang as an external program; never source it, identify it by a reserved basename, or replace it with a renderer. Keep `/dev/null` stdin, capture/replay, stderr policy, and failure continuation. |
| Display | Preserve all banner/host/update/tools/scripts/hardware/software lines, whitespace, ANSI bytes, blank lines, and `next` placement. Replay each module before starting the next module. |
| Status providers | Keep current host fallbacks and platform behavior; use the same expected-tools, tool-status, script inventory, update-cache, SSH-agent, and Git identity APIs. Status loading stays minimal and does not source the command dispatcher. |
| Issues | Use a newly owned issue file for each run. Keep the allowlist, deduplication, unknown-issue diagnostics, stdout-as-text behavior, and command selection for zero, one, or multiple allowed issues. |
| Failures and cleanup | A module may print and return nonzero or exit without stopping later modules or the shell. Keep quiet/debug stderr behavior, issue cleanup, output-file cleanup, and clearing inherited issue variables. |
| Shell state | Module changes must not reach sibling modules, user modules, or the interactive shell. Keep working directory, variables, exported state, functions, options, traps, descriptors, and stdin intact except for the existing issue-variable clearing. |
| Standalone wrappers | Each bundled executable remains directly runnable, with the same output/status behavior and issue-file API. Invocation through a renamed symlink continues to work. |

The current runner has no module timeout; a slow custom module still delays
login. Failure to create a module temporary file currently skips that module;
failure to create the issue file can omit `next` while status text remains.
Retain those limits rather than turning this optimization into a new failure
policy. Tools, scripts, update-cache fields, and hardware remain freshly read
through their current APIs; this change provides no persistent cache.

## Shared renderers and standalone wrappers

Add `shell/welcome/bundled.sh`, sourced by `welcome.lib.sh` after the existing
status helpers and before the runner. Define three private orchestration
functions:

- `remote_ssh_welcome_render_remote_ssh`: move the body of
  `00-remote-ssh.sh` here, in its current order: banner, host, update, then tools
  and scripts through `remote_ssh_welcome_load_commands`, including its existing
  `0 checked / 0 ok` and `doctor` fallback.
- `remote_ssh_welcome_render_hw`: call `remote_ssh_welcome_print_hw`.
- `remote_ssh_welcome_render_sw`: call `remote_ssh_welcome_print_sw`.

Make the three executable scripts thin wrappers which load `welcome.lib.sh`
through their existing location logic and call their own literal renderer name.
Do not derive the renderer from `$0` or the invoked basename: that would break
renamed-symlink invocation. These wrappers and the worker use the same renderer
bodies; do not duplicate display logic or change `commands.sh`, `issues.sh`,
`update.sh`, or provider semantics.

Add a narrowly scoped qualification helper in `bundled.sh`. It receives the
explicit bundled directory and a discovered path, and returns a renderer only
for its three exact registered paths. It must also require `-f`, `-x`, no
symlink, and exact canonical wrapper content. A user-local file is never passed
to this helper, even if it has a registered basename or identical bytes.

The canonical content check consists only of the fixed wrapper prologue, one
of the three literal renderer calls, and the final LF. Keep one literal
prologue and the three fixed mappings next to the helper; this is a tiny wrapper
format, not a shell parser. Read and compare with Bash builtins, with bounded
input and private locals. Match case sensitively regardless of `nocasematch`;
plain builtin string equality can avoid that option's pattern semantics.
Reject read/open errors, missing or extra final LF, extra lines/bytes, NUL,
different shebang, and any other mismatch. Do not use `eval`, source the module,
rely on an exported marker, or require `cmp`, a checksum tool, Python, or Git.
Test that the accepted bytes are exactly the bytes shipped by the three wrappers
so a future wrapper edit cannot silently leave qualification out of sync.

Qualification is an optimization decision, not a security or atomic file-update
protocol. Every mismatch takes the existing executable path. In particular,
modified files and symlinked replacements continue to execute their actual
content and interpreter. Keep the old path available as a callable helper so
fallback does not recursively retry the optimization.

Bind qualification to the loaded library tree as well as the selected directory.
Resolve the physical shell directory of the loaded welcome library through its
own source location, independently of `REMOTE_SHELL_DIR`, and resolve the
physical parent of the selected bundled directory with builtin `cd -P`/`pwd -P`
in a subshell. Permit the worker only when these directories are equal. Its path
is exactly `<that shell directory>/welcome/bundled-runner.sh`, and it loads
`<that shell directory>/welcome.lib.sh`. If either resolution fails or the caller
loaded tree A while `REMOTE_SHELL_DIR` selects tree B, fall back for the whole
group, even if B has canonical wrappers and its own worker. Do not use wrapper
bytes as proof that two trees have the same providers. An unset
`REMOTE_SHELL_DIR` continues to resolve bundled files from the loaded tree.

## One fresh worker for a qualified bundled group

In `runner.sh`, add `remote_ssh_welcome_run_bundled <directory>`. Discover eligible
paths once using the existing ordering and eligibility rules; keep them in an
explicitly initialized local indexed array with a separate count so an empty
array works under Bash 3.2 `nounset`. Do not change the caller's glob settings or
rescan the directory after choosing a path. The ordinary `run_dir` interface
continues to run external executables and remains the user-module path.

Use the worker only if every discovered bundled path qualifies. Empty directories
remain a no-op. One unknown file, modified wrapper, symlink, different library
tree, unavailable worker, nonempty `BASH_ENV`, or exported `SHELLOPTS`/`BASHOPTS`
selects external execution for the entire discovered group. This avoids inserting
an extra Bash between the parent and custom bundled executables and preserves
their shebang, arguments, environment, and order. A set-but-empty `BASH_ENV` has
no startup hook; test it separately from unset and nonempty values. Do not
silently treat `/dev/null` as unset.

The exported-option gate is deliberately conservative. Today's `run_dir` sets
`nullglob` while iterating and the capture subshell runs `set +e` before exec.
Exported option variables can transmit these changes to a wrapper's Bash, so
launching the worker after discovery would not reproduce the old environment.
Use builtin `declare -p` output to inspect only the export attribute of
`SHELLOPTS` and, where present, `BASHOPTS`; do not change, unset, or re-export
these readonly option variables. Ambiguous inspection also falls back. Do not
normalize all Bash options. The ordinary case with these attributes unexported
still uses the fast path, including callers with local `set -e`.

External fallback must preserve the original launch scope, not merely call
`run_module` after restoring discovery state. Run the captured paths through a
private helper which establishes the original `nullglob`-on iteration scope and
restores it on return; its `run_module` calls retain the existing per-capture
`set +e` before exec. Reuse this execution helper from ordinary `run_dir` so the
two external paths have one definition. It must not rescan the directory or
change caller options/export attributes. This narrowly preserves the two
observed exported-option cases without a worker option normalizer.

Add executable `shell/welcome/bundled-runner.sh` with `#!/usr/bin/env bash`, the
same interpreter selection mechanism as today's wrappers. It loads
`welcome.lib.sh` once from its own location, performs preflight validation before
display, and receives the ordered qualified paths as arguments after `--`.
It calls the existing module capture/replay machinery with a private renderer
argument. Only this internal worker may supply that argument; it selects a
fixed registered function, never an arbitrary function name from file content.

The worker does not call `remote_ssh_welcome_main` or `remote_ssh_welcome_run`.
It inherits the parent's newly owned exported issue-file path and color setting,
does not replace or delete that issue file, does not collect issues, and does not
print `next`. The parent owns those operations exactly once after bundled and
user execution.

Keep a separate capture subshell for each renderer. Redirect its stdin from
`/dev/null`, preserve the current output file and line replay, and apply quiet
or debug stderr redirection to the renderer just as to an executable. The
worker must not set or clear `nullglob` merely to iterate its ordered arguments.
Do not reset an inherited option as part of renderer dispatch; the chosen
exported-option fallback preserves the old executable behavior where option
inheritance matters. Use private worker/runner local names to
avoid dynamically shadowing renderer/provider locals. Loading the status
library happens only inside the first renderer's capture subshell, so its
variables, functions, loaded flag, and tool-definition globals do not contaminate
the hardware or software renderer.

Keep the existing executable `run_module <path>` behavior; extend its private
implementation only enough for the worker to request a registered renderer.
Each renderer failure, including `exit`, is contained by its capture subshell;
the worker continues with the next path. A preflight/library failure must return
a reserved private status before any display so the parent can fall back once
without duplicate output. Only preflight may return that reserved status; a
renderer exiting with the same number must not trigger group replay. An
unexpected worker failure after display starts is
quiet except in debug mode and must still allow user modules, issue collection,
and the caller's next command. Do not add a persistent worker, new background
job, runtime configuration key, or general interprocess protocol.

This removes two fresh Bash starts and two full welcome-library reloads for the
normal three-module group. It deliberately retains one fresh worker, three
capture subshells and files, issue-file transport, actual status-provider work,
and the welcome library loaded by the interactive hook. The prototype and
measurements must establish that the saved work exceeds qualification and
worker-dispatch overhead.

## Files and implementation sequence

| File | Planned change |
| --- | --- |
| `shell/welcome/bundled.sh` | Shared render orchestration, fixed path/function mapping, bounded canonical-wrapper qualification. |
| `shell/welcome/bundled-runner.sh` | Fresh Bash entrypoint, preflight, ordered per-renderer execution; no issue-file ownership or `next`. |
| `shell/welcome/runner.sh` | Qualified group dispatch and explicit external fallback; reuse capture/replay for internal renderers. |
| `shell/welcome.lib.sh` | Load the new renderer/qualification helper; keep existing helpers and APIs. |
| `shell/welcome.d/00-remote-ssh.sh`, `10-hw.sh`, `20-sw.sh` | Thin standalone wrappers around the shared renderers; preserve executable modes. |
| `dev/tests/test_welcome.py` | Behavior, qualification, fallback, state isolation, terminal transport, and failure regression cases. |
| `docs/shell/welcome.md` | Explain the internal bundled worker and unchanged external user-module contract. |
| `dev/docs/welcome-implementation-record.md` and a local evidence directory | Verification, frozen harness/fixtures, source fingerprints, raw output/timings, and independent audit results. |
| `dev/docs/bench-shell.md` | Link the final execution record; keep public benchmark scenarios and CLI unchanged. |

Keep the rc hook, providers, status/update libraries, public commands, and
`dev/bench` implementation unchanged. If an equivalence failure requires a
provider or hook change, stop that expansion and return it to the repair planner
with evidence instead of broadening this optimization.

After user approval:

1. Add missing behavior cases and capture their baseline outcomes on the pinned
   commit. Freeze the measurement harness, fixtures, and interpreter paths, then
   record baseline measurements before runtime edits.
2. Extract shared renderers and thin wrappers, still using only external module
   execution. Verify standalone and runner output against baseline. This stage
   must preserve behavior before introducing the worker.
3. Add the bounded qualification and worker as the small prototype. Run focused
   compatibility checks and matched measurements. Retain it only if output,
   state boundaries, fallback, and first-command readiness meet acceptance
   criteria.
4. Complete the remaining regression coverage and documentation, then run
   `just smoke`, explicit syntax checks with both interpreters, and
   `git diff --check`. Do not run `just test-assets-live` or live network checks.
5. Hand the complete diff and evidence to a fresh implementation auditor. Keep
   any subsequent repair planning separate from implementation and audit.

## Behavioral verification

Extend the existing tests rather than replacing their expected output. Use the
`runtime_bash` fixture and explicit actual Bash 3.2/5.3 paths. Put a `bash`
symlink to the selected interpreter at the front of an isolated PATH so every
env-Bash wrapper, worker, and custom test module uses the same version. Sanitize
inherited `REMOTE_SSH_*`, `NO_COLOR`, `BASH_ENV`, exported functions, and relevant
shell-option variables for default tests; introduce each unusual state
explicitly in its own case. Run direct runner calls both ordinarily and under
`set -euo pipefail`, without putting the whole call inside a conditional that
would hide `errexit` failures. Compare new behavior to baseline where baseline
already has an option-specific limitation; do not describe that limit as fixed.

Cover these groups:

- Complete output: deterministic host/IP and provider fixtures; full/narrow/
  tiny/hidden banner; color, `NO_COLOR`, and debug variants. Verify exact text,
  ANSI bytes, line order and blank lines through standalone wrappers, the
  qualified worker, and forced external fallback. Keep healthy and actionable
  tools/scripts/software/update states, not only `0 checked` or disabled cases.
- Qualification: all canonical wrappers, a disabled/missing wrapper, no files,
  unknown executable between known names, nonexecutable file, symlinked canonical
  file, symlinked foreign interpreter, modified wrapper with the original
  prologue, altered case under `nocasematch`, extra/missing LF, extra bytes,
  embedded NUL, unreadable/open-failed file, and unavailable worker. Every
  ambiguous case must execute the actual external file or skip it by the old
  eligibility rule. Do not use chmod alone to claim unreadability when running
  as a privileged user.
- User modules: same reserved basenames and canonical-looking contents still
  use external execution; preserve shebang selection, executable filtering,
  ordering, XDG/HOME lookup, disable toggle, stdin EOF, arbitrary stdout, and
  failure continuation. Use an external non-Bash module or interpreter probe
  to prove it is never sourced.
- Issues and status: existing update disabled/missing/current/available/error/
  malformed-cache behavior; zero/one/multiple/duplicate/unknown issues; magic
  stdout remains visible text. Combine bundled and user issues and assert the
  same one final `next` line. Keep status.lib-only loading without the commands
  dispatcher and exported Git-session status consumption.
- Inbound state: nonexported versus exported banner/color/column variables;
  a nonexported provider function and status-loaded flag; inherited exported
  settings/functions; caller option/trap/IFS changes; unset, empty, and nonempty
  `BASH_ENV`. A nonempty hook forces the old path and keeps its current
  once-per-module startup effects. The normal timing case must leave `BASH_ENV`
  unset rather than setting it to `/dev/null`.
- Exported options: compare baseline and candidate with caller `set -e`,
  `nullglob` initially off, and exported `SHELLOPTS`; prove the old external path
  is selected and the module sees `errexit` off on both Bash versions. On Bash
  5.3 also export `BASHOPTS` and prove the module sees `nullglob` on, as under the
  original `run_dir`. Assert caller `errexit`/`nullglob` and export attributes
  are unchanged. Keep an ordinary unexported-state case which proves the worker
  actually runs. This does not require new support for unrelated Bash modes.
- Library origin: source the welcome library from tree A, then select tree B
  through `REMOTE_SHELL_DIR`. Give both trees identical canonical wrappers but
  different provider/library sentinels. Assert B's screen and external execution,
  even when B has a worker. With `REMOTE_SHELL_DIR` unset, assert the loaded tree
  A's screen and qualified worker; also keep direct standalone wrapper coverage
  with the variable unset. A path alias resolving to the same physical tree may
  use the worker.
- Outward state: in a temporary renderer fixture, mutate cwd, locals/globals,
  exports, functions, traps, options and descriptors, then exit nonzero. Assert
  the next renderer, user module, and caller see their original state and that
  the next command runs. Include reload/repeated-run cases and Bash 3.2 empty
  array handling. Keep fresh issue variables and cleanup after success/failure.
- Failures: module output followed by exit 7, quiet/debug stderr, failed status
  library load, issue and module `mktemp` failures, worker preflight failure,
  a renderer exiting with the reserved preflight number, and worker failure
  after a started render. Assert continuation, pre-display fallback only, and no
  duplicate panel. The existing absence of module timeouts remains separate.
- Terminal transport: PTY with a controlling terminal and redirected stdout
  must show the panel at the terminal; a process without a controlling terminal
  must receive it on stdout. Include empty output, blank lines, CR/text escapes,
  spaces/backslashes, and a final line without LF. Verify stderr separately in
  quiet and debug modes and prove modules do not consume the caller's input.

The focused test invocation is `(cd dev && uv run pytest -q tests/test_welcome.py)`.
Add an execution trace outside timed samples that proves the normal case uses
one worker and no three wrapper Bash executions, while fallback and user cases
execute their files. Trace/source review should establish the process boundary;
pytest should assert behavior rather than contain timing thresholds or reproduce
the qualification implementation.

## Reproducible measurements

Do not run timing loops during plan authoring or plan audit. After approval,
create a temporary developer-only harness using the existing
`bench.scenarios.scenario_environment`, `scenario_args`, and
`bench.pty_runner.run_pty_sample` APIs. Freeze that harness and its fixture
manifest before measuring either version. Import one fixed copy of the harness
and `dev/bench` for both trees; only the runtime repo argument changes.

Materialize the baseline runtime from the full commit
`39226a2d9074acf08279e7c3edde6a51cc2a629c` in an isolated developer directory.
Never resolve the baseline from floating `HEAD`. Materialize the candidate
runtime from the exact reviewed working-tree state. Record its base commit,
diff, per-file SHA-256 values, file modes, and aggregate source fingerprint.
Recheck fingerprints after correctness checks and after timings. The measured
candidate must be the candidate the auditor reviews; any runtime edit invalidates
the affected after measurements.

For each actual interpreter, use identical PATH/tool shims, locale, terminal
size, current directory, optional integrations, config bytes, update-cache
bytes, managed-tool layout, and sampling settings in baseline and candidate.
Record absolute interpreter paths and versions, OS/architecture, tool paths and
versions, environment overrides, fixture hashes, and whether HOME is fresh or
shared. Set up fixtures after `scenario_environment` returns its isolated
HOME/XDG paths and before starting the timer. Do not rely on the developer's
ordinary HOME. Resolve versions and create managed-tool symlinks outside timing.

Keep two populated screen fixtures. A healthy fixture has two expected managed
tools at their pinned versions, all four script helpers available, deterministic
host/IP, a current cached update, a usable agent, and valid exported Git-session
status. An actionable fixture has one missing expected tool, an unavailable
`bssh` requirement, an available cached update and a missing Git identity; it
must still run the actual status functions and produce the corresponding counts
and final `next`. Freeze the exact expected output for each fixture. Use local
executable shims only for external machine probes and tool presence; do not stub
welcome renderers or replace actual inventory/status APIs with constant text.
Hardware may use the same real host values if captured and asserted unchanged.

Use fresh, matching update-cache fixtures to suppress background network checks
in enabled-update scenarios. Write one fixed recent timestamp and text before
the paired run; do not change bytes between trees. Check that the cache remains
fresh for the whole run. No measurement may perform a network update or asset
request. Main optimized samples must remove `BASH_ENV` entirely and leave
`SHELLOPTS` and `BASHOPTS` unexported. Verify that the principal measurements use
the worker; keep nonempty `BASH_ENV` and exported-option fallback in correctness
tests and any targeted diagnostics.

Measure the finite principal matrix below with three discarded warmups and
twenty measured samples per version and cell, using alternating
baseline/candidate order to reduce drift. Repeat the whole principal matrix in
a second paired batch. Preserve every sample, return code,
timeout flag, complete output and output hash, not only medians or failed-output
tails. The existing public JSON report omits successful output, so the temporary
harness must retain `Sample.output_tail` and assert that output was not truncated;
the welcome fixtures must remain below the runner's 128 KiB limit.

| Principal workload | Fixtures | Interpreters | Paired batches |
| --- | --- | --- | --- |
| Fresh noninteractive process sourcing `welcome.lib.sh` and calling `remote_ssh_welcome_run` | Healthy and actionable | Actual Bash 3.2 and 5.3 | Two |
| Full PTY `remote-ssh-default-preseed` startup | Healthy and actionable | Actual Bash 3.2 and 5.3 | Two |

This is eight baseline/candidate comparisons per batch. The isolated workload
includes process creation, library loading, worker/capture, and actual status
work; detach its controlling terminal so stdout/stderr are captured separately.
The representative full PTY workload keeps welcome and cached updates
enabled, uses fresh HOME with the benchmark's existing once-per-HOME state
preseed, and retains the same optional integrations on both trees. User module
directories are empty in these principal samples. Assert the complete expected
screen before the first-command-ready marker for every sample.

Use a small control set: `bash-baseline` and `remote-ssh-min` on both actual
interpreters, using the same frozen healthy environment and one paired batch
with the same 3+20 sampling. Do not cross these controls with both screen
fixtures. Extra warm-home, user-module, and fallback timings are optional
targeted diagnostics only if correctness tests, the trace, or principal results
reveal a specific concern; they are not another mandatory scenario matrix.

Report raw samples, median, p95, min/max and absolute/percentage changes for ready
and total time. Label the full PTY result as first-command-ready: its marker
prints after rc execution and the complete welcome panel. This measures when
welcome stops delaying the first command, not PS1 rendering or SSH transport.
Keep PS1 and `PROMPT_COMMAND` untouched; no prompt adapter is required. Treat
total time as a secondary diagnostic and report the isolated result separately
from full startup. Do not compare synthetic `zsh-reference` values as measured
competing startup.

## Acceptance and audit workflow

Accept only when the baseline/candidate screen transcripts and status/issue
outcomes match, user and fallback modules retain external execution, both Bash
versions pass focused tests and syntax checks, and `just smoke` passes. Inspect
the final diff and trace for the intended one-worker process boundary, three
isolated captures, unchanged providers, and no extra runtime dependency or state.

The principal populated welcome cases must show a repeatable lower median in
both isolated welcome and full PTY first-command-ready time on both interpreters.
Controls must show no reproducible regression beyond the observed run-to-run
spread; inspect p95 as well as median. User and fallback paths must pass their
behavior tests; run a small matched timing diagnostic if those tests or the
trace identify added work that needs investigation. If noise obscures
the comparison, repeat that matched pair with unchanged fixtures and source,
then report the uncertainty. Do not accept a speedup from missing output, fewer
status checks, a skipped fast path, or different effective settings. Do not use
historical millisecond targets or enlarge scope to force a numeric win. If the
worker fails this test, return the result to the planner and remove or revise
the prototype before claiming completion.

The plan follows initial independent audit R0. If it needs revision, the plan
author addresses concrete findings and the separate fresh auditor rechecks
R1, R2, then R3 at most. An unresolved R3 is reported to the coordinator and
user; there is no R4 and no implementation before explicit user approval.

After approval, use a fresh implementer, then a fresh implementation auditor.
For findings, a separate repair planner produces the concrete repair plan before
an implementer changes code. Re-audit after each repair, with at most R1 through
R3. Stop and report unresolved R3 findings rather than beginning a fourth
round. Keep plan acceptance, user implementation approval, implementation
correctness, and measured performance as separate recorded decisions. This
workflow authorizes no commit, push, or live asset test.
