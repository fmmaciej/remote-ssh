# Install Flow

Remote-ssh installs into the current user's home directory and avoids package
managers, source builds, `.deb`, `.rpm`, and `.apk` packages.

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
./runme.sh fd rg fzf zoxide
./runme.sh --yes fd rg fzf zoxide
./runme.sh --profile quick --yes
./runme.sh --full --yes
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
quick  rg fd sd bat starship eza zoxide navi atuin
full   fd rg sd dust fzf bat bottom procs yazi nvim zellij nu starship eza zoxide atuin navi bssh
```

`--full` is a compatibility alias for `--profile full`:

```bash
./bin/remote-ssh install --profile mini --yes
./bin/remote-ssh install --profile full --yes
./bin/remote-ssh install --full --yes
```

Tools without a matching asset for the current OS/architecture are skipped with
a clear install summary.

To install only selected tools:

```bash
./bin/remote-ssh install fd rg fzf
```

For non-interactive scripts:

```bash
./bin/remote-ssh install --yes fd rg fzf
```

To uninstall managed tools:

```bash
remote-ssh uninstall rg
remote-ssh uninstall --yes rg
remote-ssh uninstall --yes
```

Without explicit tool names, `remote-ssh uninstall` removes all managed tools
detected from symlinks in `~/.local/bin` and valid ownership records. It removes managed release
directories under `~/.local/opt` and updates `expected-tools`; it does not
remove the remote-ssh checkout or SSH/Git configuration.

## Expected Tools

The selected tool set is saved in:

```text
~/.config/remote-ssh/expected-tools
```

The file contains one tool per line. Blank lines and `#` comments are ignored.

After the first install, these commands use the saved expected tools when no
explicit tool list is provided:

```bash
remote-ssh install
remote-ssh update
remote-ssh check
remote-ssh doctor
```

If no expected tools config exists, `remote-ssh install` asks you to choose
tools explicitly or run:

```bash
remote-ssh install --profile quick --yes
```

Helper scripts such as `ssh-find` and `ssh-pick` are part of the remote-ssh
checkout. There is no `--scripts` install flag; use `remote-ssh guide scripts`
to inspect helper requirements.

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

Removal requires a valid ownership record inside a direct child of the install
prefix. Files, directory symlinks, foreign directories such as `rg-personal-notes`,
and older releases without a record are protected. Active binary and alias
symlinks protect their entire release during prune, including bundled runtimes.

Older unmarked releases remain usable and are left for manual review. Reinstall
a tool to create a new marked release without changing `expected-tools`:

```bash
FORCE=1 remote-ssh tool install rg
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
