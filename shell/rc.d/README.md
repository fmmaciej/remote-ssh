# rc.d flow

`rc.sh` loads shell customizations in this order:

1. `shell/env.sh`
2. `shell/aliases.sh`
3. `shell/rc.d/*.sh`
4. `shell/rc.d/os.d/<os>.sh`
5. `shell/rc.d/host.d/<hostname>.sh`

`<os>` is detected from `uname -s` and normalized to `linux` or `darwin`
for the common cases.

`<hostname>` comes from `hostname -s` with a fallback to `hostname`.

Missing directories and missing files are ignored. This keeps the default
runtime small while allowing local overrides on specific operating systems or
hosts.

## Plugin files

Each file should be safe to source more than once and should handle its own
dependencies:

```bash
# shellcheck shell=bash

ensure_this_file_sourced

have atuin || return 0
eval "$(atuin init bash)"
```

Do not install dependencies from `rc.d` files. Installation belongs to
`install.sh` and `tools/defs`.

## OS files

Use `os.d` for platform-specific runtime behavior:

```text
shell/rc.d/os.d/linux.sh
shell/rc.d/os.d/darwin.sh
```

Example files are provided as `.example` files and are not loaded until copied
to `.sh`.

## Host files

Use `host.d` for one machine only:

```text
shell/rc.d/host.d/<hostname -s>.sh
```

Example files are provided as `.example` files and are not loaded until copied
to `.sh`.

## Session Git Config

Use `remote_git_config_add` when Git settings should apply only to the current
remote-ssh session and child processes. It uses Git's environment config
interface and does not write to `~/.gitconfig`.

Example `host.d/<hostname>.sh`:

```bash
# shellcheck shell=bash

ensure_this_file_sourced

have git || return 0

remote_git_config_add user.name "Maciej"
remote_git_config_add user.email "maciej@fmmaciej.com"
remote_git_config_add init.defaultBranch "main"
remote_git_config_add pull.ff "only"
```

Check active values:

```bash
git config user.name
git config user.email
```

The default Git plugin, `12-git.sh`, sets session-scoped workflow defaults:

```bash
pull.rebase true
rebase.autoStash true
fetch.prune true
push.autoSetupRemote true
init.defaultBranch main
core.editor "${EDITOR:-vim}"
```

Host files are loaded after `rc.d/*.sh`, so they can append a more specific
value for the same key:

```bash
remote_git_config_add core.editor "vim"
remote_git_config_add user.name "Maciej"
remote_git_config_add user.email "maciej@fmmaciej.com"
```

## fzf and Atuin

`fzf` stays enabled as a general-purpose picker and as a dependency for tools
such as `sshf`.

`atuin` is loaded separately by `23-atuin.sh` in interactive shells. When
`atuin` exists in `PATH`, it owns shell history integration. The `Ctrl-r`
history picker from `20-fzf.sh` is then skipped and works only as a fallback on
hosts without `atuin`.

Atuin stores history in its own database and does not automatically import the
old shell history. On first use, flush the current shell history and import it:

```bash
# bash
history -w
atuin import bash

# zsh
fc -W
atuin import zsh
```

For a generic import, use:

```bash
atuin import auto
```
