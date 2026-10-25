# Refactor Audit Stage 1: Shell Runtime

Date: 2026-06-01

This report audits the shell runtime for refactor readiness. It covers
`shell/rc.sh`, `shell/env.sh`, `shell/aliases.sh`, `shell/config*`,
`shell/update-check*`, `shell/welcome*`, `shell/rc.d/`, and root `lib/`.
It does not apply code changes.

## Findings

### 1. Welcome startup does substantial work through subprocess modules

Risk: high

References:

- `shell/rc.d/08-welcome.sh:10-13` sources `welcome.lib.sh` and runs the
  welcome entrypoint during interactive startup.
- `shell/welcome/runner.sh:55-81` runs every welcome module as a separate
  executable process, with a temp output file per module.
- `shell/welcome/runner.sh:84-95` runs every executable file in each welcome
  directory.
- `shell/welcome/runner.sh:169-177` runs bundled modules, optional user
  modules, collects issue state, and prints the next action.
- `shell/welcome.d/00-remote-ssh.sh:3-13`, `shell/welcome.d/10-hw.sh:3-7`,
  and `shell/welcome.d/20-sw.sh:3-7` each re-source `welcome.lib.sh`.
- `shell/welcome/commands.sh:3-12` loads the reduced tool status library from
  the main repo tree.
- `shell/welcome/commands.sh:24-40` checks expected tool status for every
  expected tool.
- `shell/welcome/commands.sh:66-79` checks helper script entrypoints,
  backends, and requirements.

The current design isolates modules well, but every default interactive shell
can spawn multiple Bash processes, repeatedly source `welcome.lib.sh`, and load
tool status code just to render the banner/status panel. This is the main
startup-cost risk in Stage 1.

Suggested order:

1. Benchmark current `remote-ssh-welcome` and `remote-ssh-default` startup
   scenarios before changing this area.
2. Preserve module isolation until tests cover equivalent issue propagation and
   stdout/stderr behavior.
3. Only then consider reducing repeated loader work or collapsing bundled
   module execution.

### 2. Update-check background lock can become permanently stale

Risk: medium

References:

- `shell/rc.d/04-update-check.sh:22-23` uses `mkdir "$lock_dir"` as the
  non-blocking lock and silently returns if it already exists.
- `shell/rc.d/04-update-check.sh:25-27` removes the lock only through the
  background process EXIT trap.
- `shell/rc.d/04-update-check.sh:33-39` skips refresh when the stale-check path
  cannot acquire that lock.

If the background process is killed before its EXIT trap runs, the lock
directory can remain next to the cache file and suppress future login-time
refreshes indefinitely. The command-line `remote-ssh update check` path can
still work, but the cheap login-time check may stop refreshing until the lock is
removed manually.

Suggested order:

1. Add a targeted test that pre-creates an old lock directory and proves the
   desired recovery behavior.
2. Define a conservative stale-lock policy based on lock directory age or a
   pid marker.
3. Keep the hook non-blocking and silent on failure.

### 3. Bash preexec has no remote-ssh-specific disable toggle

Risk: medium

References:

- `shell/rc.d/05-bash-preexec.sh:5-12` restricts loading to interactive Bash.
- `shell/rc.d/05-bash-preexec.sh:14-26` sources
  `tools/vendors/bash-preexec.sh` whenever the vendored file exists and
  `bash_preexec_imported` is not already set.
- `shell/rc.d/23-atuin.sh:37-40` has a disable toggle for Atuin itself, but
  that toggle does not prevent preexec from loading.

The vendored file is intentionally outside refactor scope, but its integration
is still startup behavior. If preexec conflicts with a host shell setup, the
user currently needs to remove/patch the file or predefine implementation
details rather than set a documented `REMOTE_SSH_*` opt-out.

Suggested order:

1. Decide whether the project wants a documented preexec toggle separate from
   `REMOTE_SSH_ENABLE_ATUIN`.
2. Add an rc-flow test for the toggle before changing the hook.
3. Keep `tools/vendors/bash-preexec.sh` unchanged.

### 4. Root helper library mixes minimal runtime helpers with network and debug helpers

Risk: medium

References:

- `shell/env.sh:18-22` sources `lib/guards.sh` and `lib/helpers.sh` during
  shell startup.
- `tools/lib/env.sh:20-33` also sources root `lib/guards.sh`, `lib/log.sh`,
  and `lib/helpers.sh` for CLI/tool code.
- `lib/helpers.sh:7-69` contains minimal shell helpers used during startup.
- `lib/helpers.sh:71-83` defines `fetch_json`, which shells out to `curl` and
  knows GitHub token behavior.
- `lib/helpers.sh:85-97` defines `remote_atuin_debug`, which is
  shell-feature-specific debug output.

`fetch_json` and `remote_atuin_debug` are not executed at shell load time, so
this is not an immediate startup dependency bug. The ownership boundary is
unclear, though: a file loaded by the minimal shell path also exposes GitHub API
and Atuin debug helpers. This makes future dependency audits easier to get
wrong.

Suggested order:

1. Inventory current call sites before moving anything.
2. Keep `have`, `path_prepend`, `remote_source_*`, OS, and hostname helpers in
   the minimal shell helper surface.
3. Move or rename specialized helpers only with guide/test updates.

### 5. Loader libraries are repeatedly sourceable but do not consistently mark ownership

Risk: low

References:

- `shell/env.sh:18-27` sources root helpers and config loading on every
  `rcrc`.
- `shell/aliases.sh:5` exposes `rcrc='source "$REMOTE_SHELL_DIR/rc.sh"'`.
- `shell/config.lib.sh:14-20`, `shell/update-check.lib.sh:14-18`, and
  `shell/welcome.lib.sh:14-28` source their module sets without a shared
  load-once convention.
- `lib/guards.sh:20-45` already provides `load_once` and `init_lib`, but these
  helpers are not used by the shell loader libraries.

Repeated sourcing appears intentional and mostly safe today because functions
are redefined and config markers preserve ownership. The inconsistency still
adds cognitive cost and makes startup-cost refactors harder because each loader
has to be inspected independently.

Suggested order:

1. Do not add load-once guards blindly; some flows depend on reloading config.
2. First define which loaders should be idempotent reloaders versus one-time
   initialization files.
3. Add re-source tests around `rcrc` before changing loader behavior.

## Refactor Candidates

- Measure and reduce welcome startup work. The highest-payoff candidate is the
  module execution path: `08-welcome.sh`, `welcome/runner.sh`, bundled
  `welcome.d` modules, and `welcome/commands.sh`.
- Keep update-check cheap but make lock handling recoverable. The hook already
  has interactive guards, stale checks, cache files, and background execution;
  stale-lock recovery is the missing piece.
- Add an explicit preexec opt-out if the project wants all interactive startup
  hooks to be controllable through documented `REMOTE_SSH_*` variables.
- Clarify root helper ownership by separating minimal shell helpers from
  GitHub/API and feature-specific debug helpers.
- Consolidate duplicate tiny parsing/toggle helpers only after ownership is
  clear. Examples include `remote_ssh_config_trim` in
  `shell/config/parse.sh:3-9`, `remote_ssh_welcome_trim` in
  `shell/welcome/base.sh:35-41`, welcome boolean handling in
  `shell/welcome/toggles.sh:3-14`, and update-check boolean handling in
  `shell/update-check/toggle.sh:3-8`.

## Risk

| Area | Risk | Why |
| --- | --- | --- |
| Welcome startup path | high | It runs during every default interactive shell and crosses from shell modules into tool status checks. |
| Update-check lock handling | medium | Failure mode is silent and persistent, but limited to informational login-time refreshes. |
| Bash preexec integration | medium | Vendored hook integration affects interactive Bash globally and lacks a documented project toggle. |
| Root helper ownership | medium | No immediate load-time bug, but mixed helper ownership can hide future dependency creep. |
| Loader idempotency | low | Current behavior is mostly safe, but unclear reload semantics make refactors riskier. |
| Config loader | low | It has a clear env-over-config precedence and existing tests around owned values. |
| Optional helpers such as `ssh-pick`, `bssh`, `log`, `fzf`, `navi`, `yazi` | low | Dependencies are mostly guarded or call-time, with explicit warning behavior where needed. |

## Test Coverage Needed

Existing useful coverage:

- `dev/tests/test_rc_flow.py` covers rc flow, noninteractive update-check
  skip, and background refresh behavior.
- `dev/tests/test_welcome.py` covers welcome ordering, issue propagation,
  config ownership, update cache rendering, host IP fallback, and sw status.
- `dev/tests/test_shell_helpers.py` covers line editing, editor/pager behavior,
  aliases, and vim alias behavior.
- `dev/tests/test_tool_init_shell.py` covers Starship, zoxide, Atuin, fzf
  history fallback, Atuin auto-import marker behavior, and bash-preexec loading.
- `dev/tests/test_bench_shell_startup.py` covers the shell startup benchmark
  harness and scenarios.
- `dev/tests/test_git_session_identity.py` covers Git session identity behavior
  and disablement.

Targeted tests to add before follow-up refactors:

- Welcome startup benchmark/reference test for any change that reduces module
  process count or status-lib loading.
- Welcome behavior tests preserving module ordering, executable-only modules,
  stdout/stderr handling, empty stdin, temp-file cleanup, user module opt-out,
  and issue propagation.
- Update-check rc-flow test for stale lock recovery.
- Bash-preexec opt-out test if a project-level toggle is introduced.
- Re-source/idempotency test for `rcrc` before adding load-once guards to
  shell loaders.
- Helper ownership tests or guide snapshot updates if `fetch_json` or
  `remote_atuin_debug` moves out of `lib/helpers.sh`.

No `just smoke` or `just test-assets-live` was run for this audit-only stage.

## Suggested Order

1. Add measurement and tests around the welcome startup path.
2. Fix update-check stale-lock behavior with a small, isolated change.
3. Decide and test the bash-preexec opt-out policy.
4. Clarify loader idempotency and `rcrc` expectations.
5. Split specialized helpers out of root `lib/helpers.sh` only after call-site
   inventory and guide/test updates.
6. Consolidate duplicate trim/boolean helpers last, if the earlier changes make
   ownership clear enough to justify it.
