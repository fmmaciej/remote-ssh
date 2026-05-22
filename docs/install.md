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

With `REMOTE_SSH_REF` set, `runme.sh` fetches that ref and checks out
`FETCH_HEAD` before running `remote-ssh install`. Without it, an existing
checkout uses `git pull --ff-only`.

## Local Install

From a checked-out repository:

```bash
./bin/remote-ssh install --profile quick --yes
```

Install profiles are platform-filtered:

```text
mini   rg fd sd
quick  rg fd sd bat starship eza zoxide navi atuin
full   fd rg sd dust fzf bat yazi nvim zellij nu starship eza zoxide atuin navi tspin vector
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
detected from symlinks in `~/.local/bin`. It removes matching release
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

Helper scripts such as `ci-run`, `helm-chart-diff`, and `ssh-pick` are part of
the remote-ssh checkout. There is no `--scripts` install flag; use
`remote-ssh guide scripts` to inspect helper requirements.

## Installed Paths

Installed tool versions are placed under:

```text
~/.local/opt/<tool>-<version>
```

Symlinks are created in:

```text
~/.local/bin
```

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

To only check whether the upstream checkout changed:

```bash
remote-ssh update check
```
