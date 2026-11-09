# Helpers

Back: [Shell Runtime](../shell.md)

The remote-ssh shell loads a few small helpers:

Optional [Flyline](flyline.md) changes the editor and Tab UI, while these
helpers remain shell commands/functions. It adds no executable wrapper.
`rcrc` preserves the selected editor/history backend; start a new disabled
shell with `REMOTE_SSH_ENABLE_FLYLINE=0 remote-ssh shell` to return to Readline.

- `remote-ssh`: main entrypoint for setup, install, uninstall, check, ssh, git,
  update, doctor, prune, and scripts.
- `remote-ssh guide`: show loaded aliases, functions, paths, tools, and Git/SSH
  notes.
- `remote-ssh guide starship`: explain the bundled Starship prompt symbols.
- `cheats`: open private `navi` cheatsheets from `dots/navi/cheats`.
- `log` and `logrun`: capture command output to a file while still streaming
  it.
- `bssh`: run `bssh` with stream output and the shared SSH config.
- `bssh-ip`: print the resolved SSH hostname, user, and port for a host.
- `ssh-find`: find an SSH host by alias, hostname, or IP address.
- `ssh-pick`: connect to an SSH host selected through `ssh-find`.

To list script-backed helper commands and shell functions:

```bash
remote-ssh scripts --list
```

For the helper guide:

```bash
remote-ssh guide scripts [helper]
```

`remote-ssh --help` and `remote-ssh help` are intentionally short CLI usage
outputs. Use `remote-ssh guide` for the longer, dynamic guide generated from
the currently loaded shell configuration.

To reprint the post-install setup instructions later, run:

```bash
remote-ssh guide post-install
```

## Cheatsheets

Private cheatsheets are stored in:

```text
dots/navi/cheats
```

Remote-ssh shells prepend that directory to `NAVI_PATH`, so `navi` and the
`cheats` alias can search project-local snippets without copying them into a
global user directory.

Sessions default `NAVI_FINDER` to `skim`, so both `navi` and `cheats` use `sk`.
Set `NAVI_FINDER` before starting the session or use `navi --finder` to select
another supported finder explicitly. The session setting takes precedence over
the finder in navi's YAML configuration.

The integration supports snippet selection, suggested and free-text parameter
values, Enter/Tab acceptance, cancellation, and automatic single-result
selection with the pinned navi and skim versions. `navi --print` returns ordinary
commands with their substituted parameters. Quote placeholders in cheatsheets
when a parameter should remain one shell argument, for example `"<directory>"`.

Navi's picker uses `--height=40% --reverse --border` independently of
`SKIM_DEFAULT_OPTIONS` and `SKIM_OPTIONS_FILE`. Customize it through navi's
`--fzf-overrides` and `--fzf-overrides-var` options (or corresponding navi
configuration). Ordinary `sk` commands keep their global settings. From the
session shell, `navi --finder fzf` uses the real fzf executable if installed.

Nested navi commands are supported while executing inside the original navi
process tree. A nested navi command returned by `--print` and executed later
does not retain this integration and can lose parameter values. Mixed finders
inside nested calls, shell widgets, and general fzf compatibility are outside
the supported scope. Outside a remote-ssh session, `navi --finder skim` alone
does not provide this integration.

See [developer checks](../../dev/docs/checks.md#navi-and-skim) for the adapter
contract and offline acceptance tests.

## Directory Selection

The `zi` directory picker and Bash's interactive `z` completion use zoxide's
ranked `query --list` output with skim. Both replace generated selection paths
that call fzf internally. `zi` keeps `_ZO_ECHO=1` support. Bash versions where
zoxide enables completion (4.4+) retain ordinary directory completion and its
Readline helpers; cancellation redraws the current line. Plain `z` and zoxide's
tracking hooks continue to use the normal initialization.

## bssh

`bssh` wraps the installed `bssh` binary with:

```bash
bssh --stream --ssh-config "$BSSH_SSH_CONFIG" <args>
```

`BSSH_SSH_CONFIG` defaults to:

```text
$HOME/.ssh/config.d/00-all.conf
```

Set `BSSH_SSH_CONFIG` before loading `rc.sh` to use a different config file.

Examples:

```bash
bssh lab
bssh-ip lab-a
```

`bssh-ip HOST` uses `ssh -G -F "$BSSH_SSH_CONFIG" HOST` and prints the resolved
`HostName`, plus `user` and `port` when OpenSSH reports them.

## ssh-find

`ssh-find` reads host aliases from `$HOME/.ssh/config`, including `Include`
files, plus the supported subset of `$HOME/.config/bssh/config.yaml`. It opens
`sk` and shows:

```text
alias  address  user  source
```

The selected row is printed as a full tab-separated record for other helpers.
`ssh-find` does not connect anywhere.

The first seven fields are alias, address, user, source, port, connection kind,
and connection target. OpenSSH records append an eighth field with the absolute
config path only when a config override was explicitly selected. Automatic
selection and direct bssh records retain seven fields. Optional user and port
fields may be empty.

Examples:

```bash
ssh-find
ssh-find lab-a
ssh-find 10.1.2
```

The optional argument sets the initial `sk` query. It does not auto-select a
single match; press Enter to choose a row.

OpenSSH entries resolve `HostName`, `User`, and `Port` through `ssh -G`. bssh
entries support `defaults.user`, `defaults.port`, `clusters.<name>.user`,
`clusters.<name>.port`, and `clusters.<name>.nodes` as strings
(`user@host:port`, `host:port`, `host`) or simple maps (`name`/`alias`, `host`,
`user`, `port`). `/etc/hosts` is used only to map a hostname to a display IP.

Set `SSH_FIND_SSH_CONFIG` to use a specific OpenSSH config; `SSH_CONFIG` is the
fallback selector. Empty values are ignored. Without either override, aliases
come from `~/.ssh/config` and resolution uses ordinary `ssh -G` configuration
loading, including system defaults. Set
`SSH_FIND_BSSH_CONFIG` to use a specific bssh config. Set `SSH_HOSTS_FILE` to
test or override the hosts-file lookup.

It currently uses `scripts/ssh_find.py` plus `ssh -G`, so this helper requires
`python3`, `ssh`, and `sk`.

## ssh-pick

`ssh-pick` calls `ssh-find`, then connects to the selected record. OpenSSH
records connect through their alias so options such as `IdentityFile`,
`ProxyJump`, and `RemoteCommand` stay active. Automatic selection connects using
`ssh alias`, preserving ordinary configuration loading. Explicit selection uses
the same `ssh -F CONFIG` override for resolution and connection, even when CONFIG
is `~/.ssh/config`. As with OpenSSH itself, `-F` excludes system-wide SSH config.
bssh records connect directly to
`[user@]host` with `-p PORT` when a port is known.

Examples:

```bash
ssh-pick
ssh-pick --query lab-a
ssh-pick --query 10.1.2
ssh-pick --query 10.1.2.3 uptime
```

The dependency is intentional for now because the parser is more reliable than
a shell-only version; a future version may replace it or add a fallback.

## History

The history backend is selected once during the first interactive remote-ssh
setup in each Bash process. Working Atuin owns persistent history in its local
database, with normal directory, host, exit-status, and duration metadata.
Bash keeps in-memory history while its history-file writes are suppressed.
`rcrc` reloads configuration without changing this choice or rebinding keys.

To select Bash history for a new shell:

```bash
REMOTE_SSH_ENABLE_ATUIN=0 remote-ssh shell
```

If Atuin is initially disabled, missing, or fails to initialize, Bash retains
its history file and skim supplies Ctrl-R when available; otherwise native
Readline history stays available. An explicit `HISTFILE` is preserved, including
an empty value or `/dev/null`. Installing Atuin, changing PATH or the toggle,
or removing its executable takes effect for backend selection in a new shell.
An active Atuin shell does not automatically fail over if the executable is
removed or breaks; recording may fail, so start a new shell promptly.

remote-ssh binds only Ctrl-R in Emacs and vi insert modes to Atuin. Up remains
ordinary history navigation, and vi command-mode `k`, `/`, and Ctrl-R redo keep
their existing behavior. `ATUIN_NOBIND` suppresses these managed Atuin bindings.
Later user binding edits survive reload. Atuin initialized independently before
remote-ssh retains its own hooks, keys, config, and history-file policy, even
when remote-ssh's Atuin switch is disabled.

First successful owned setup runs `atuin import auto` once per host state
marker at `${XDG_STATE_HOME:-$HOME/.local/state}/remote-ssh/atuin-import-auto.done`.
Set `REMOTE_SSH_ENABLE_ATUIN_AUTO_IMPORT=0` before starting the shell to skip it.
A failed import is retried in a new shell. Existing databases, import markers,
credentials, and database locations are preserved. Automatic synchronization
is disabled in the bundled config; manual `atuin sync` remains available.

After updating from the older integration, exit existing shells and open new
ones. Reloading old detach/reattach callbacks with `rcrc` is unsupported.

## Tmux

The bundled configuration locates the checkout from the configuration file's
path, including paths with spaces. New panes start `/bin/bash` with that
checkout's `shell/rc.sh`. `prefix+r` reloads the same checkout's configuration.
`prefix+q` asks for confirmation before restarting and killing the current pane
process. Loading the configuration requires tmux support for `current_file`
and format expansion in `set-option -F`.
