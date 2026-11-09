# TODO

Reviewed against the implementation on 2026-11-02. Open items are backlog;
deferred proposals require a concrete use case or a separate design decision.

## Implemented / Current Baseline

- [x] README explains the project, its intended users, and why it exists, and
  links to install, shell, tool, developer, and TODO documentation. Further
  shortening is a polish task below.
- [x] `ssh-find` and `ssh-pick` are documented as optional helpers requiring
  `python3`, `ssh`, and skim (`sk`). Python remains an explicit dependency.
- [x] Runtime config supports update-check enable/disable and interval settings
  through `${XDG_CONFIG_HOME:-$HOME/.config}/remote-ssh/config`.
  `remote-ssh guide config` shows effective values and their sources; checks
  remain throttled and non-mutating. See [runtime config](shell/config.md).
- [x] The Bash boundary is explicit: `shell/rc.sh` rejects loading from Zsh,
  and docs explain `remote-ssh shell` and the manual Bash fallback. Individual
  modules retain tested Zsh init branches; this does not imply full Zsh support.
- [x] Post-install templates describe explicit shell activation and the
  `bash --rcfile ... -i` fallback.
- [x] `shell/rc.d/os.d` and `shell/rc.d/host.d` are reserved for shell runtime
  customization. Tool installation uses exact manifests and platform selection,
  independently of these hooks; hooks do not install dependencies.
- [x] Added 33 pinned SHA-256 values for all declared assets of `bat`, `eza`,
  `fd`, `fzf`, `nu`, `nvim`, and `zoxide`, using official release metadata.
  Coverage is 89/99 assets repository-wide; the ten exact exceptions for navi
  and yazi are documented in [pinned tool checksums](tool-checksums.md).
  Offline tests enforce complete mappings outside those exceptions and verify
  that a bad checksum stops installation before extraction.
- [x] Single-binary selection uses literal names and requires exactly one valid
  executable within depth four, or an explicitly declared `BINARY_PATH`.
  Missing/ambiguous candidates, unsafe paths, and incomplete scans fail before
  release staging. Explicit paths have no discovery fallback; selected relative
  paths reject symlinks and control characters. Regression tests preserve raw
  assets, bundles, aliases, working releases, and temporary-file cleanup. See
  [single-binary selection](tools.md#single-binary-selection).

## Open: Install Reliability

- [ ] Revisit the ten checksum exceptions for navi `v2.23.0` and yazi `v25.5.31`
  when updating these tools or when upstream publishes additional hashes.
  - The checked official release metadata has `digest: null`, no checksum
    assets, and no hashes in the release descriptions for those files.
  - Keep exceptions tied to exact repository/tag/asset tuples; a new release
    must be checked again. Do not substitute a locally calculated hash alone
    as proof of upstream origin.

- [ ] Harden archive extraction before unpacking external release assets.
  - Proposal, **not scheduled**:
    [archive extraction plan](../dev/docs/archive-extraction-plan.md).
    It was previously declined as the next implementation step.
  - Ordinary `tar`/`unzip` extraction still trusts archive entries. Bundle mode
    separately validates paths, the declared root, and entry types.
  - Validate paths and entry types before extraction, reject absolute paths,
    traversal, and unsafe links, and isolate extracted files from inputs.
  - Reconcile the plan with all currently supported archive formats, including
    `.tar.xz`, before implementation; raw executables keep their separate flow.
  - Keep Bash 3.2 compatibility and minimal runtime dependencies. Treat parser
    portability and failure/rollback coverage as part of this separate task.

## Open: Optional Shell Completion

- [ ] Add optional Flyline using latest stable 1.10.0 plus a pinned port of
  Vim PR #974.
  - [Updated integration plan](../dev/docs/flyline-implementation-plan.md), R7.
    The port, vi/unload fixes, library lifecycle and opt-in runtime are implemented.
    The [pilot](../dev/docs/flyline-pr974-pilot-record.md) passes 32/32 vi probes
    locally on macOS arm64, with Atuin/skim/Starship and Carapace callback checks.
    The [fork migration](../dev/docs/flyline-fork-integration-record.md) preserves
    upstream history in `fmmaciej/flyline:remote-ssh-vim`. Release publication is
    deferred by user; the production manifest remains unpromoted.
    The [completed SDD repair](../dev/docs/flyline-integration-repair-r1-record.md)
    has independent Pass; local native, history and startup gates pass.
  - Preserve vi, Atuin and skim; prioritize fast typing and Tab UI. Validate
    the patched library; Linux and weak-host qualification are deferred at the
    user's request. Optional Carapace remains its own integration task.
  - Distribute versioned prebuilt assets; do not build or download PR artifacts
    at remote shell startup. Keep installation/activation opt-in.

- [ ] Add opt-in Carapace completion while retaining Bash/Readline and vi.
  - [Implementation plan](../dev/docs/carapace-implementation-plan.md), R1;
    planned, not implemented.
  - One provider for commands reaching the default completion handler, with
    existing explicit completions preserved and no provider execution at startup.
  - Validate the proposed generic callback and weak-host performance before
    claiming support. Keep Carapace outside default install profiles initially.

## Open: Documentation Polish

- [ ] Shorten README's install variants and command catalogue where they
  duplicate detailed docs.
  - Keep a clear first-use path and links to `docs/install.md`, `docs/shell.md`,
    `docs/tools.md`, `dev/README.md`, and this TODO.
  - The landing-page structure is already present; this is no longer a full
    README reorganization or the project's top priority.

- [ ] Correct the guide note claiming that `vim/nvim and tmux are not installed`.
  - Neovim has a managed bundle definition and is included in profile `full`;
    tmux is still supplied separately by the host.

- [ ] Document the existing tmux and Zellij choices before considering new
  session behavior.
  - Current support: bundled tmux config, alias, documentation, and test;
    a pinned Zellij definition and navi cheatsheet. Neither starts automatically.
  - Zellij is included in profile `full`; tmux has no managed tool definition.
    Distinguish optional activation from inclusion in an install profile.
  - Explain the tradeoff between tmux's familiar server workflow and Zellij's
    standalone release and discoverable interface, including keybinding habits
    and the cost of adding a multiplexer to a minimal session.

## Deferred: Revisit When Needed

### Upstream Signatures

Consider official signature verification after checksum coverage. Establish
which projects publish usable signatures and decide on runtime dependencies
before adding a verifier.

### Python-Free SSH Helpers

Revisit `scripts/ssh_find.py` only for a concrete host that needs these helpers
without Python. Account for existing SSH config and bssh record handling before
choosing a replacement or maintaining a second shell implementation.

### Multiplexer Session Behavior

Automatic tmux/Zellij launch and a `user@host` session name are unimplemented
proposals. Decide which multiplexer to use, how to attach or create sessions,
how to handle nesting, and how users opt in before implementing either.
Retain manual launch while those requirements are unspecified.

### LazyVim Profile

No LazyVim profile or helper is implemented. Revisit for a concrete editing
workflow, keeping the lightweight bundled `dots/vimrc` as the default.
If added, isolate the profile with `NVIM_APPNAME=remote-ssh-lazyvim`, bypass
the bundled `nvim -u .../vimrc` alias in its helper, and document manual starter
installation. Do not install plugins during `runme.sh`; first launch may need
Git, network access, fonts, and plugin-specific tools.

### Dozzle Examples

No Dozzle integration is implemented. Consider docs or navi examples only when
needed for container-log work. It is a web/container application with socket or
RBAC considerations, outside the standalone CLI install model, and does not
provide retained log storage. Adding it as a default tool is not planned.

### Shared Platform Detection

`remote_os_id` and installer `detect_platform` remain separate. Revisit shared
OS normalization if they diverge or shell runtime needs architecture detection.
Keep any shared helper lightweight and retain exact `ASSETS`, `detect_libc`, and
`current_default_tools` selection in the installer.

### Runtime Roles

`rc.d/roles.d/db.sh` and `web.sh` remain ideas. Define a real role and how it
differs from existing OS/host hooks and runtime config before adding a loader.

### Navi / Skim Scope

Revisit only for a concrete workflow beyond the
[documented supported scope](../dev/docs/checks.md#navi-and-skim).
A nested navi command returned by `--print` and executed later loses the adapter
environment and can lose parameter values. Shell widgets, mixed nested finders,
and general fzf compatibility remain deferred.

### Quick-Start Version Pinning

`REMOTE_SSH_REF` already selects a branch, tag, or fetchable Git ref for the
checkout. Quick-start examples still download `runme.sh` from `main`.
Decide with the release workflow whether examples should pin both the bootstrap
script and checkout to a published tag; setting `REMOTE_SSH_REF` alone does not
pin the downloaded script.

### Test Suite Organization

Deferred; excluded from the current cleanup scope.

- Split larger pytest files when they become hard to review, especially
  `dev/tests/test_tool_init_shell.py`, `dev/tests/test_install_tool_core.py`,
  and shared helpers in `dev/tests/conftest.py`
