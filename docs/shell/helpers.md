# Helpers

Back: [Shell Runtime](../shell.md)

The remote-ssh shell loads a few small helpers:

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
`fzf` and shows:

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

The optional argument sets the initial `fzf` query. It does not auto-select a
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
`python3`, `ssh`, and `fzf`.

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

When remote-ssh initializes Atuin successfully, it owns persistent command
history and Bash file writes are disabled for that integration's lifetime.
When our integration is unavailable, disabled with `REMOTE_SSH_ENABLE_ATUIN=0`,
or fails to initialize, Bash keeps its normal history file. fzf supplies Ctrl-R
when available, unless independently initialized Atuin owns the bindings.

An explicit `HISTFILE` is preserved for fallback, including an empty value or
`/dev/null` to disable file persistence. Reloading with `rcrc` does not duplicate
Atuin hooks; disabling or removing Atuin restores fallback history and its
previous arrow key bindings unless those bindings were subsequently changed by
the user. Reload also detects a removed executable still cached by Bash.

Re-enabling Atuin in the same shell reattaches its saved hooks and bindings
without running the upstream initializer again. User callbacks are preserved,
including callbacks added while Atuin was active. If reattachment cannot find
a required Atuin helper, Bash history and the available fzf fallback remain
enabled. Atuin initialized independently before remote-ssh keeps its own
registrations and bindings, including its default Ctrl-R search. The fzf
fallback does not replace these bindings, even when remote-ssh's Atuin toggle
is disabled. A failed remote-ssh initialization still enables the usual fallback.

When disabling our integration with `rcrc`, the current command's history entry
is finished at the following prompt, using that command's exit status. Later
time spent in the fallback is excluded. A temporary first prompt statement
handles owned history completion before user prompt commands, including a
multiline `PROMPT_COMMAND` that forwards dispatch through a function or script.
The owned registration is removed after completion. User precmd callbacks run
at their normal dispatch point: a prefix preparing data for a wrapper still
runs before those callbacks. Status, pipeline metadata, and the previous argument
delivered to callbacks follow the normal dispatcher for that prompt layout.
On Bash 5.1 and newer, a prepended completion boundary uses a separate prompt
array entry so Bash preserves the inputs of the user's prefix or wrapper.
Cleanup restores the original prompt layout while retaining user edits. Bash
3.2 retains the upstream dispatcher's pipeline capture behavior.
Disabling and re-enabling within one input line still finishes the entry once.

Completion is best-effort. The pending entry is tied to the outer interactive
call site at the beginning of the prompt, independently of history settings. If
the executable, completion helper, or prompt hook is unavailable, or the completion
context is uncertain, remote-ssh drops the local pending association. A directly
entered multiline block may change that call site before the prompt; in that
case the local pending association is dropped. Multiline functions and sourced
scripts invoked from one input line keep the same outer call site.

Removing all prompt dispatch after disable also removes the opportunity for
immediate cleanup. The next reload or resumed completion callback discards an
expired association before trying to finish it. Old registrations restored
directly or through a cached wrapper retain normal prompt dispatch, including
after reactivation. Exact owned statements are removed from the current prompt;
cached user function bodies are preserved and can replay compatible statements
again. The backend may retain an unfinished entry, but a later command's status
or time in the fallback is never used to finish that detached ID.

On Bash with `bind -X`, restoration includes shell commands installed with
`bind -x`, Readline functions, macros, and unbound keys. On older Bash, including
macOS Bash 3.2, shell-command bindings cannot be enumerated. If any tracked
binding is unreadable, remote-ssh passes `--disable-up-arrow`: Up and vi-command
`k` stay under user control while Atuin still records history. remote-ssh leaves
Ctrl-R out of its own Atuin initialization.

## Tmux

The bundled configuration locates the checkout from the configuration file's
path, including paths with spaces. New panes start `/bin/bash` with that
checkout's `shell/rc.sh`. `prefix+r` reloads the same checkout's configuration.
`prefix+q` asks for confirmation before restarting and killing the current pane
process. Loading the configuration requires tmux support for `current_file`
and format expansion in `set-option -F`.
