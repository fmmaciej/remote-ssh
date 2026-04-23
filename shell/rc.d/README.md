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

Keep `aliases.sh` focused on aliases and simple command wrappers. Shell runtime
initialization such as `eval "$(tool init ...)"`, shell hooks, and tool-specific
session exports belongs in `rc.d/*.sh`.

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

## Git Config

Git config is no longer injected from `rc.sh`.

Use the explicit setup command instead:

```bash
remote-ssh-git-setup
```

This adds `dots/git/config.base` to your global Git config via
`include.path` and creates `dots/git/user.local` from the example if it is
missing.

Files:

```text
dots/git/config.base
dots/git/user.local.example
dots/git/user.local
```

`user.local` is intentionally local and not tracked by Git.

## fzf and Atuin

`fzf` stays enabled as a general-purpose picker and as a dependency for tools
such as `sshf`.

`atuin` is loaded separately by `23-atuin.sh` in interactive shells. When
`atuin` exists in `PATH`, it owns shell history integration. The `Ctrl-r`
history picker from `20-fzf.sh` is then skipped and works only as a fallback on
hosts without `atuin`.

In interactive Bash sessions, `06-bash-history.sh` keeps session history in
memory but disables writes to the standard Bash history file. Persistent shell
history is intentionally left to Atuin in remote-ssh sessions.

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
