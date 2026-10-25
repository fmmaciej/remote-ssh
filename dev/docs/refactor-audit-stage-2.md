# Refactor Audit Stage 2: Public CLI And Commands

Date: 2026-06-01

This report audits the public CLI and command modules for refactor readiness.
It covers `bin/remote-ssh`, `tools/lib/commands.lib.sh`, and
`tools/lib/commands/`. It does not apply code changes.

## Findings

### 1. `remote-ssh guide --help` exits as a failure

Risk: low

References:

- `tools/lib/commands/guide.sh:30-33` prints usage for `-h|--help` and then
  returns `1`.
- `tools/lib/commands/git.sh:25-28`, `tools/lib/commands/tool.sh:93-95`, and
  `tools/lib/commands/scripts.sh:110-112` treat subcommand help as success.
- `tools/lib/commands/help.sh:5-9` treats the top-level help command as
  success when no extra arguments are passed.

This is a small but real CLI consistency issue. It makes `remote-ssh guide
--help` look like an error path even though it is a normal help request.

Suggested order:

1. Add a focused entrypoint test for `remote-ssh guide --help`.
2. Change only the help exit status.
3. Keep invalid guide sections and extra guide arguments returning failure.

### 2. Some status and doctor helpers force `errexit` on after probing

Risk: medium

References:

- `tools/lib/commands/ssh/status/agent.sh:16-19` runs `set +e`, captures
  `ssh-add -l`, and then runs `set -e`.
- `tools/lib/commands/ssh/status.sh:95-98` uses the same unconditional
  `set -e` restoration after `ssh -G`.
- `tools/lib/commands/git/status/model.sh:48-53` uses the same pattern around
  a network-capable SSH auth probe.
- `tools/lib/commands/doctor.sh:142-145` uses the same pattern around
  `remote_ssh_tool_status_load`.
- `tools/lib/commands/update/check.sh:184` and
  `tools/lib/commands/update/check.sh:218-227` preserve and restore the
  caller's original `errexit` state explicitly.

The public CLI enters through `bin/remote-ssh:3`, which enables `errexit`, so
normal command execution mostly masks this. The command functions are still
sourceable shell functions, and the unconditional restore can unexpectedly turn
`errexit` on for a caller that had it disabled. The update-check command already
has the safer pattern.

Suggested order:

1. Add shell subprocess tests that source the command libraries with `errexit`
   disabled and call the affected collectors.
2. Reuse the `update check` preservation pattern or extract a tiny local helper
   if the duplication becomes meaningful.
3. Keep the command output and exit statuses unchanged.

### 3. `ssh setup` rewrites `~/.ssh/config` non-atomically

Risk: medium

References:

- `tools/lib/commands/ssh/setup.sh:58-61` creates or touches the user's
  `~/.ssh/config`.
- `tools/lib/commands/ssh/setup.sh:67-75` builds a temp file and then writes it
  back with `cat "$tmp_ssh_config" >"$home_ssh_config"`.
- `dev/tests/test_ssh_command.py` covers include insertion and idempotency, but
  not interrupted or failed rewrites.

The command only adds the remote-ssh include once, and it already keeps the
managed config in a separate repo-owned file. The final rewrite of the user's
home SSH config is still not atomic, so an interrupted write can leave a partial
file.

Suggested order:

1. Add a test around preserving existing `~/.ssh/config` contents during setup.
2. Define the expected permission and ownership behavior for the rewritten
   file.
3. Replace the final write with an atomic temp-file move in a follow-up code
   change.

### 4. `remote-ssh prune` dry-run creates the install prefix

Risk: low

References:

- `tools/lib/commands/prune.sh:84-93` parses `--apply` but defaults to dry-run.
- `tools/lib/commands/prune.sh:95` runs `mkdir -p "$INSTALL_PREFIX"` before
  candidate discovery regardless of `--apply`.
- `tools/lib/commands/prune.sh:117-119` only removes releases when `--apply`
  is set.

The deletion boundary is conservative, but the dry-run command can still create
an install directory on a host that did not have one. That is a small mutation
in an otherwise informational flow.

Suggested order:

1. Decide whether dry-run should be strictly non-mutating or whether creating
   the prefix is acceptable.
2. If strict dry-run is desired, add a test for a missing install prefix.
3. Keep `--apply` deletion behavior unchanged.

### 5. Every CLI invocation eagerly loads all command facades

Risk: medium

References:

- `bin/remote-ssh:15-18` sources the tools environment and command library
  before command dispatch, including `remote-ssh --help`.
- `tools/lib/commands.lib.sh:21-34` sources every top-level command facade on
  every invocation.
- `tools/lib/commands/guide.sh:5-12`, `tools/lib/commands/git.sh:5-10`, and
  `tools/lib/commands/ssh.sh:5-12` source private command modules from their
  facades.
- `tools/lib/commands.lib.sh:8-18` already lazy-loads install libraries only
  when required, so a partial lazy-loading precedent exists.

This is not currently a functional bug, and most facades are light. The risk is
load-time coupling: a syntax or sourcing problem in an unrelated command can
break help, and future command modules can accidentally increase startup cost.

Suggested order:

1. Keep the current eager loading until command behavior is well covered.
2. If startup/help cost becomes a target, lazily source command facades by
   dispatch branch.
3. Preserve `bin/remote-ssh` as routing, usage, and bootstrap only.

## Refactor Candidates

- Normalize CLI help behavior across subcommands. The concrete issue is
  `guide --help`; broader cleanup should wait until tests cover each command's
  usage path.
- Standardize temporary `set +e` probing. `update check` has the clearest
  current preservation pattern; SSH, Git status, and doctor can converge on it.
- Keep mutation boundaries explicit in command modules. `update check` is a
  good model: `tools/lib/commands/update/check.sh:59-99` collects state through
  Git read operations and `git ls-remote`, while
  `tools/lib/commands/update.sh:36-38` keeps `pull --ff-only` and install work
  in the mutating `update` command.
- Extract tiny list/confirm/report helpers only after behavior tests are in
  place. Duplication exists in `tools/lib/commands/install.sh:20-48`,
  `tools/lib/commands/uninstall.sh:19-58`, and
  `tools/lib/commands/tool.sh:13-24`.
- Defer larger install/uninstall planning extraction to Stage 3. The public
  command files expose the repetition, but the install core owns most of the
  semantics.
- Consider a dispatch table for guide sections only if future guide sections
  keep expanding. `tools/lib/commands/guide.sh:18-38` is readable today, but it
  is already a manually repeated argument-count pattern.

## Risk

| Area | Risk | Why |
| --- | --- | --- |
| Help exit consistency | low | One public help path returns failure, but the fix is narrow and easy to test. |
| `errexit` preservation | medium | Normal CLI entry masks it, but sourced command functions can alter caller shell options. |
| SSH setup config rewrite | medium | It touches user-owned SSH config and should avoid partial writes. |
| Prune dry-run side effect | low | It does not delete anything, but it can still create the install prefix. |
| Eager command loading | medium | Mostly cheap today, but it couples unrelated commands and help paths at load time. |
| Update-check mutation boundary | low | The informational command uses read-only Git checks and cache writes only when requested. |
| Parser/list/confirm duplication | low | The duplication is visible but should not be collapsed before tests lock behavior down. |

## Test Coverage Needed

Existing useful coverage:

- `dev/tests/test_entrypoint.py` covers the root dispatcher, top-level help,
  unknown commands, guide routing, Git usage errors, check delegation, and tool
  list dispatch.
- `dev/tests/test_guide.py` covers guide section rendering and shell snapshot
  behavior.
- `dev/tests/test_scripts_command.py` covers the scripts command and the moved
  `scripts guide` flow.
- `dev/tests/test_ssh_command.py` covers SSH command routing, setup include
  behavior, idempotency, and status cases.
- `dev/tests/test_git_setup.py` and `dev/tests/test_git_status.py` cover Git
  setup and Git/SSH status reporting.
- `dev/tests/test_check.py`, `dev/tests/test_update.py`,
  `dev/tests/test_prune.py`, `dev/tests/test_uninstall.py`, and
  `dev/tests/test_doctor.py` cover the main public command behaviors touched by
  this stage.

Targeted tests to add before follow-up refactors:

- `remote-ssh guide --help` should exit `0` and keep invalid guide usage
  exiting non-zero.
- Sourced command collectors should preserve the caller's original `errexit`
  state.
- `ssh setup` should preserve existing home SSH config contents across the
  rewrite path and, if changed, use an atomic final replacement.
- `remote-ssh prune` should either document current dry-run directory creation
  or test that dry-run does not create the install prefix after the behavior is
  changed.
- Any lazy command loading change should include help/usage smoke tests for
  every public subcommand.
- Any shared list/confirm/parser extraction should preserve install,
  uninstall, tool list, and update/check output exactly enough for the existing
  subprocess tests to catch regressions.

No `just smoke` or `just test-assets-live` was run for this audit-only stage.

## Suggested Order

1. Fix `guide --help` exit status with a single targeted entrypoint test.
2. Preserve caller `errexit` around SSH, Git status, and doctor probes.
3. Make `ssh setup` home config rewriting atomic after tests cover existing
   contents and idempotency.
4. Decide the intended `prune` dry-run mutation contract and test it.
5. Extract shared list/confirm/report helpers only where tests already pin
   behavior.
6. Consider lazy-loading command facades last, after public command help and
   dispatch tests are broad enough.
