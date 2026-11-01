# Atuin Integration Simplification Plan

Created: 2026-10-30
Status: implemented; awaiting independent audit

The current planning baseline includes an in-progress migration from fzf to
skim, including changes to Atuin integration tests. Use `20-skim.sh`, `sk`,
and the current test helpers as the implementation baseline. Preserve those
working-tree changes rather than restoring the earlier fzf integration.

Keep Atuin as the local history store while reducing remote-ssh's integration
code and startup work. Preserve shared history between sessions on one host and
search by directory, host, and exit status. Implement the four agreed changes:
select the history backend once per shell, use Ctrl-R as the only managed
Atuin search shortcut, disable automatic synchronization, and load
`bash-preexec` only when needed for the selected integration.

## Scope and behavior contract

- Keep Atuin pinned at `18.14.1`. Do not modify its vendored test fixture or
  `tools/vendors/bash-preexec.sh`, replace its recording hooks, or introduce
  runtime dependencies.
- Read `REMOTE_SSH_ENABLE_ATUIN` on the first interactive remote-ssh setup in
  each Bash process. Preserve its current default of enabled. Treat later
  `rcrc` calls as configuration reloads, not history-backend selection.
- Freeze the result even when Atuin is disabled, missing, or fails to start.
  Installing/removing the executable, changing PATH, or changing the toggle
  takes effect for backend selection in a new shell, not on `rcrc`.
- An active Atuin session remains active after `REMOTE_SSH_ENABLE_ATUIN=0;
  rcrc`; an existing fallback session remains on fallback after setting it to
  `1`. Repeated reloads must not duplicate hooks or rebind history keys.
- Keep fallback at initial setup: Bash history with skim Ctrl-R when available,
  otherwise native Readline history. Preserve explicit `HISTFILE` values,
  including an empty value and `/dev/null`.
- For an integration owned by remote-ssh, suppress Bash history-file writes
  only after Atuin setup succeeds. Reload must not restore `HISTFILE` behind
  the active recording hooks.
- Preserve Atuin already initialized independently by the user: do not
  initialize it again, change its history-file policy, or replace its keys.
  The single-shortcut policy applies to remote-ssh's own initialization.
- Keep automatic first-use history import and its existing toggle/marker.
  Removing import was not included in the approved scope.
- Keep the existing shell configuration allowlist and installation profiles.
  Atuin's enable switch remains an environment setting in this change.

The freeze covers remote-ssh's backend and binding setup. It does not prevent
the user from manually changing bindings or Atuin from reading its own config.
Manual `atuin sync` remains possible; credentials and existing databases stay
untouched. There is no new daemon configuration in this change.

## Current boundaries and required changes

| File | Current behavior | Planned change |
| --- | --- | --- |
| `shell/rc.d/05-bash-preexec.sh` | Loads the vendor library for interactive Bash regardless of the Atuin toggle or executable. | Capture the initial request and load only for an eligible Atuin startup; skip subsequent reloads and independently initialized Atuin. |
| `shell/rc.d/06-bash-history.sh` | Calls `remote_history_use_bash` on every source, restoring `HISTFILE` previously suppressed for Atuin. | Prepare fallback once and preserve the committed backend's history policy on reload. |
| `shell/rc.d/20-skim.sh` | Determines key ownership using availability, live toggle values, and Atuin lifecycle flags. | Use the frozen startup result; initialize the fallback key once after that result is known. |
| `shell/rc.d/23-atuin.sh` | Initializes, detaches, reattaches, restores arrow bindings, and completes detached history entries. | Initialize once, install only the agreed keys, and keep a small startup-failure rollback. Remove runtime switching machinery. |
| `dots/atuin/config.toml` | `auto_sync = true`; update checks already disabled. | Set `auto_sync = false`; remove settings used only by the abandoned up-arrow search. |
| `docs/shell/helpers.md`, `shell/rc.d/README.md` | Describe live switching and old key behavior; the module README also has stale history/import guidance. | Document the new contract consistently and correct the stale guidance. |

Configuration is loaded by `shell/env.sh` before the sorted `rc.d` files.
Preserve the early preexec setup before Starship initialization. Do not simply
move preexec loading into `23-atuin.sh`: prompt integrations may already have
selected how they cooperate with it by then.

## Stage 1: freeze the startup decision and make history reload-safe

Use a small, unexported process-local state: the initial request/eligibility,
whether setup has finished, and the final backend (`atuin`, `bash`, or
`external`). The final decision is committed only after setup or fallback is
complete. A new interactive child Bash must make its own decision rather than
inheriting a completed initialization flag. Avoid a general lifecycle framework.

1. In `05-bash-preexec.sh`, check interactive Bash, prior selection, external
   Atuin initialization, the captured enable setting, and executable
   availability. Use executable lookup that ignores aliases/functions, as the
   existing Atuin initialization intends. Reuse an already loaded preexec
   library without sourcing it twice; never unload a user's library.
2. Load the vendor library only for an eligible Atuin attempt. Missing or
   unreadable vendor code selects startup fallback. A later failure of
   `atuin init` may leave the library loaded; do not add an unload protocol.
3. Make `06-bash-history.sh` respect completed selection. On first setup,
   preserve the user's fallback `HISTFILE`; on subsequent sources, do not
   restore a file suppressed by the active Atuin integration. Keep normal
   in-memory Bash history available.
4. In `23-atuin.sh`, attempt initialization at most once. Success selects
   Atuin and suppresses file writes; failure selects Bash and preserves the
   fallback file. Validate the expected helpers from the pinned integration,
   rather than accepting empty output or a successful `eval` alone.
5. Finalize key ownership only after the result is known. Do not provisionally
   bind skim and then restore it during a normal successful Atuin startup.
6. On later `rcrc`, return before availability probing, initialization,
   backend changes, history-key binding, or repeated import checks.

Keep a bounded rollback for failed first initialization: remove newly added
Atuin registrations and restore only keys touched by that attempt, while
preserving pre-existing user hooks and bindings. Record ownership so a partial
upstream initialization guard is not mistaken for externally owned Atuin.
This rollback is distinct from the live detach/reattach feature being removed.

## Stage 2: make Ctrl-R the single managed search shortcut

The pinned Bash integration binds `/` in `vi-command` when its default Ctrl-R
bindings are enabled. Therefore `--disable-up-arrow` alone does not satisfy the
single-shortcut contract.

1. Initialize with both `--disable-up-arrow` and `--disable-ctrl-r`.
2. Use the pinned integration's `atuin-bind` helper to bind only:
   - Ctrl-R in the `emacs` map to `atuin-search-emacs`;
   - Ctrl-R in the `vi-insert` map to `atuin-search-viins`.
3. Preserve Up (`\e[A` and `\eOA`), vi-command `k` and `/`, and the existing
   vi-command Ctrl-R redo action. In vi mode the picker is available from
   insert mode; do not silently replace redo in command mode.
4. Respect an explicit user `ATUIN_NOBIND` opt-out. It suppresses our managed
   bindings as well, while history recording can remain enabled.
5. Keep fallback skim Ctrl-R in the same intended editable maps, without
   taking vi-command redo or external Atuin bindings. Once selected, reload
   must not overwrite later user edits to these keys.

The upstream integration may install internal dispatch macros even with its
default search bindings disabled. Preserve that unmodified implementation;
test the user-facing key contract instead of claiming zero internal bindings.

## Stage 3: delete the abandoned lifecycle and change sync default

After the new startup/reload tests cover the replacement behavior:

- Delete owned live detach/reattach, pending-entry tokens, temporary prompt
  prologues, cached-prologue compatibility, callback-pipeline restoration,
  arrow-key snapshots/restoration, and their obsolete state variables.
- Keep normal Atuin preexec/precmd recording unchanged. An entry containing
  `rcrc` finishes through the ordinary upstream hook at the next prompt,
  including its actual exit status; no detached completion is needed.
- Keep only startup lookup/validation, initial fallback, bounded failed-init
  rollback, external-ownership handling, the setup guard, and auto-import.
- Set `auto_sync = false` in the bundled Atuin config. Keep
  `update_check = false`, current paths, fuzzy search, preview, and
  `enter_accept = false`. Remove `filter_mode_shell_up_key_binding`,
  `search_mode_shell_up_key_binding`, and `inline_height_shell_up_key_binding`.
  Drop the now-unused `sync_frequency` setting to make the local default clear.

Do not add a custom Atuin build or try to disable duration collection inside
upstream hooks. These changes reduce our integration and startup work; they
do not remove the core per-command Atuin recording cost or shrink its binary.

## Tests and acceptance criteria

Use subprocess tests for initial selection and real PTYs for prompt completion
and actual keypresses. Reuse the unmodified offline Atuin 18.14.1 fixture and
`dev/tests/pty_shell.py`. The current fixture CLI supplies a constant history
ID: adapt the fake CLI to issue distinct IDs before asserting that a command
was completed exactly once. Keep asynchronous history-end checks bounded.

| Area | Required evidence |
| --- | --- |
| Initial selection | Enabled/working Atuin; disabled; missing binary; alias/function without binary; missing/unreadable preexec; failing/empty/partially failing init. Fallback remains usable and the attempt is not repeated. |
| Conditional loading | Disabled/missing/external Atuin does not cause our loader to source the vendor library. Existing preexec is retained. Noninteractive sources install no hooks. |
| Reload freeze | Changing the toggle, PATH, or binary availability in either direction does not change the selected backend after repeated full `rcrc` calls. A fresh shell sees the changed inputs. |
| History ownership | Active Atuin keeps `HISTFILE` suppressed across reload; fallback preserves default/custom/empty/`/dev/null` choices. No history files or database are migrated or truncated by our setup. |
| Recording | Successful and failed commands, directory changes, multiline input, and commands containing `rcrc` retain normal upstream start/end pairing and exit status. User prompt callbacks still receive the expected status and pipeline information. |
| Keys | PTY Ctrl-R invokes Atuin in Emacs and vi insert modes; fallback invokes skim. Up, `k`, `/`, vi-command redo, user key edits after setup, and external bindings remain intact. Honor `ATUIN_NOBIND`. |
| External ownership | An independently initialized Atuin is neither reinitialized nor replaced by skim, even when our toggle is off. Preserve its hooks and history-file policy. |
| Surrounding prompt setup | Full rc startup/reload with representative Starship and Zoxide hooks does not duplicate Atuin callbacks or corrupt status delivery. |
| Configuration/import | Assert the bundled sync default is false. Retain import-once, disabled-import, and retry-on-a-new-shell-after-import-failure coverage. |

Update existing test modules by behavior, not by preserving their old names:

- `test_history_backend.py`: replace automatic live removal/reactivation
  expectations with frozen backend and new-shell selection tests; retain
  executable lookup and `HISTFILE` cases.
- `test_atuin_lifecycle.py`: retain the fixture/hash check, normal recording,
  external ownership, failed initialization, and PTY bindings. Replace
  detach/reattach and arrow restoration tests with startup-only tests.
- `test_atuin_ownership.py`: retain startup failure, external ownership, and
  active reload entry-completion tests; remove detached-entry scenarios.
- `test_atuin_prompt.py`: retain meaningful ordinary prompt/status regressions
  adapted to reload without detaching. Remove tests solely for deleted pending
  prologues, stale tokens, and compatibility replay.
- `test_tool_init_shell.py`: update fakes to implement the pinned helper
  contract, assert both disable flags, retain auto-import tests, and cover the
  revised fallback decision timing.

Keep Bash 3.2 compatibility. Exercise available modern Bash as well, including
the vendor library's DEBUG and Bash 5.3+ PS0 paths when those versions are
available. Report missing interpreter coverage rather than inferring it passed.
`shell/rc.sh` is Bash-only; do not expand this task into a Zsh redesign. Preserve
any existing direct-module Zsh tests unless an explicitly scoped change needs
to adjust them.

Run the focused history/init tests during implementation, then `just smoke`
as the required final verification. Do not run `just test-assets-live`.

## Documentation and rollout

Update `docs/shell/helpers.md` and `shell/rc.d/README.md` together. Explain:

- `REMOTE_SSH_ENABLE_ATUIN=0 remote-ssh shell` selects fallback for a new shell;
  later toggle changes and `rcrc` do not switch history ownership.
- Ctrl-R opens Atuin in insert mode; normal Up and vi-command navigation stay
  available. Explicitly describe the externally initialized Atuin exception.
- Initial absence/failure uses Bash/skim. Removing or breaking Atuin after a
  successful startup does not trigger automatic failover, so start a new shell
  promptly in that situation; recording may fail in the old one.
- Automatic sync is disabled, with manual sync still available. Existing local
  history, import markers, credentials, and database locations are preserved.
- Existing shells running the old integration must be exited and reopened
  after this update. Do not support migrating their old pending callbacks with
  `rcrc`; retaining that compatibility would preserve the machinery being cut.

Keep historical audit reports as evidence of their original snapshots. Link
this follow-up from the audit plan. The separate proposed Flyline integration
must use the final startup-only history contract if implemented later; do not
edit or implement that separate proposal as part of this change.

## Performance evidence and completion

Before implementation, record the current source state and capture a local
startup baseline with the existing `just bench-shell` tooling in isolated
HOME/XDG directories. Compare the same controlled inputs before and after:
Atuin disabled, binary absent, working Atuin with import marker preseeded, and
the separately identified first-use import case. Fix PATH/tool versions and
control welcome/update hooks, database contents, and cache state. Use a
developer-only isolated wrapper when environment overrides are needed; do not
change the benchmark's public scenarios for this feature.

Startup fixture tests establish behavior, not real Atuin performance. Use a
real pinned binary when locally available for performance measurements; report
its absence as a measurement limitation. Retain raw samples and source
fingerprints, and compare distributions on the same host without a universal
millisecond threshold. Keep measurements out of the user's actual history and
credentials. If measuring per-command latency, report it separately from
startup; fewer lines of shell do not by themselves prove faster recording.

Implementation is complete when the four agreed behaviors, retained recording
features, offline regression tests, required `just smoke`, and updated docs are
all delivered. Report the removed lifecycle code and observed startup changes
without promising a particular speedup. Do not stage or commit unrelated work.

## References

- [Pinned Atuin Bash integration](https://github.com/atuinsh/atuin/blob/v18.14.1/crates/atuin/src/shell/atuin.bash)
- [Atuin key binding configuration](https://docs.atuin.sh/latest/configuration/key-binding)
- [Atuin configuration, including auto_sync](https://docs.atuin.sh/latest/configuration/config)
- [bash-preexec documentation](https://github.com/rcaloras/bash-preexec)
- [Existing shell startup benchmark](bench-shell.md)

Use the tagged source and offline fixture to validate the pinned API; current
online documentation can describe behavior added after 18.14.1.


## Implementation notes

The implementation defers the pinned initializer's `bind` writes in a local
queue until eval and helper/hook validation succeed. Read queries use builtin
Readline behavior; an existing `bind` function is restored before application.
The queue is preflighted in an inherited subshell keymap, so deterministic
application errors also leave the parent's keys untouched, including unknown
Bash 3.2 `bind -x` commands. No second eval of upstream integration is needed.

A transient failure during the subsequent parent replay is best-effort:
callbacks and HISTFILE are restored, but already overwritten shell bindings
cannot always be recovered on Bash 3.2. Skim reclaims editable Ctrl-R when
available; without skim a partially applied managed Ctrl-R could remain. Up,
`k`, `/`, and vi-command redo are never requested. This boundary is explicit
for independent audit. This queue is scoped to 18.14.1 startup, not a general
shell transaction or reload protocol. Normal successful startup does not
snapshot or restore arrow bindings. See [measurements](atuin-measurements/README.md)
for isolated startup evidence and source fingerprints.

The full real 18.14.1 CLI initializer appends an AI `?` binding outside the
vendored `atuin.bash` source. Its local `atuin init --help` supports
`--disable-ai`; implementation also passes this flag to preserve the agreed
single-shortcut behavior. The unmodified offline fixture alone cannot cover
this generated CLI suffix. The isolated real-binary recording check explicitly
preserves `?` and exercises commands containing `$?`.
