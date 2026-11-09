# Flyline Integration Plan

Created: 2026-10-30
Revision: R7; repair 01 supported initialization batching, local qualification 2026-11-09
Status: four audit fixes and repair 01 implemented; local functional/native/startup/full checks pass;
final SDD acceptance is tracked in the repair record and execution history; Release publication deferred by user

The [2026-11-09 integration audit](flyline-integration-audit.md) recorded three
P2 issues (late external Atuin ownership, disabled external Flyline ownership,
and unrelated binary uninstall) and one P3 rollback export-attribute issue.
The four fixes and their regression-first evidence are recorded in the
[repair R1 record](flyline-integration-repair-r1-record.md), including both
historical startup failures and the changed-source repair-01 qualification result. The accepted
[repair contract below](#post-audit-repair-plan) and frozen R5 basis remain
available; Release preparation and commit splitting remain separate work.

The [R4 native pilot](flyline-pr974-pilot-record.md) records the
six-patch candidate `1.10.0-pr974.aae68bb4.r4`, including undo transactions,
counted movement, vi history and safe unloading. It passes 32 vi probes locally,
with native terminal/history/completion checks and declared performance budgets.
Library installation, management and optional session activation are implemented
and tested in isolated local checkouts. The release and production definition
are not published. The [R1 report](flyline-pr974-pilot-record-r1.md) preserves
the original 13/17 failure unchanged.

The [fork integration record](flyline-fork-integration-record.md) supersedes
the earlier asset-only release proposal. The user's `fmmaciej/flyline` fork now
has `remote-ssh-vim` at `d037c075ed30a61080873985ea2621d743ddfc64`: the real
1.10.0 history, six patch commits, and separate downstream build/documentation.
`master` is unchanged. Candidate R5 is rebuilt from this genuine Git history;
R4 artifacts and evidence remain historical. The user chose **no Release
publication** on 2026-11-09. Keep the release/manifest prepared locally and do
not promote an unavailable URL into `tools/defs`.

Future releases belong to `fmmaciej/flyline`, with a downstream-prefixed tag
pointing at the actual source commit. Do not publish Flyline assets in
`fmmaciej/remote-ssh` or use an asset-only tag anchored to unrelated source.
The exact fork commit is pinned in `dev/flyline/fork.json`; no moving branch is
an installation source. Build logic belongs to the fork; this project keeps
the pinned build entrypoint, installer, session hooks and integration probes.

The user explicitly limited current validation to local macOS. Linux, weak SSH
hosts and other architectures remain unverified; no SSH connection is authorized
for this continuation. Initial publication must contain only qualified macOS
arm64 assets. The detailed steps below remain the implementation contract and
follow-up platform checklist, not a claim that every listed environment passed.

Add Flyline as an optional editor for interactive `remote-ssh shell` sessions,
based on the latest stable upstream release plus the implementation from
[Vim-mode PR #974](https://github.com/HalFrgrd/flyline/pull/974).
On the planning date the latest stable release is **v1.10.0**, not v1.9.0.
Pin that release and the PR head as recorded below; do not install a moving
branch or resolve `latest` on remote hosts.

The priorities are fast editing on weak hosts, vi/Vim operation, and useful
Tab completion. Coloring is optional and subordinate to those priorities.
Flyline supplies the editor/UI; the separately planned Carapace supplies
completion definitions. Installation and activation remain independent.

The [v1.9.0 pilot](flyline-pilot-record.md) remains valid historical evidence:
that unpatched release failed the vi comparison. The user has now requested
planning a new candidate containing the Vim implementation, with the latest
stable release as its base. This reopens the pilot for that candidate without
waiving the vi requirement or claiming that the PR is already validated here.

## Scope and initial decisions

- Keep the existing Readline session as the default. Proposed switch:
  `REMOTE_SSH_ENABLE_FLYLINE=0` by default, `1` to request activation. Add it to
  the existing shell configuration allowlist, with environment precedence.
- Keep Flyline out of `MINI_TOOLS`, `QUICK_TOOLS`, `DEFAULT_TOOLS`, and
  `RUNME_TOOLS`. Users explicitly select it through the existing install CLI.
- Keep Atuin installed and its history intact. Adding an editor does not select
  a new history store or migrate data. Preserve the existing Atuin toggle and
  backend selection once per Bash process. `rcrc` must preserve this choice.
- Keep editor and provider independent. Follow the existing
  [Carapace plan](carapace-implementation-plan.md) for one optional completion
  provider, with no user-maintained provider map. Both toggles default to `0`.
  Flyline alone must still support built-in/fixture completions, and Carapace
  alone must still work with Readline. Neither silently installs the other.
  Do not add argc, bash-completion, flycomp, or automatic completion generation.
- Enable Vim mode explicitly after loading; `set -o vi` is insufficient for
  Flyline. The PR API is `flyline key --vim-mode true`; verify the ported API
  and key dispatch before considering initialization successful.
- Prioritize vi and Tab UI. Native highlighting may remain if measurements
  allow; use an existing disable control only if the selected source provides
  one. Do not invent a setting or add a highlighting subsystem. Disable mouse capture,
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

For the full editor plus rich-completion profile, explicitly install Carapace
and also set `REMOTE_SSH_ENABLE_CARAPACE=1` after both implementations exist.
Document expected-tools maintenance without changing the meaning of
`remote-ssh tool install` or overwriting the user's maintained tool set.

## Source, backport, and artifact identity

| Input | Pinned identity |
| --- | --- |
| Latest stable base, checked 2026-11-08 | `v1.10.0`, commit `ca910967af35579a2d455a071aa939778d8f6171` |
| Vim implementation | PR #974, commit `aae68bb4acb43d7462bbe4abffedd6e2b10bd889` |
| PR branch's own package version | `1.7.1`; it is not a 1.10.0 build |
| Prior pilot | Unmodified 1.9.0; not the new acceptance baseline |

Port only the Vim changes onto the pinned stable base. Do not deploy the older
PR branch wholesale, merge a moving master, or discard fixes in 1.10.0 to make
the patch apply. Record the resulting source commit, all additional patch
hashes, Cargo.lock, toolchain, build flags, target, and source/library hashes.
Retain the base lockfile unless a specific dependency change is necessary and
reviewed. Use locked builds; do not resolve the dependencies' moving Git
branches afresh. A newer stable release discovered before implementation
requires an explicit plan/pin update and another port check, not silent drift.

A planning-only `git apply --check` against the 1.10.0 source accepts changes
in **9 of the PR's 10 files**. `crates/flybuffer/src/editing_advanced.rs` needs
manual reconciliation with intervening editing changes. This establishes a
plausible port, not compilation, correct behavior, or ABI compatibility. See
[port-check evidence](flyline-pr974-planning-evidence/port-check.json).
The accompanying [input record](flyline-pr974-planning-evidence/inputs.json)
identifies the source archive, patch reconstruction, CI artifact, and the
limits of this planning check. No source patches were applied during it.

The PR's `VimDotRepeat` currently only clears pending state. Include a bounded
fix and regression coverage for actual `.` repeat in the port. Audit remaining
required vi operations rather than inferring completeness from declared action
names. Changes needed for vi/history/completion compatibility belong in a
small, recorded patch series; do not grow an unrelated Flyline fork.

Build on developer/CI machines only, then distribute immutable versioned
GitHub Release archives with checksums. Example custom identity:
`1.10.0-pr974.aae68bb4.r1`; increment it for every source/patch change. Embed or
ship provenance that distinguishes this build from official 1.10.0 even if
the upstream library's own version text remains unchanged.

The controlled release repository (`GH_REPO`), exact tag, asset names, and
digests must be finalized before shipping the tool definition. Do not invent
URLs or pass placeholders to runtime. Prepare builds, test results, archives,
checksums, and release notes before any separate external publication step.
Planning does not publish releases, push branches, or send messages upstream.

The PR's successful Linux CI run has a `built-flyline-library` artifact that
expires on 2026-11-28. It can aid an isolated PR-head investigation, but it is
not a durable installation source, a backported 1.10.0 build, or a macOS build.
Runtime must never download Actions artifacts, compile Rust, cherry-pick Git
commits, or execute the upstream installer.

### macOS and initial targets

The 1.10.0 release and build configuration support both
`aarch64-apple-darwin` and `x86_64-apple-darwin`, with native `.dylib` linking
flags. Plan separate builds of the **patched** source for both; official
1.10.0 macOS archives do not contain this unmerged PR.

Start native acceptance on macOS arm64 and Linux glibc x86_64. Add macOS Intel
and Linux aarch64 support only with their own build/load/PTY evidence. Keep
musl deferred until the library is validated with musl Bash. Cross-compilation
alone does not validate an interactive target.

On macOS, use a modern Bash exposing the required loadable-builtin symbols,
initially Homebrew Bash >= 4.4. The system `/bin/bash` is not an assumed target.
Never install Bash or change the default shell automatically. The earlier
arm64 library-load result is useful context but does not validate the new
patched library. Report an unavailable Intel test machine as unverified.

## Current integration boundaries

| Area | Current behavior | Required change |
| --- | --- | --- |
| [Shell launcher](../../tools/lib/commands/shell.sh) | Selects Bash from PATH and launches it with `--rcfile`. | Preserve selection; do not silently switch Bash to satisfy Flyline. |
| [Line editing](../../shell/rc.d/11-line-editing.sh) | Enables vi mode. | Establish whether the pinned Flyline can preserve the required editing behavior. |
| [Early history selector](../../shell/rc.d/05-bash-preexec.sh) | Sets process-local `REMOTE_SSH_HISTORY_REQUEST` and loads bash-preexec only for a prospective owned Atuin setup. | Preserve early selection before prompt initialization. |
| [Atuin](../../shell/rc.d/23-atuin.sh) | Finalizes `REMOTE_SSH_HISTORY_BACKEND` as `atuin`, `bash`, or `external` once per process; managed bindings affect only Ctrl-R in Emacs/vi insert modes. | Adapt the editor UI after selection without rerunning Atuin initialization or changing storage. |
| [Bash history](../../shell/rc.d/06-bash-history.sh) | Preserves explicit `HISTFILE`; successful owned Atuin setup later suppresses file writes. | Preserve persistence and external ownership. |
| [skim](../../shell/rc.d/20-skim.sh) | Supplies `__skim_history` and binds Ctrl-R for the Bash backend in Emacs/vi insert modes. | Add a Flyline adapter to the existing widget; preserve the Readline fallback. |
| [Installer](../../tools/lib/install-tool/install.sh) | Installs an executable or bundle and publishes executable links. | Represent a Bash library without pretending it is a command in PATH. |
| [Release records](../../tools/lib/common/release.sh) | Identify owned executable releases. | Identify and protect library releases as well, preserving old records. |
| [Platform selection](../../tools/lib/install-tool/assets.sh) | Prefers musl executable assets on glibc Linux. | A loaded library must match the host Bash/libc ABI; do not reuse that preference blindly. |
| [Tool inventory](../../tools/lib/install/tool_inventory.sh) and [status](../../tools/lib/commands/tool_status.sh) | Check executable links in `INSTALL_BIN_DIR`. | Report library installation separately from session activation. |

The current history contract is documented in
[shell helpers](../../docs/shell/helpers.md#history). `rcrc` preserves backend
selection and later user binding edits. Up, vi command-mode `k` and `/` retain
their history behavior. The new pilot corrects an earlier assumption: clean
Bash 5.3.20's vi-command Ctrl-R is history search, not Vim redo. Readline's
binding remains untouched; explicitly enabled Flyline Vim mode uses the PR's
redo action, separately from managed insert-mode Ctrl-R history search.

R2 retains R1's skim and once-per-process history contract. Inventory,
ownership, archive handling, and executable selection may continue changing
independently; re-read those modules before implementing the library layout.
The current backport/native arm64 build passes the local vi and combined
Carapace callback pilot above. Linux/SSH qualification and provider runtime
delivery remain separate follow-up work.

## Stage 0: build and validate the PR candidate

Use the pinned 1.10.0 base and PR source above. Reconcile the patch conflict,
complete the required vi behavior, and build a candidate in an isolated
developer checkout. The upstream PR CI passed on its older source; it does
not validate this backport. A version check alone does not establish that the
current Bash exports the symbols needed for loading.

Before runtime changes:

1. Record the base, PR and resulting port commits, patch series, toolchain,
   lockfile, build inputs, exact candidate archive members and SHA-256 values.
   Confirm settings/APIs against the resulting source, not current master.
2. Run relevant upstream unit/integration tests and build release-mode native
   artifacts into an isolated developer directory. Inspect dependencies and
   test loading in disposable Bash subprocesses and PTYs. Do not run the
   upstream installer or modify the developer's shell files.
3. Test the current vi workflow: Escape, insert/command modes, movement,
   deletion, replacement, change/yank/paste, undo/redo, `.` repeat, history
   navigation, and return to insert mode. Explicitly enable the PR's Vim mode.
   Capture actual executed arguments, including the prior `ac` to `bc` case.
4. Exercise the pinned Atuin 18.14.1, conditional bash-preexec initialization,
   Starship, and the Bash/skim history path with that editor. Verify prompt
   hooks, exit status, duration, Ctrl-R selection without execution, ordinary
   Up navigation, and reloads that preserve the selected backend and key edits.
5. Record a support table with Bash executable/version, OS, architecture,
   libc, artifact, load result, vi result, and PTY result. Mark untested rows
   unverified; do not infer compatibility from an asset's name.
6. Test real Bash completions, then the planned Carapace default handler
   (`complete -D`) with Flyline. Verify flags, values, dynamic Git refs, paths
   with spaces, cancellation, and command submission only after explicit Enter.
   Do not assume that command-specific callback support proves `-D` support.
   If needed, make a bounded fix in Flyline's Bash-completion adapter and record
   it with the port. Do not switch to a per-command provider map to hide a bug.
7. Compare Readline, official 1.10.0, and the patched candidate with identical
   fixtures. Prior 1.9.0 timing is historical, not acceptance of the new build.

The first acceptance targets are macOS arm64 and Linux glibc x86_64; Intel
macOS and Linux aarch64 follow with their own evidence. Use the normal Bash
>= 4.4 artifact family. Bash < 4.4 remains on Readline even where upstream
offers legacy builds; system macOS Bash must not be upgraded by this project.
Linux musl requires separate library validation with the target Bash build.

**Exit condition:** at least one supported platform has a reproducible real
PTY demonstration, with the required vi cases passing after the bounded port
and fixes. If required behavior is still incomplete, record the remaining gap
and withhold runtime integration. Do not relax the vi contract or silently
turn vi users into another editing mode to pass the gate.

Deliver a new `dev/docs/flyline-pr974-pilot-record.md` with source fingerprints,
patches, test transcripts, unsupported combinations, and the resulting
decisions. Preserve the old 1.9.0 pilot and its evidence as historical results.
Native Vim correctness and performance must pass before runtime integration;
the presence of the PR or green historical CI alone does not pass this gate.

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

Read the finalized `REMOTE_SSH_HISTORY_BACKEND` before installing managed
history adapters. Keep history request/backend variables process-local; a
child Bash makes its own selection. For the initial integration, an `external`
history backend skips managed Flyline activation rather than adapting user
hooks or keys whose contract remote-ssh does not own.

After loading, explicitly enable Vim mode and apply only settings verified
against the port. A missing/rejected `--vim-mode` option is an initialization
failure, not permission to silently continue with Flyline's ordinary keymap.
Record successful ownership only after loading, settings, and bindings succeed.
Missing or unsupported assets leave Readline usable. A recoverable init failure
must unload the integration's own builtin and restore affected session state.
A native crash inside Bash cannot be caught by a shell fallback; the
compatibility pilot and conservative platform support are necessary limits.

Select the managed editor once per interactive Bash process, after history
selection. Record an explicit finalized state for disabled, skipped, failed,
and active outcomes. Repeated sourcing or `rcrc` must not retry loading,
duplicate hooks, overwrite later user bindings, or switch either editor or
history backend. A changed toggle, PATH, installed library, or executable
availability takes effect in a new shell. Initial setup failure may roll back
the changes from that attempt; do not add a detach/reattach or hot-reload
protocol. A new shell with `REMOTE_SSH_ENABLE_FLYLINE=0` is the recovery path.

## Stage 3: history, prompt, and completion behavior

| Session state | History storage | Ctrl-R owner |
| --- | --- | --- |
| Flyline disabled or unavailable | Existing Atuin/Bash policy | Existing Atuin/skim/Readline behavior |
| Flyline active, Atuin active | Existing Atuin database and hooks | Flyline adapter opening Atuin search |
| Flyline active, Bash backend, skim available | Existing Bash history policy | Flyline adapter calling `__skim_history` |
| Flyline active, Bash backend, skim unavailable | Existing Bash history policy | Flyline's native Bash-history search; must pass the new pilot |
| External history integration | User-owned storage and hooks | User-owned bindings; managed Flyline activation skipped |

For the Atuin adapter, use APIs verified against our pinned version. Selection
must insert editable text and cancellation must restore the original buffer.
Do not copy the upstream example's `+submitOrNewline` action or its Up-to-Atuin
binding: the project's `enter_accept=false` policy and ordinary Up behavior
must survive. Managed search bindings apply only to Ctrl-R in Emacs and vi
insert modes, respecting `ATUIN_NOBIND`. Preserve vi command-mode `k`, `/`, and
Ctrl-R redo supplied by the PR; do not describe it as an existing Readline redo
binding. A library that cannot provide these editing semantics fails the
pilot gate; custom binding support alone is not proof of modal vi support.

Test multiline commands and the same Ctrl-R/Up sequence across both editors.
Keep the one-time backend selection, existing history hooks, import marker,
database, and synchronization policy intact. `rcrc` must not rerun imports or
install history adapters again. An Atuin executable disappearing or failing
after selection does not trigger automatic storage or Ctrl-R reassignment;
document starting a new shell, as the current history contract already does.

With Atuin disabled, retain explicit empty `HISTFILE` and `/dev/null` choices.
Do not enable Flyline JSONL storage or import/export Atuin history automatically.
Adapt the existing skim widget using the pinned Flyline's supported mechanism
for invoking a Bash editing function and restoring its buffer. Cancellation
must preserve the original text and selected entries must remain editable.
Do not source upstream fzf initialization or introduce a generic fzf adapter.
Keep skim settings and navi's private protocol adapter scoped as they are now.
Verify normal Bash persistence, native search without skim, and parallel-session
behavior. Older Atuin-only entries remain in Atuin unless separately migrated.

Retain Starship and test multiline prompt rendering and command exit status.
Completion uses existing registered Bash functions, the optional Carapace
default handler, and built-in file completion. Keep the same provider design
with both editors. Verify all four editor/provider-toggle combinations.
Verify startup and basic completion with none of bash-completion, Carapace, or
flycomp installed, then quoted paths, aliases, Unicode, and a controlled dynamic
completer. Use a fixture function to test the UI without adding a provider.
Do not claim that installing Flyline supplies completion definitions for every
installed tool. Disable suggestions that would offer to download or build
additional tools during login or ordinary typing.

Retain the Carapace plan's on-demand contract: it must not start during editor
initialization, ordinary typing, prompts, or reload. Flyline's automatic
suggestions must not accidentally invoke this provider in the background;
disable them initially using the verified settings. With both features enabled,
Atuin owns history storage, Flyline owns editing/UI, and Carapace supplies
candidates. These roles are independent, not three competing editors.

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
| Lifecycle | Actual builtin detection, fresh backend/editor selection in nested shells, no reinitialization on `rcrc`, preservation of later user key edits, initial setup rollback, external integration exclusion, recovery in a new disabled shell. |
| Editing | vi gate, ordinary Up/k navigation, command-mode `/` and Ctrl-R redo, multiline input, Unicode, paste, resize, Ctrl-C/Ctrl-D, terminal restoration, highlighting with no extra completion providers, and the UI with a fixture completer. |
| History | Initial Atuin on/off/unavailable/failure, `ATUIN_NOBIND`, skim present/absent, no duplicate records, correct status/duration, editable selection, cancellation, explicit `HISTFILE`, persistence, unchanged backend after toggle/PATH/executable changes. |
| Terminal contexts | Direct PTY, representative SSH session, tmux and zellij; mark unavailable environments unverified. |

Extend the existing [startup benchmark](bench-shell.md) with explicit Flyline
off/on scenarios, keeping its existing scenarios comparable. Measure fresh
and warm caches, Atuin on/off, first usable input, history search, and Tab
response. Report sample counts, medians, tail latency, and idle activity.
Measure short and long lines, single keys, first/warm Tab, and transient
provider memory separately from shell RSS. Include an actual weak Linux host
before claiming support for that environment; record an unavailable host as
unverified. Choose and record acceptable overhead before interpreting the
measurements. Do not transfer 1.9.0 performance numbers or infer speed from Rust.

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

## Post-audit repair plan

Planned on 2026-11-09 from [findings F1–F4](flyline-integration-audit.md#confirmed-findings).
This section preserves the accepted R5 repair contract. The implemented fixes,
functional checks, historical startup failures and changed-source qualification are recorded in the
[repair R1 record](flyline-integration-repair-r1-record.md). The frozen audit
script, transcripts and fingerprints remain unchanged.

### Scope and order

Use four focused changes, each with its failing regression first. Apply them in
the order **F3 → F1 → F2 → F4**, then run the combined native checks. F3 affects
ordinary management commands and can be verified independently. F1/F2 establish
ownership before F4 handles the remaining managed activation failures.

| Step | Implementation | Regression coverage |
| --- | --- | --- |
| 1 / F3 | `tools/lib/commands/uninstall.sh` | `dev/tests/test_uninstall.py`, library cases in `dev/tests/test_install_library.py` |
| 2 / F1 | `shell/rc.d/29-flyline.sh`; change module 23 only if ownership cannot be established from its existing selected backend | `dev/tests/test_flyline_lifecycle.py`; full-rc OS/host hook fixtures |
| 3 / F2 | `shell/rc.d/29-flyline.sh` | Enabled/disabled builtin and function/alias exclusion tests in `dev/tests/test_flyline_lifecycle.py` |
| 4 / F4 | `shell/rc.d/29-flyline.sh` | Variable state/export rollback matrix in `dev/tests/test_flyline_lifecycle.py` |
| 5 / validation | New opt-in `dev/flyline/ownership.py`, reusing `managed.py` and the existing PTY helper | Real R5 library and local Atuin, then existing lifecycle/history/startup probes |

Runtime changes remain Bash-only, with no new dependencies, network probes or
per-command hooks. Keep loading opt-in, after OS/host hooks, and once per Bash
process. The R5 Rust source, library bytes, source pin and artifact identity do
not change for these shell integration fixes. No fork rebuild is needed unless
validation exposes a separate native defect.

### Step 1 — F3: scope uninstall preflight to library operations

Resolve and validate explicit tool names before determining whether library
inspection is necessary. For explicit selections consisting only of executable
or bundle layouts, do not consult `.active`. An ordinary file, symlink, or broken
symlink at that path must remain untouched and must not block binary uninstall.

For a selection containing a library, retain validation of an existing `.active`
directory, before any link/release/config mutation. A mixed explicit selection
must fail as a whole on an invalid library directory. Do not merely remove the
global check: the current release-directory collector could otherwise delete a
library release after its active link was protected/skipped.

For automatic selection without tool arguments, require library inspection only
when known tool definitions include a library layout. Preserve conservative
failure on an existing invalid `.active` when that inspection is needed. With
only executable definitions, auto-discovery must continue to work despite an
unrelated `.active` file. Preserve existing behavior when `.active` is absent.
Check required preflight return codes directly; do not lose failures through
process-substitution output collection.

Acceptance tests must verify exit status, selected links/releases, preservation
of the unrelated path and its target, and the `expected-tools` file:

- Explicit ordinary binary uninstall with `.active` as a file, directory
  symlink, or broken symlink succeeds and only removes the selected managed tool.
- Automatic binary-only discovery with no library definitions succeeds with
  the unrelated file; a control without that file has the same result.
- Explicit library, mixed binary/library, and automatic discovery requiring
  libraries abort before mutation on invalid `.active`; `expected-tools` stays
  unchanged. An unreadable real directory is tested where permissions allow.
- Valid mixed uninstall, format-1 records, aliases, unknown/unmanaged paths and
  current library lifecycle/prune protections retain their existing behavior.

### Step 2 — F1: recheck external history ownership after late hooks

Immediately before resolving/loading Flyline, check the current Atuin ownership
marker as well as the selected backend. If `__atuin_initialized=true` and the
backend is not remote-ssh's successfully selected `atuin`, skip Flyline as
`skipped:external`. Keep the existing `external` backend exclusion. A managed
Atuin initializer also sets this marker, so the marker alone must not disable
the supported managed Atuin/Flyline combination.

Use the existing process-local backend as evidence of managed initialization;
avoid a second ownership cache unless tests demonstrate it is necessary. Do not
rerun Atuin initialization, overwrite the backend selected earlier, migrate
history, or reselect it on `rcrc`. Inherited `FLYLINE_*` strings alone remain
insufficient evidence of an external editor.

Add full-rc subprocess/PTY fixtures for a late initializer in each of OS and
host hooks, with no native dependency in default tests. Assert that the current
marker is observed, the Flyline library resolver/load/settings are not called,
and the external history bindings/callbacks remain intact. Keep positive managed
Atuin coverage, including `ATUIN_NOBIND`, plus early external, Bash/skim, repeated
`rcrc`, and a fresh nested Bash process. Check both Atuin toggle settings where
the early backend is Bash because managed Atuin was disabled or unavailable.

### Step 3 — F2: detect a loaded but disabled builtin

Supplement the current type-based function/alias guard with read-only Bash
introspection of both enabled and disabled builtins. Match the exact Flyline
builtin entry from `builtin enable -a`; do not change its enabled state while
probing, and do not match similarly named entries. Keep this after the existing
toggle/TTY/Bash guards, with no external process invocation for text filtering.

If an external Flyline builtin is enabled or disabled, return
`skipped:external` before resolver/load/settings calls. Never enable, configure
or unload that instance. Existing function/alias exclusions remain effective.
When no builtin is loaded, stale inherited version/load-directory markers must
still permit an otherwise valid managed activation.

Update the mock's `enable` dispatcher so list/query operations do not masquerade
as unload operations. Cover enabled and disabled external entries, function and
alias cases, an unrelated builtin name, and the normal no-Flyline load path.
The native probe must preserve an externally disabled R5 builtin as disabled,
with no `dynamic builtin already loaded` warning from a second load.

### Step 4 — F4: restore values and export attributes after failed activation

Before attempting a managed load, save set/unset state, scalar value and export
attribute independently for `FLYLINE_LOAD_DIR` and `FLYLINE_VERSION`. Preserve
empty strings and an exported-but-unset declaration. Restore using assignments,
`unset`, and explicit export/unexport operations as appropriate. If `declare -p`
is used for inspection, do not replay a plain `declare` inside the finalizer:
it would create function-local variables instead of restoring the caller's state.

On load failure or settings failure followed by successful unload, restore both
variables exactly. On successful activation, keep intentional managed values
and export behavior. Preserve the existing unload-failure warning/recovery path;
do not restore misleading old markers while a failed-to-unload builtin remains.

Parametrize each variable's unset, exported-but-unset, empty/nonempty exported,
and empty/nonempty unexported states across both failure stages. Avoid a full
cross product when independent cases cover the same behavior. Verify existence,
value, export status and child-process environment, not only concatenated values.
Include quoted/whitespace values, successful activation, and the unload-failure
control. After a native settings failure, demonstrate actual Readline vi editing.

### Combined validation and completion gate

1. Run the affected pytest subprocess/PTY tests using the existing `runtime_bash`
   matrix, explicitly ensuring local Bash 3.2 and Homebrew Bash 5.3 are selected.
   Bash 3.2 validates CLI behavior and graceful editor skipping; it is not a
   native library target. Each new regression must fail for its audited cause
   before the corresponding fix and pass afterward.
2. Add `dev/flyline/ownership.py` with explicit `--repo`, `--bash`, `--library`,
   `--atuin`, and `--output` paths. Use isolated managed installs and PTYs for
   late external Atuin in OS/host hooks, the disabled external builtin, rollback
   attributes, and positive managed activation. A timeout or wrong state exits
   nonzero. Write expected/actual results and transcripts without downloading
   binaries or modifying the frozen audit reproduction.
3. Run that native gate with the existing R5 payload, then existing lifecycle
   Readline restoration and managed history checks for Bash, skim and Atuin.
   Verify the library hash is still
   `ac989a041026f49df1d3b544290ee3e67b497a0d3f82fe4785cd3c106e431d57`.
4. Because startup guards change, repeat the existing eight-scenario startup
   comparison once, with 20 measured rounds per scenario and the established
   30 ms median / 60 ms p95 overhead limits. Save the budget before sampling.
   Full editor performance and multiplexer requalification are unnecessary for
   these shell-only fixes unless a new failure justifies them.
5. Run `just smoke`, `git diff --check`, and local documentation link checks.
   Save new results, commands and source fingerprints under
   `dev/docs/flyline-integration-repair-r1-evidence/` with a separate repair
   record. Link the record from this plan. Keep all historical evidence intact.

The repair is complete when all F1–F4 expectations above pass, the focused and
full checks are green, the native checks prove preserved external ownership
and usable Readline recovery, and the startup budget passes. Update plan status
only after those results exist. If native checks expose a Rust defect, report
it separately before changing the fork/artifact pin or reusing R5 qualification.

Current authorization remains local macOS only. No SSH/Linux runs, live asset
checker, startup-file edits, release publication, production manifest promotion,
staging, commits or pushes are part of this repair plan. Proposed source changes
map to audit commit group C for F3 and group D for F1/F2/F4; developer probes and
new evidence map to E/F. Splitting or creating commits is a later task.

## Delivery and completion criteria

1. Port the pinned PR onto the pinned latest stable release, address required
   vi gaps, and produce the new native pilot/support/performance record.
2. Prepare immutable tested archives and provenance, then implement library
   installation, ownership, and the complete management lifecycle. Publish an
   external release only after those concrete artifacts are ready for review.
3. Optional editor activation and history/prompt/completion adapters.
4. PTY regressions, measurements, and user documentation.

Keep each step reviewable; do not publish an installable definition before the
management lifecycle understands it. Rebase the plan on any intervening
installer changes before starting step 2.

The initial integration is complete when a user can explicitly install the
pinned patched library, enable Vim editing and Tab UI in a new remote-ssh shell,
use the agreed history behavior and optional Carapace candidates, and return
to the existing session path
by starting with `REMOTE_SSH_ENABLE_FLYLINE=0`. Missing or incompatible Flyline
must not prevent normal shell use. Installation remains optional; enabling it
by default, replacing Atuin, adding bash-completion/flycomp, and expanding
platform coverage are separate decisions informed by the pilot. Carapace
remains the independent optional provider described in its own accepted plan.

## Upstream evidence

Rechecked on 2026-11-08. Documentation and CI describe upstream capabilities,
not proof that the backport, our integration, or all target platforms work.

- [Flyline v1.10.0 release](https://github.com/HalFrgrd/flyline/releases/tag/v1.10.0).
- [Vim PR #974](https://github.com/HalFrgrd/flyline/pull/974) and
  [its pinned CLI](https://github.com/HalFrgrd/flyline/blob/aae68bb4acb43d7462bbe4abffedd6e2b10bd889/src/cli.rs#L525).
- [Known dot-repeat stub](https://github.com/HalFrgrd/flyline/blob/aae68bb4acb43d7462bbe4abffedd6e2b10bd889/src/app/actions/keyboard.rs#L1302).
- [PR-head CI and Linux artifact](https://github.com/HalFrgrd/flyline/actions/runs/33311816306).
- [Tagged README](https://github.com/HalFrgrd/flyline/blob/v1.10.0/README.md):
  editor features, Bash completion integration, and third-party history UI.
- [Tagged installer](https://github.com/HalFrgrd/flyline/blob/v1.10.0/install.sh):
  Bash artifact families, native library names, checksums, and platform logic.
  Read as evidence only; it must not be executed by remote-ssh.
- [macOS/native release targets](https://github.com/HalFrgrd/flyline/blob/v1.10.0/.github/workflows/release.yml).
- [Upstream install/upgrade notes](https://github.com/HalFrgrd/flyline/blob/v1.10.0/docs/installing_and_upgrading.md):
  dynamic loading and existing-session update behavior. Recheck against the
  selected tag during Stage 0.
