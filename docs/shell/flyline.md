# Optional Flyline

Back: [Shell Runtime](../shell.md)

The optional integration uses Flyline **1.10.0 + PR #974**, with recorded vi
and unload fixes. Readline remains the default. The implementation and native
macOS arm64 pilot are ready for review. Source and developer builds now live in
the user's [Flyline fork](https://github.com/fmmaciej/flyline/tree/remote-ssh-vim),
preserving upstream history. The pinned [R5 prerelease](https://github.com/fmmaciej/flyline/releases/tag/remote-ssh-v1.10.0-pr974.aae68bb4.r5)
and its production tool definition are available for explicit installation. See the
[fork validation and support record](../../dev/docs/flyline-fork-integration-record.md).

The qualified combination is macOS arm64 with Homebrew Bash 5.3.20. System
macOS Bash 3.2 keeps Readline. Installation does not install or upgrade Bash.
Linux, weak remote hosts, Intel macOS and SSH transport are unverified.

Explicitly install and enable it in a new shell:

```bash
remote-ssh tool install flyline
REMOTE_SSH_ENABLE_FLYLINE=1 remote-ssh shell
```

The toggle defaults to `0` and can also be set in the allowlisted
`~/.config/remote-ssh/config`. It requests activation only: a missing library,
unsupported terminal/Bash, external history owner, or existing line editor
causes activation to be skipped. Inspect the current process with:

```bash
printf '%s: %s\n' "$REMOTE_SSH_FLYLINE_STATE" "$REMOTE_SSH_FLYLINE_REASON"
```

Use the same exported `INSTALL_PREFIX` for installation and shell startup when
using a custom prefix. No `flyline` executable is put in PATH. `check` and
`doctor` report library installation; they do not establish that another
process has activated it or that its Bash is ABI compatible.

Flyline explicitly enables its Vim keymap. Escape enters Normal mode; `i`/`a`
return to insertion. The patched workflow covers counted movement, change,
yank/paste, undo, redo, dot-repeat, `k`/`j` history and `/`/`?` search. This is
the bounded experimental PR implementation, not complete Vim compatibility.
Command-mode Ctrl-R performs the PR's redo. Clean Bash Readline normally uses
Ctrl-R for history search; do not infer identical bindings between editors.

Atuin retains history storage, hooks, import/sync policy, exit status and
duration recording. Ctrl-R in insert/Emacs mode opens its editable search,
unless `ATUIN_NOBIND` is set. It never submits the selected command itself.
With Bash history, Ctrl-R uses the existing skim widget when available,
otherwise Flyline's native search. Up remains ordinary history navigation.
Explicit empty `HISTFILE` and `/dev/null` remain valid choices. Flyline JSONL
storage is disabled; no history migration occurs.

The editor and history backend are selected once per Bash process. `rcrc`
preserves that choice and later key edits. Updates/reinstalls affect new shells;
open shells retain the library they loaded. Start a new shell after changing
toggles, PATH, or executable availability. If Atuin disappears, the current
session does not automatically switch storage or reassign Ctrl-R.

Flyline supplies editing, highlighting, and Tab UI. Installed Bash completion
functions and file completion still supply candidates. It does not define
parameters for every command. Carapace remains a separate planned provider;
the pilot tested its default callback, but this change does not install or
activate it. bash-completion and flycomp are not required. Automatic and inline
suggestions, flycomp/download prompts, tutorial, mouse capture and animations
are disabled in the managed profile; the prompt stays with Starship.

To return to the default editor:

```bash
REMOTE_SSH_ENABLE_FLYLINE=0 remote-ssh shell
```

Close the old shell when convenient. Uninstalling removes managed active links
and releases; it does not unload code from running shells. `prune` protects
active library links and defaults to a dry run.
