# Flyline Integration Plan

Created: 2026-10-30
Status: proposed; planning only, implementation not started

Add Flyline as an optional editor for interactive `remote-ssh shell` sessions.
The intended benefit is syntax highlighting, inline suggestions, and a completion
menu while retaining Bash. Installation and activation are separate choices.
Ship an initial supported integration only after the compatibility pilot below.

## Scope and initial decisions

- Keep the existing Readline session as the default. Proposed switch:
  `REMOTE_SSH_ENABLE_FLYLINE=0` by default, `1` to request activation. Add it to
  the existing shell configuration allowlist, with environment precedence.
- Keep Flyline out of `MINI_TOOLS`, `QUICK_TOOLS`, `DEFAULT_TOOLS`, and
  `RUNME_TOOLS`. Users explicitly select it through the existing install CLI.
- Keep Atuin installed and its history intact. Adding an editor does not select
  a new history store or migrate data. Preserve the existing Atuin toggle.
- Reuse available Bash completion functions. Do not add Carapace, flycomp,
  a system-wide completion framework, or automatic completion generation in
  this change. Measure actual completion gaps before planning those additions.
- Enable highlighting and basic completion first. Disable mouse capture,
  decorative animations, agent setup, and automatic flycomp prompts using the
  selected release's documented settings. Use the terminal cursor initially.
- Do not edit startup files, change the default shell, install another Bash,
  execute the upstream installer, or build anything on remote hosts.
- Keep ordinary installation and all management commands working under Bash
  3.2. Unsupported interactive Bash builds retain Readline.

Planned use after implementation, not commands available today:

```bash
remote-ssh tool install flyline
REMOTE_SSH_ENABLE_FLYLINE=1 remote-ssh shell
```

## Current integration boundaries

| Area | Current behavior | Required change |
| --- | --- | --- |
| [Shell launcher](../../tools/lib/commands/shell.sh) | Selects Bash from PATH and launches it with `--rcfile`. | Preserve selection; do not silently switch Bash to satisfy Flyline. |
| [Line editing](../../shell/rc.d/11-line-editing.sh) | Enables vi mode. | Establish whether the pinned Flyline can preserve the required editing behavior. |
| [Atuin](../../shell/rc.d/23-atuin.sh) | Owns history hooks and selected Readline bindings; requires `bash-preexec`. | Keep recording intact and adapt editor-specific bindings explicitly. |
| [fzf](../../shell/rc.d/20-fzf.sh) | Supplies a custom history widget when Atuin is inactive. | Keep the Readline fallback; choose one Ctrl-R owner when Flyline is active. |
| [Installer](../../tools/lib/install-tool/install.sh) | Installs an executable or bundle and publishes executable links. | Represent a Bash library without pretending it is a command in PATH. |
| [Release records](../../tools/lib/common/release.sh) | Identify owned executable releases. | Identify and protect library releases as well, preserving old records. |
| [Platform selection](../../tools/lib/install-tool/assets.sh) | Prefers musl executable assets on glibc Linux. | A loaded library must match the host Bash/libc ABI; do not reuse that preference blindly. |
| [Tool inventory](../../tools/lib/install/tool_inventory.sh) and [status](../../tools/lib/commands/tool_status.sh) | Check executable links in `INSTALL_BIN_DIR`. | Report library installation separately from session activation. |

The planning baseline contains unrelated work on inventory, ownership,
uninstall, and reporting. Re-read the resulting code before implementation;
do not replace those changes with the older behavior described in an audit.

## Stage 0: establish feasibility with a pinned release

Use upstream `v1.9.0` as the research candidate, not a promise that it is the
latest release. Its tagged installer distinguishes Bash before/after 4.4,
Linux libc variants, and native library names on macOS. A version check alone
does not prove that a Bash build exports the symbols needed for loading.

Before runtime changes:

1. Record the selected tag, commit, exact release asset names, archive contents,
   and SHA-256 values. Confirm all settings and integration APIs against that
   tag; current `master` examples may refer to newer Atuin or Flyline APIs.
2. Download candidate artifacts into an isolated developer directory. Inspect
   dependencies and test loading in disposable Bash subprocesses and PTYs.
   Do not run the upstream installer or modify the developer's shell files.
3. Test the current vi workflow: Escape, insert/command modes, movement,
   deletion, undo, history navigation, and return to insert mode. `set -o vi`
   alone is not evidence that a replacement editor implements it.
4. Exercise the pinned Atuin 18.14.1, bash-preexec, Starship, and local history
   fallback with that editor. Verify prompt hooks, exit status, and duration.
5. Record a support table with Bash executable/version, OS, architecture,
   libc, artifact, load result, vi result, and PTY result. Mark untested rows
   unverified; do not infer compatibility from an asset's name.

Initial candidates are Linux glibc x86_64/aarch64 and macOS x86_64/aarch64 with
a compatible modern Bash. Use the normal Bash >= 4.4 artifact family for the
first integration. Bash < 4.4 remains on Readline even where upstream offers
legacy builds; system macOS Bash must not be upgraded by this project. Add
Linux musl only after validating its library with the target Bash build.

**Exit condition:** at least one supported platform has a reproducible real
PTY demonstration, with an explicit result for vi editing. If vi is missing,
stop at the pilot report and resolve the editing-mode contract before shipping
the integration. Do not silently turn vi users into Emacs-mode users.

Deliver a short `dev/docs/flyline-pilot-record.md` with source fingerprints,
test transcripts, unsupported combinations, and the resulting decisions.
This planning task does not perform the pilot or claim these checks passed.

## Stage 1: install and manage a library release

Implement this as a small, explicit extension of managed tool installation,
not a general plugin framework or a fake executable wrapper.

Proposed storage contract to finalize using the Stage 0 archive inventory:

- Add an installation layout such as `bash-builtin`, retaining existing
  `binary` and `bundle` behavior. Declare the exact library member for each
  asset in a manifest mapping, analogous to bundle roots. Do not discover it
  at runtime through filename guessing or GitHub API calls.
- Keep versioned releases as direct children of `INSTALL_PREFIX`. Publish an
  absolute active-file symlink at `$INSTALL_PREFIX/.active/flyline`, pointing
  at the declared library inside its release. Do not place a shared library
  or an executable named `flyline` in `INSTALL_BIN_DIR`.
- Validate a library as a readable regular file contained in the staged
  release. An executable permission bit is not the library contract. Validate
  paths and ownership as strictly as for existing managed releases.
- Introduce a versioned library ownership record containing tool, version,
  layout, and library path. Continue reading existing format-1 executable
  records without rewriting them. Reject unknown or malformed records for
  deletion and automatic loading.
- Download, verify, extract, validate, and stage before switching the active
  link. A failed download, checksum, load probe, or link switch must preserve
  the previous release. Do not overwrite a mapped library file in place.
- Probe the candidate in a disposable instance of the Bash selected from PATH
  before publishing it; the probe must exit and must not initialize user files.
  Capability failures get a clear diagnostic. A later change of Bash still
  requires runtime guards and may make an installed library unusable.
- Teach install/reinstall, expected-tools handling, update, list, check,
  doctor, uninstall, and prune about this layout in the same delivery unit.
  `command -v flyline` is not a valid installation check.
- Prune must inspect active library links in addition to executable links,
  protect active releases, and abort deletion if active-link enumeration fails.
  Unknown files and directories remain protected. Do not attempt to inspect
  other processes or unload libraries from open shells.
- Updates take effect in a new shell. Existing sessions retain their loaded
  code; do not promise a live upgrade or force a library reload during update.
- Support custom `INSTALL_PREFIX` consistently. Shell lookup uses the same
  configured prefix, with the existing default, instead of hardcoded version
  paths. Add only the minimal configuration plumbing needed for that lookup.

Use a pinned `tools/defs/flyline.sh` with checksums and supported archive formats.
For this layout, require an exact libc match on Linux. Keep the existing musl
preference for executable tools. Document this narrow exception in `AGENTS.md`
and tool documentation, and test both selection policies. The manifest must
also distinguish artifact support from the current Bash's ability to load it.

Extend the developer generator and live checker where their executable
assumptions apply. Updating the checker does not authorize running
`just test-assets-live`.

## Stage 2: optional session activation

Add a small private Flyline module with explicit initialization and state.
Prefer a finalization call near the end of `shell/rc.sh`, after regular,
OS-specific, and host-specific hooks have established prompt and history
configuration. Confirm this order in the pilot before freezing it.

Before loading, require the enable switch, an interactive Bash, usable terminal
input/output, a supported TERM, and a compatible Bash version/build. Resolve
the active managed library to a valid owned release using a shared lightweight
helper; do not source the whole installer or use developer tools at login.

Load through `builtin enable -f` with the explicit absolute library path.
Do not search `BASH_LOADABLES_PATH` or load an arbitrary library found in PATH.
Detect an already loaded Flyline or another line editor, including ble.sh;
do not replace or configure an integration owned independently by the user.
Use actual builtin state, not inherited `FLYLINE_VERSION` alone, as evidence
that Flyline is loaded in the current process.

Record successful ownership only after loading, settings, and bindings succeed.
Missing or unsupported assets leave Readline usable. A recoverable init failure
must unload the integration's own builtin and restore affected session state.
A native crash inside Bash cannot be caught by a shell fallback; the
compatibility pilot and conservative platform support are necessary limits.

Repeated sourcing must not duplicate bindings or history hooks. Disabling an
owned instance must restore its settings and Readline behavior. A new shell
with the switch set to zero is the guaranteed recovery path; do not promise
arbitrary mid-session toggling before native unload behavior has been tested.

## Stage 3: history, prompt, and completion behavior

| Session state | History storage | Ctrl-R owner |
| --- | --- | --- |
| Flyline disabled or unavailable | Existing Atuin/Bash policy | Existing Atuin/fzf/Readline behavior |
| Flyline active, Atuin active | Existing Atuin database and hooks | Flyline adapter opening Atuin search |
| Flyline active, Atuin disabled or initialization failed | Existing Bash history policy | Flyline's native search of Bash history |

For the Atuin adapter, use APIs verified against our pinned version. Selection
must insert editable text and cancellation must restore the original buffer.
Do not copy the upstream example's `+submitOrNewline` action: the project's
`enter_accept=false` policy must survive. Test multiline commands and the
same Ctrl-R/Up sequence across both editor paths. Keep existing hooks and
Atuin lifecycle restoration intact; changing the recording backend is outside
this addition.

With Atuin disabled, retain explicit empty `HISTFILE` and `/dev/null` choices.
Do not enable Flyline JSONL storage or import/export Atuin history automatically.
Verify normal Bash persistence and parallel-session behavior before relying
on Flyline's native search. Explain that older Atuin-only entries remain in
Atuin unless the user separately migrates them.

Retain Starship and test multiline prompt rendering and command exit status.
Completion uses existing registered Bash functions and built-in file completion.
Verify quoted paths, aliases, Unicode, and a controlled dynamic completer.
Do not claim that installing Flyline supplies completion definitions for every
installed tool. Disable suggestions that would offer to download or build
additional tools during login or ordinary typing.

## Stage 4: tests, measurements, and user documentation

Use subprocess pytest tests for management behavior and real PTYs for editor
behavior. Mocks can test guards and rollback but cannot establish native
compatibility. Keep native tests offline once their explicit local artifacts
are supplied; default tests must not download release binaries.

| Area | Required evidence |
| --- | --- |
| Installation | Pinned manifest, checksum rejection, exact libc selection, library-member validation, custom prefix, atomic reinstall and rollback. |
| Management | Expected-set reinstall, list/check/doctor without executable assumptions, update, uninstall, active release protection, conservative prune, old record compatibility. |
| Disabled path | No load attempt or extra processes when disabled; Bash 3.2, missing artifact, unsupported TERM, noninteractive and no-TTY guards. |
| Lifecycle | Actual builtin detection, nested shells, repeated sourcing, owned unload/failure recovery, preservation of external integration state. |
| Editing | vi gate, multiline input, Unicode, paste, resize, Ctrl-C/Ctrl-D, terminal restoration, highlighting and completion. |
| History | Atuin on/off/unavailable, no duplicate records, correct status/duration, selection without execution, cancellation and original buffer, persistence. |
| Terminal contexts | Direct PTY, representative SSH session, tmux and zellij; mark unavailable environments unverified. |

Extend the existing [startup benchmark](bench-shell.md) with explicit Flyline
off/on scenarios, keeping its existing scenarios comparable. Measure fresh
and warm caches, Atuin on/off, first usable input, history search, and Tab
response. Report sample counts, medians, tail latency, and idle activity.
Choose and record acceptable overhead before interpreting the measurements;
do not invent performance claims from the implementation language.

Update `docs/install.md`, `docs/shell.md`, `docs/shell/helpers.md`,
`shell/rc.d/README.md`, `docs/tools.md`, and relevant `remote-ssh guide`
sections with support limits, activation, completion prerequisites, history
ownership, update behavior, and a copyable disable command. Keep CLI help
concise. Keep README changes to a short pointer if useful.

Run focused tests during implementation, then `just smoke` and
`git diff --check`. Run the bounded native/PTY matrix and benchmark separately
with the selected artifacts. Do not run `just test-assets-live` unless
explicitly requested. This document-only change requires link and diff checks,
not a claim of runtime validation.

## Delivery and completion criteria

1. Pilot record and support/vi decisions.
2. Library installation, ownership, and complete management lifecycle.
3. Optional editor activation and history/prompt/completion adapters.
4. PTY regressions, measurements, and user documentation.

Keep each step reviewable; do not publish an installable definition before the
management lifecycle understands it. Rebase the plan on any intervening
installer changes before starting step 2.

The initial integration is complete when a user can explicitly install the
pinned supported library, enable highlighting in a new remote-ssh shell, use
the agreed editing/history behavior, and return to the existing session path
by starting with `REMOTE_SSH_ENABLE_FLYLINE=0`. Missing or incompatible Flyline
must not prevent normal shell use. Installation remains optional; enabling it
by default, replacing Atuin, adding flycomp/Carapace, and expanding platform
coverage are separate decisions informed by the pilot.

## Upstream evidence

Checked on 2026-10-30. Documentation describes capabilities, not proof that our
integration or all target platforms work.

- [Flyline v1.9.0 release](https://github.com/HalFrgrd/flyline/releases/tag/v1.9.0).
- [Tagged README](https://github.com/HalFrgrd/flyline/blob/v1.9.0/README.md):
  editor features, Bash completion integration, and third-party history UI.
- [Tagged installer](https://github.com/HalFrgrd/flyline/blob/v1.9.0/install.sh):
  Bash artifact families, native library names, checksums, and platform logic.
  Read as evidence only; it must not be executed by remote-ssh.
- [Upstream install/upgrade notes](https://github.com/HalFrgrd/flyline/blob/master/docs/installing_and_upgrading.md):
  dynamic loading and existing-session update behavior. Recheck against the
  selected tag during Stage 0.
