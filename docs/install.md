# Install Flow

Remote-ssh installs into the current user's home directory and avoids package
managers, source builds, `.deb`, `.rpm`, and `.apk` packages.

The experimental [Flyline integration](shell/flyline.md) is optional and excluded
from all install profiles. Its pinned [R5 prerelease](https://github.com/fmmaciej/flyline/releases/tag/remote-ssh-v1.10.0-pr974.aae68bb4.r5)
is available through `remote-ssh install flyline`. Its source lives in the
user's Flyline fork. The library layout stores immutable releases in `INSTALL_PREFIX`
and an absolute active-file link in `INSTALL_PREFIX/.active/flyline`, with no
executable in `INSTALL_BIN_DIR`. A selected PATH Bash >= 4.4 must successfully
load the staged library in a disposable child before the active link changes.
Only macOS arm64/Bash 5.3.20 has native qualification so far. Installation and
session activation are separate operations; management still runs on Bash 3.2.

## Remote Bootstrap

`runme.sh` is the remote bootstrap script. It contains an editable
`RUNME_TOOLS` list for the first install:

```bash
curl -fsSLO https://raw.githubusercontent.com/fmmaciej/remote-ssh/main/runme.sh
chmod +x runme.sh
$EDITOR runme.sh
./runme.sh
```

Remove tools you do not want from `RUNME_TOOLS` before the first install. The
script clones or updates this repository in:

```text
~/.local/share/remote-ssh
```

Without arguments, `runme.sh` runs `remote-ssh install` with `RUNME_TOOLS`.
With arguments, it forwards them directly to `remote-ssh install`:

```bash
./runme.sh fd rg sk zoxide
./runme.sh --yes fd rg sk zoxide
./runme.sh --profile quick --yes
./runme.sh --profile full --yes
```

For a non-interactive quick install without editing the bootstrap list:

```bash
curl -fsSL https://raw.githubusercontent.com/fmmaciej/remote-ssh/main/runme.sh | bash -s -- --profile quick --yes
```

That path delegates directly to `remote-ssh install --profile quick --yes`; it does not
use the editable `RUNME_TOOLS` list.

To bootstrap from a specific branch, tag, or fetchable Git ref:

```bash
REMOTE_SSH_REF=v1.2.3 bash runme.sh
```

With `REMOTE_SSH_REF` set, `runme.sh` fetches that ref and force-checks out
`FETCH_HEAD` before running `remote-ssh install`. Without it, an existing
checkout fetches its upstream branch and resets tracked files to that upstream.

## Local Install

From a checked-out repository:

```bash
./bin/remote-ssh install --profile quick --yes
```

The installer links only the management CLI from checkout helpers; prompt,
aliases and other checkout helpers require the explicit Bash session below.
It does not change your default shell or edit startup files.

The installer also links the `remote-ssh` command into `~/.local/bin` (or
`INSTALL_BIN_DIR` when overridden). To use it in your current terminal:

```bash
export PATH="$HOME/.local/bin:$PATH"
remote-ssh guide post-install
```

Add the export to your shell startup file, such as `~/.zshrc` for Zsh or
`~/.bashrc` for interactive Bash, to keep the command available in new terminals.
The installer prints the export using the actual installation directory and
does not edit shell startup files.

SSH is optional. To start the environment locally from this checkout:

```bash
./bin/remote-ssh shell
```

After installation, use `remote-ssh shell` when the installed bin directory is
in PATH, or use the full command path printed in the footer. Both commands also
work from Zsh and start a new interactive Bash in your current directory. Use
`exit` to return to the calling shell; its directory and environment stay intact.
A nested session returns one level at a time.

The equivalent manual fallback after a default `runme.sh` installation is
`bash --rcfile "$HOME/.local/share/remote-ssh/shell/rc.sh" -i`. For another
checkout location, replace the rcfile path. Do not source `shell/rc.sh` directly
in Zsh.

`INSTALL_BIN_DIR=/custom/bin ./bin/remote-ssh install --yes fd` selects another
command/tool destination. A relative destination is relative to the install
caller's working directory. The footer prints full-path commands which work
without a PATH change; it prints a PATH export only when the effective directory
is absent from the install process's PATH. Configure that directory for future
terminals too. An earlier PATH entry can shadow `remote-ssh`.

The CLI is a symlink to the installing checkout's executable, not a standalone
copy. Keep that checkout in place: moving/deleting it can break the link; updates
in the same checkout update the command. Reinstallation reuses only the exact
direct canonical link. An existing file, directory, hard link, broken link,
link to another checkout, or relative/chained equivalent link causes an early
failure without replacement. Inspect and move/remove the entry deliberately,
or select another `INSTALL_BIN_DIR`. Changing destinations leaves older links
alone; installation does not migrate them.

`remote-ssh uninstall` removes managed tools and retains the management CLI,
checkout and SSH/Git configuration. `remote-ssh prune`, including `--apply`,
only handles eligible inactive tool release directories. Full manual removal
also requires inspecting the management symlink and removing it only if it
still points to the checkout being removed.

Install profiles are platform-filtered:

```text
mini   rg fd sd
quick  rg fd sd bat starship eza zoxide sk navi atuin
full   fd rg sd dust sk bat bottom procs yazi nvim zellij nu starship eza zoxide atuin navi bssh
```

Profiles are a one-time explicit selection:

```bash
./bin/remote-ssh install --profile mini --yes
./bin/remote-ssh install --profile full --yes
```

Tools without a matching asset for the current OS/architecture are skipped with
a clear install summary.

To install only selected tools:

```bash
./bin/remote-ssh install fd rg sk
```

For non-interactive scripts:

```bash
./bin/remote-ssh install --yes fd rg sk
```

To uninstall managed tools:

```bash
remote-ssh uninstall rg
remote-ssh uninstall --yes rg
```

Install and uninstall without a choice show usage and return 1 without writes.
Uninstall requires names and confirmation (or `--yes`), removes all proven own
active and inactive releases of those names, and ends their membership only
when removal finishes. Foreign substitutions abort before deletion; incomplete
removal retains management and protected evidence for repair. The CLI, checkout,
SSH/Git settings, shell startup files and external tools remain outside removal.

## Managed Set And Migration

Successful install adds to an automatic managed set. Profiles are one-time
shortcuts, not subscriptions. `update` refreshes the checkout, then fresh code
repairs only this set, including missing/broken installs. A completed uninstall
is not resurrected. Empty membership allows project-only update. Retired or
unsupported members remain visible/protected and make update/check fail.

State lives under `INSTALL_PREFIX/.remote-ssh-managed`, bound to physical
prefix/bin paths. Changing paths or XDG does not take ownership of another
installation. Do not edit this state. Corrupt/unreadable state is an error;
it is never silently interpreted as an empty set.

Before the first successful mutation, the installer adopts all proven active
installs, including older versions, libraries and alias-only installs. It does
not adopt inactive releases, external PATH tools, unmarked directories or names
from the old expected-tools file. That file is left unchanged; its fzf entry
can provide an informational hint only. No manual expected-tools edits are needed.
`list`/`check` can show adoption-pending results without writing migration state.

```bash
remote-ssh list
remote-ssh list --installed
remote-ssh check
remote-ssh check rg fd
remote-ssh update
```

Reports never execute managed payloads or load libraries. Check includes runtime,
Git/checkout, rc syntax, PATH and optional helper diagnostics. It returns 1 for
required environmental or selected-tool problems; an empty managed set or
optional helper warning is not itself an error. Use `install TOOL` or `update`
for repair; inspect protected foreign collisions deliberately before retrying.
Interrupted batches retain per-tool outcomes. Later lifecycle commands run the
same recovery gate before beginning another batch; unrelated operations cannot
overwrite unresolved ownership evidence. Releases remain immutable; no lifecycle
command prunes automatically. `prune` is read-only by default and `prune --apply`
removes only proven inactive releases with no active or pending claims.

### First Update From An Older Checkout

An already-running old updater may refresh this checkout and then invoke the new
bare install. It stops with usage/1 because bare install now always requires a
choice. Run `remote-ssh update` once more: the new updater adopts the proven
existing set before refresh and repairs it. Do not select a profile or edit
expected-tools to work around this one-time transition. Removed commands and
flags have no compatibility aliases.

Helper scripts remain in the checkout; use `remote-ssh guide scripts` to inspect
requirements and `remote-ssh shell` to activate the environment.

## Migrating From fzf To skim

The managed fzf package is being retired in two stages. The quick/full profiles,
SSH selection, Bash history fallback, zoxide and managed Navi integration already
use skim (`sk`). During the migration window, the frozen fzf definition remains
available so existing installations can still be inspected and uninstalled.
`remote-ssh check` prints an informational migration hint for managed fzf or a
legacy fzf migration hint, including when skim is already present.

Use the same `INSTALL_PREFIX`, `INSTALL_BIN_DIR` and XDG configuration as the
installation being migrated. Start by installing and checking skim:

```bash
remote-ssh install sk
remote-ssh check sk
```

Installation adds sk to the automatic managed set. No expected-tools edit is needed.

Review an explicit `NAVI_FINDER=fzf` in your environment/configuration or custom
commands. Use `NAVI_FINDER=skim` for the managed integration. Navi's
`NAVI_FZF_OVERRIDES` and `NAVI_FZF_OVERRIDES_VAR` names remain valid: they are
part of Navi's protocol. General `FZF_DEFAULT_OPTS` settings are not automatically
translated to skim flags. Keep an external fzf installation if you use it separately.

Open a new `remote-ssh shell` and verify the pickers you use: Navi snippet and
parameter selection/free input, Enter/Tab/cancel, `zi`/`z`, SSH selection, and
Ctrl-R when the Bash history backend is selected. Once those work, remove the
old managed fzf installation and check your saved set:

```bash
remote-ssh uninstall fzf
remote-ssh check
```

Uninstall removes only recognized files under the selected remote-ssh installation.
Updates and check do not edit expected-tools, uninstall fzf or change your finder
preference. The [retirement plan](../dev/docs/fzf-retirement-plan.md) requires
confirmation of host migration before the active fzf definition is removed.

Keep `shell/navi-bin/fzf`: it is the private adapter that runs skim for Navi.
Its name and fzf-named options are required protocol details, independently of
whether the real fzf package is managed by remote-ssh.

### Recovery After Skipping The Migration Window

A recorded fzf member remains recognized as retired after a future definition
removal. Its data stays protected; `uninstall fzf` still requires sufficient live
ownership proof. A host that skipped adoption and lost the definition cannot
infer ownership from a name or old expected-tools entry. Use the pinned recovery
checkout below for that older-host case; never weaken deletion proof.

First complete the skim installation and configuration steps above. For cleanup,
use a separate checkout pinned to the last verified recovery revision. These
commands leave the current checkout unchanged:

```bash
recovery_checkout="$(mktemp -d "${TMPDIR:-/tmp}/remote-ssh-fzf-recovery.XXXXXX")"
git clone https://github.com/fmmaciej/remote-ssh.git "$recovery_checkout"
git -C "$recovery_checkout" checkout --detach c5fa54c70fba2ca931af5b241f166fb6bec98a06
git -C "$recovery_checkout" rev-parse HEAD
```

Confirm that HEAD is exactly the full commit above. Then invoke that checkout
with the original installation paths and an explicit `REMOTE_ENV_DIR`. The
latter prevents an inherited session variable from redirecting recovery to the
new checkout without the definition:

```bash
REMOTE_ENV_DIR="$recovery_checkout" \
  INSTALL_PREFIX="${INSTALL_PREFIX:-$HOME/.local/opt}" \
  INSTALL_BIN_DIR="${INSTALL_BIN_DIR:-$HOME/.local/bin}" \
  "$recovery_checkout/bin/remote-ssh" uninstall fzf
```

For a custom installation, export its actual prefix/bin paths before running
the command; the defaults above apply to ordinary installations. Retain the
same `XDG_CONFIG_HOME` used for the saved tool set. Review the tool's normal
confirmation prompt. The pinned cleanup preserves skim and independently
installed fzf. This is a one-time recovery procedure, not a second maintained
installer catalog.

Skim's `.tar.xz` release archives require tar with xz support. GNU tar also
needs `xz` in PATH; macOS tar has built-in support. A failed extraction leaves
the previous installation intact.

## Installed Paths

Installed tool versions are placed under:

```text
~/.local/opt/<tool>-<version>
```

Symlinks are created in:

```text
~/.local/bin
```

New releases contain a `.remote-ssh-release` ownership record identifying the
tool, version, layout, and relative executable path. Neovim preserves its full
package layout, so its symlink targets `<release>/bin/nvim`.

Reinstalls may create `<tool>-<version>.<PID>-<RANDOM>` directories, where PID
and RANDOM contain decimal digits only. Other suffixes are not recognized as
installer-generated suffixes. The ownership record must match the full release
version and directory name; a different version sharing the pinned version's
prefix does not satisfy the pinned install check.

Installation locations may be directory symlinks. `prune` and `uninstall`
scan the physical prefix's direct children and keep child directory symlinks
protected. `check` recognize equivalent bin paths by filesystem
identity, including directory symlinks and relative PATH entries. An empty
PATH entry denotes the current directory. Diagnostic headers retain configured
paths; release listings use physical paths.

Removal requires a valid ownership record inside a direct child of the install
prefix. Files, directory symlinks, foreign directories such as `rg-personal-notes`,
and older releases without a record are protected. Active binary and alias
symlinks protect their entire release during prune, including bundled runtimes.
This protection also covers links to helper programs or data files inside a
release, even when there is no link to its main executable. Reference detection
does not grant ownership: deletion still requires the valid ownership record
described above. Protected paths are compared literally using Bash built-ins.

Older unmarked releases remain usable and are left for manual review. Reinstall
a tool to create a new marked release while retaining automatic membership:

```bash
remote-ssh install rg
```

The old unmarked directory remains protected; reinstalling does not adopt or
delete it automatically.

Old inactive release directories can be reported with:

```bash
remote-ssh prune
```

Deletion requires:

```bash
remote-ssh prune --apply
```

Both prune modes require an existing, readable and searchable `INSTALL_BIN_DIR`.
Missing directories, insufficient permissions, or failed active-link enumeration
abort with a nonzero exit status before reporting candidates or removing releases.
A successfully read empty directory means there are no active tool links; write
permission on the bin directory is not required. Directory symlinks and custom
alias names are supported. Inventory failures do not count as an empty directory.

## Updating

To update an installed checkout:

```bash
remote-ssh update
```

This discards local edits to tracked files in the remote-ssh checkout and
recreates them from the upstream branch. Untracked files are reported but left
in place.

A failed fetch or reset stops the update before installation and before marking
the checkout current. After a successful reset, installation runs in a new
process using the refreshed checkout's code. Installation failures are returned
to the caller.

To only check whether the upstream checkout changed:

```bash
remote-ssh update check
```
