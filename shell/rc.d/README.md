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
`remote-ssh install` and `tools/defs`.

Keep `aliases.sh` focused on aliases and simple command wrappers. Shell runtime
initialization such as `eval "$(tool init ...)"`, shell hooks, and tool-specific
session exports belongs in `rc.d/*.sh`.

## Update check

`04-update-check.sh` runs only in interactive shells. It reads a small cache
from `${XDG_STATE_HOME:-$HOME/.local/state}/remote-ssh/update-check` and, when
that cache is stale, refreshes it in the background without writing to the
terminal.

The refresh uses:

```bash
remote-ssh update check --quiet --write-cache
```

It never runs `git pull`, never installs tools, and should not block shell
startup. Disable it before loading `rc.sh` when needed:

```bash
export REMOTE_SSH_UPDATE_CHECK=0
```

The default interval is one day. Override it with:

```bash
export REMOTE_SSH_UPDATE_CHECK_INTERVAL=3600
```

## Runtime config

`shell/env.sh` reads `${XDG_CONFIG_HOME:-$HOME/.config}/remote-ssh/config`
before `rc.d` hooks run. The config file supports allowlisted `KEY=value`
settings only; it is not sourced as shell. When a key appears more than once,
the last allowlisted line wins. Existing environment variables take precedence
over config values. After `REMOTE_SSH_CONFIG=0; rcrc`, values previously loaded
only from this config return to defaults while manually exported values remain
environment values.

Inspect effective config values with:

```bash
remote-ssh guide config
```

Disable config loading before loading `rc.sh` when needed:

```bash
export REMOTE_SSH_CONFIG=0
```

## Welcome

`08-welcome.sh` runs only in interactive shells and delegates the runner to
`shell/welcome/runner.sh`. `shell/welcome/` contains internal library modules;
executable status modules live in `shell/welcome.d/`. The runner executes
bundled modules from `shell/welcome.d/`, then user executable modules from
`${XDG_CONFIG_HOME:-$HOME/.config}/remote-ssh/welcome.d`. Bundled modules render
the login status for remote-ssh, hardware, SSH agent, and Git session config.
The `next` line is reserved for actionable problems; disabled or missing update
cache state and standalone SSH agent status are informational.
Use `shell/welcome.d/user-module.sh.example` as a starting point for custom
user-local welcome lines.
User-local modules should stay fast, local-only, and noninteractive because they
run during shell startup.

Disable it before loading `rc.sh` when needed:

```bash
export REMOTE_SSH_WELCOME=0
```

Other welcome toggles:

```bash
export REMOTE_SSH_WELCOME_USER=0
export REMOTE_SSH_WELCOME_BANNER=0
export REMOTE_SSH_WELCOME_COLOR=0
export REMOTE_SSH_WELCOME_DEBUG=1
export NO_COLOR=1
```

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
remote-ssh git setup
```

This adds `dots/git/config.base` to your global Git config via
`include.path` and creates `dots/git/user.local` from the example if it is
missing.

In remote-ssh shells, `dots/git/user.local` is also applied as a session Git
identity override through `GIT_CONFIG_COUNT`. This lets the remote-ssh identity
win over per-repository `.git/config` values without writing to those
repositories. Disable it before loading `rc.sh` if needed:

```bash
export REMOTE_SSH_ENABLE_GIT_SESSION_IDENTITY=0
```

It also creates `dots/ssh/config.local` from the example if needed and adds an
`Include` line to `~/.ssh/config`. Use that file for account-specific Git SSH
aliases:

```sshconfig
Host github.com-myuser
  HostName github.com
  User git
  IdentitiesOnly no
```

Then point repositories at the alias:

```bash
git remote set-url origin git@github.com-myuser:OWNER/REPO.git
```

Files:

```text
dots/git/config.base
dots/git/user.local.example
dots/git/user.local
dots/ssh/config.example
dots/ssh/config.local
```

`user.local` and `config.local` are intentionally local and not tracked by Git.

## fzf and Atuin

`fzf` stays enabled as a general-purpose picker and as a dependency for tools
such as `ssh-pick`.

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
