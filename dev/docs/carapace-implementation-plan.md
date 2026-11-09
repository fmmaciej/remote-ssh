# Carapace Completion Integration Plan

Created: 2026-11-08
Revision: R1; compatibility contract with the planned Flyline editor
Status: planned; implementation not started

Add optional command/argument completion to the existing Bash/Readline session
using one Carapace provider. Preserve vi, fast ordinary typing, and the existing
Atuin/skim integration. Users do not maintain a command-to-provider map.

The [completion pilot](completion-provider-pilot.md) found all 11 tested
candidate cases working with Carapace 1.8.2. Its ordinary key latency was the
same as Readline's; the work occurred on completion requests. These macOS
results are evidence for the approach, not a performance promise for weak
Linux hosts. The earlier [Flyline pilot](flyline-pilot-record.md) remains
historical. The [updated Flyline plan](flyline-implementation-plan.md) targets
latest stable 1.10.0 plus Vim PR #974. Carapace remains the one optional provider
with either editor; neither feature automatically activates the other.

## Decisions and scope

- Keep Bash/Readline as the default editor and preserve existing vi behavior.
  Editor replacement belongs to the independent Flyline plan. This provider
  feature does not itself add an editor, highlighting, or a different shell.
- Carapace is the single added completion provider. Do not add argc, flycomp,
  bash-completion, GNU awk, fzf, or other shells as dependencies.
- Installation and activation are separate. Proposed setting:
  `REMOTE_SSH_ENABLE_CARAPACE=0` by default; `1` requests activation. Add it to
  the existing configuration allowlist; environment values take precedence.
- Keep Carapace out of `MINI_TOOLS`, `QUICK_TOOLS`, `DEFAULT_TOOLS`, and
  `RUNME_TOOLS` initially. Installation uses the ordinary tool CLI and exact
  GitHub release manifest. No package manager or source build on remote hosts.
- Initial interactive integration targets Bash >= 4.4. Older Bash keeps its
  ordinary completion and vi behavior; management/installation remains Bash
  3.2 compatible. Do not upgrade Bash automatically.
- Complete command names through Bash's existing PATH completion. Use Carapace
  for arguments of commands reaching the default completion handler.
- Preserve existing specific completions, notably the zoxide/skim `z`
  integration, and later user/host overrides. This is a generic ownership rule,
  not a per-command list of alternative providers.
- No Carapace execution, completion discovery, network calls, or generated-code
  evaluation during shell startup, reload, ordinary typing, or prompt rendering.
  Execute Carapace only when the user requests completion.

Proposed use after implementation, not functionality available today:

```bash
remote-ssh tool install carapace
REMOTE_SSH_ENABLE_CARAPACE=1 remote-ssh shell
```

For persistence, add the setting to the existing remote-ssh config. Explain
that `tool install` does not select the maintained expected-tool set: users
wanting Carapace maintained by update/reinstall also retain their existing
entries and add `carapace` to `expected-tools`. Do not change those CLI semantics
or replace that user configuration as part of this feature.

## Proposed runtime design

Use a small namespaced Bash adapter and one default completion registration,
`complete -D`, rather than registering a different callback for every command.
Derive its candidate handling from the pinned upstream Bash callback. The
adapter calls the selected executable with Carapace's Bash completion protocol
using the current command line and completion context.

The hook defines/registers the adapter using Bash builtins. Its first actual
Carapace request occurs on Tab. Later requests use the same adapter; there is
no per-command initialization process, manually maintained command map, or
generated initialization cache. This is a simpler startup strategy than the
three command-specific initializations measured in the pilot.

### Stage 0: verify this adapter before wiring it into rc.sh

The pilot tested upstream command-specific callbacks. It did **not** test the
new default-handler integration. First prove the following in isolated PTYs:

1. The pinned Bash protocol can serve one generic callback for `git`, `rg`, and
   `fd`, including the entire 11-case fixture suite, quoted paths, incomplete
   quotes, and repeated requests. Reuse upstream token handling; do not create
   a general shell parser or a custom completion UI.
2. `complete -D` dispatch works in Emacs and vi insert modes without rebinding
   Tab or changing Readline settings. Bash's command-name/file completion
   remains available for unsupported commands, including paths containing spaces
   under the adapter's quoting options.
3. Missing/unsupported commands, valid requests returning no candidates,
   unavailable executable, and provider failure are distinguishable enough to
   fall back without inserting errors or status messages into the command.
   Never cache an empty candidate list as proof that a command is unsupported.
4. Set `CARAPACE_BRIDGES` to empty in the child invocation to keep this adapter
   on built-in/native Carapace completers. Verify that empty means no implicit
   shell bridges for this release. Do not change the parent environment or
   discover/install zsh, fish, bash-completion, or inshellisense implicitly.
5. Confirm the callback's metadata/helper requirements for aliases, functions,
   nested commands such as `sudo git`, shell variables, and cursor positions
   before the end of a line. Record supported behavior and limitations. Do not
   copy unrelated global helpers into the session without establishing a need.

If this design cannot pass the pinned-protocol/default-handler controls, stop
with a short implementation finding before shipping it. Do not silently switch
to eager all-command initialization, introduce another provider, or claim that
the earlier command-specific pilot validated this adapter.

### Startup and ownership

Proposed entrypoint: `shell/rc.d/27-carapace.sh`, after existing tool bindings.
Put nontrivial private functions below `shell/carapace/` if needed; avoid a
general completion framework. The hook:

1. Checks interactive Bash, the toggle, supported Bash features, and executable
   availability before making any registration. These are local checks; do not
   execute `carapace --version` on startup.
2. Resolves a real executable from PATH rather than invoking an alias or shell
   function. Respect the normal managed PATH and custom installation directory.
   Accept a system Carapace only when explicitly enabled, with a documented
   compatibility limit; the supported candidate is the pinned release.
3. Checks the existing default completion registration. If another owner
   already has one, leave it intact and record an inactive/conflict reason.
   Do not chain unknown completion frameworks or overwrite their handlers.
4. Registers one owned default callback and suitable Bash fallback options.
   Do not touch explicit per-command registrations, `complete -E`/`-I`,
   keymaps, `PROMPT_COMMAND`, DEBUG traps, or history hooks.

Use names prefixed with `_remote_ssh_carapace_` and process-local ownership
state. Expose actual session status/reasons through a small shell diagnostic
function, following the existing `remote_atuin_debug` pattern; guide/docs explain
how to invoke it. A separately launched guide process must not claim to inspect
its parent's unexported completion state. Avoid routine startup chatter.
If the executable disappears, completion must retain
Bash fallback behavior. New shells pick up a changed installation; do not add
automatic live upgrades or a version probe on every completion.

### Reload and disable

Handle `rcrc` as reconciliation, not unconditional reinitialization:

- Enabled and still owned: preserve the existing registration and functions.
- Disabled: remove only the exact default registration owned by this feature.
  Do not remove a registration the user has replaced after activation.
- Existing foreign default: remain inactive until the conflict is removed and
  the user reloads; expose the reason rather than taking ownership.
- The config loader's existing reset/environment-precedence rules also apply
  to the new toggle, including config disable/re-enable and repeated reloads.

Keep ownership state local to the Bash process. Do not export initialization
markers that would cause a nested Bash to skip its own setup. Atuin's selected
history backend and user modifications to its bindings remain untouched.

### Completion requests and failure behavior

Keep work synchronous with the requested Tab; no background daemon, automatic
suggestions, or background completion. A callback may run local commands and,
depending on the completer, contact external services. Document that dynamic
completion can therefore be slower than a static flag list. Startup itself
must remain local-only.

Handle argument quoting and the upstream spacing/noquote protocol correctly;
keep candidate values separate, preserve exit status handling, and clear
`COMPREPLY` for each request. Limit exported completion context to the provider
call rather than leaving `COMP_*` or Carapace metadata in unrelated children.
On failure, clear partial candidates and use Bash fallback. Do not install
anything, fetch definitions, prompt for setup, or execute the entered command.

Do not promise zsh's menu UI, fuzzy selection, or descriptions in Bash.
Carapace supplies candidate knowledge; Readline remains the presentation and
editing layer.

## Tool definition and platform support

Use Carapace Bin `v1.8.2` / `1.8.2` as the initial pinned candidate already
measured. Its upstream executable is `carapace`. Generate the definition with:

```bash
tools/generate-def.sh carapace-sh/carapace-bin --tool carapace --tag v1.8.2
```

Expected candidate release archives from the inspected metadata:

- `carapace-bin_1.8.2_linux_amd64.tar.gz`
- `carapace-bin_1.8.2_linux_arm64.tar.gz`
- `carapace-bin_1.8.2_darwin_amd64.tar.gz`
- `carapace-bin_1.8.2_darwin_arm64.tar.gz`

Confirm archive members, exact executable path, official SHA-256 digests,
dependencies, and Linux libc compatibility before declaring ASSETS selectors.
Do not label Linux archives `any` or `musl` merely because they are Go builds.
Follow existing platform preference and unsupported-platform reporting. Other
architectures/Termux are outside the first support set.

Use the existing single-binary staged installer, release ownership, active
symlinks, expected-tools handling, update, checks, and prune. No installer layout
extension, tool-specific post-install executable generation, runtime GitHub API,
or new management command is needed. A failed update/reinstall retains the
working binary. Ordinary installation checks remain separate from whether
completion is active in an interactive shell.

## Planned files and responsibilities

| Area | Planned change |
| --- | --- |
| `tools/defs/carapace.sh` | Pinned assets/checksums using the existing binary layout. |
| `shell/rc.d/27-carapace.sh`, optional `shell/carapace/` modules | Toggle, guards, namespaced callback, default completion ownership and reload cleanup. |
| `shell/config/entries.sh` | Allowlisted toggle, default `0`. |
| `tools/lib/commands/guide/` where needed | Existing config rendering exposes the setting; guide instructions point to the in-session diagnostic function for actual state. |
| `dev/tests/test_tool_assets.py` | Exact manifest/platform/checksum expectations. |
| New `dev/tests/test_carapace_shell.py` | Isolated subprocess/PTY acceptance, fake-provider counters/failures, ownership and fallback. |
| `dev/tests/test_config.py`, existing tool-init tests | Config precedence/reset, reload, history/skim/zoxide coexistence. |
| `docs/shell/completions.md`, `docs/shell.md`, `docs/shell/config.md`, `shell/rc.d/README.md` | User activation, requirements, defaults, limitations, disable/reload and troubleshooting. |
| `docs/tools.md`, `docs/install.md` where relevant | Optional tool installation and expected-set maintenance; no default-list changes. |
| `dev/README.md`, implementation record under `dev/docs/` | Plan, acceptance evidence, actual support matrix and measurements. |

The installer and several installer tests have unrelated worktree changes.
Re-read their current contracts before implementing; do not revert or combine
that work with this feature. Keep `bin/remote-ssh` a thin dispatcher and avoid
adding help text for an unimplemented subcommand.

## Validation and acceptance

### Offline subprocess and real PTY coverage

- Toggle off, missing executable, noninteractive shell, Bash 3.2: no provider
  invocation, completion/keymap changes, cache files, network, or warnings.
- Enabled supported Bash: zero provider executions while starting, typing,
  displaying prompts, or running `rcrc`; provider invoked on Tab only.
- All 11 pilot candidate cases via the generic callback, then genuine Tab
  checks for flags, values, paths with spaces, dynamic branches and modified
  tracked files. Verify inserted shell words, not just a substring in output.
- Unknown commands and provider failures fall back to files/directories;
  empty valid results do not poison later completions. Test repeated requests,
  quotes, nonzero status, empty output, and cursor-in-middle behavior.
- Existing default and command-specific owners are preserved. Test default
  replacement after activation, disable/re-enable, repeated `rcrc`, nested
  shells, and removal of the executable.
- vi insert/command modes, the `ac` to `bc` operation, undo/history keys, and
  Readline Tab behavior. Do not change Tab bindings to make a test pass.
- Atuin and Bash/skim history backends: Ctrl-R selection without execution,
  backend selected once per process, and preserved custom bindings on reload.
  Preserve the `z`/`zi` skim selection and navi's bounded private finder setup.
- Combined Flyline profile, once available: verify that its Tab UI invokes the
  same `complete -D` adapter, with no per-command provider map. Compare both
  editor/provider toggles independently. No Carapace process may be triggered
  by Flyline startup or automatic suggestions; missing default-handler support
  must be resolved in the editor integration before claiming combined support.
- Custom XDG/config/install paths, environment precedence, config resets, and
  installations supported on a platform where interactive activation is not.

Mocked providers exercise failure/counter contracts offline. Native tests with
the pinned executable validate its real protocol; fakes alone do not establish
integration correctness. Reuse the existing PTY testing helpers and isolate
HOME/history/environment in all native probes.

### Performance and support record

Compare the same remote-ssh session with the toggle off/on, randomized order,
at least 15 measured repetitions after warmup. Record startup to a usable
command, first and repeated Tab, ordinary single-key latency, shell RSS, and
transient provider memory separately. Include one static and one dynamic
request, both with required-candidate assertions.

The primary startup acceptance condition is **zero Carapace processes**, not
a transferred millisecond budget from the earlier Mac benchmark. Ordinary
typing must stay in Readline without a provider callback. Report first-Tab
cost explicitly; do not present warmed callback timing as the cold request.

Exercise an actual weak Linux host before presenting this as validated for
that environment. Record host resources, Bash, libc, artifact, tool versions,
and terminal/SSH context. If that host is unavailable during implementation,
mark it unverified and retain opt-in status; do not invent a support result or
silently broaden the default profiles. Test Linux glibc/musl and macOS rows
only where artifacts and execution evidence support them.

Run `just smoke` after implementation and appropriate targeted checks during
development. Do not run `just test-assets-live` without an explicit request.
Write `dev/docs/carapace-implementation-record.md` with results, unsupported
rows, benchmark source/input hashes, and any remaining limitations.

## Delivery order

1. Validate the generic/default callback in isolation and record the Stage 0
   result. Confirm the candidate assets and Bash/platform requirements.
2. Add the normal optional tool definition and offline manifest tests.
3. Add the disabled-by-default hook, config toggle, ownership/reload behavior,
   and targeted subprocess/PTY tests in the same change.
4. Add guide/user docs and run native integration/performance acceptance.
5. Run the required checks and publish the implementation record. Keep the
   feature optional; any later default-profile inclusion is a separate decision.

## Planning evidence and checks

R0 is based on current configuration loading, vi/history/zoxide hooks, the
single-binary installer, and the linked completion pilot. A local 1.8.2 probe
confirmed that `carapace rg bash` emits a command-specific registration, while
an unknown command with empty bridges exits **0 with empty output**. Exit code
alone is therefore insufficient to detect successful initialization.

The upstream all-command initializer generated in the developer's normal
environment also contained an absolute user-specific Carapace bin path and
global helper functions. Do not check that raw output into the project or
source an initializer generated for a different user's environment. The
proposed adapter deliberately avoids that initialization path; its behavior
still requires Stage 0 validation.

Current upstream documentation was consulted through Context7. References:
[setup](https://carapace-sh.github.io/carapace-bin/setup.html),
[environment/bridges](https://carapace-sh.github.io/carapace-bin/setup/environment.html),
and [pinned release](https://github.com/carapace-sh/carapace-bin/releases/tag/v1.8.2).
This planning change adds documentation only; no integration tests or runtime
support are being claimed by publishing the plan.
