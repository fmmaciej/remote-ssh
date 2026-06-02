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

Set `SSH_FIND_SSH_CONFIG` to use a specific OpenSSH config. Set
`SSH_FIND_BSSH_CONFIG` to use a specific bssh config. Set `SSH_HOSTS_FILE` to
test or override the hosts-file lookup.

It currently uses `scripts/ssh_find.py` plus `ssh -G`, so this helper requires
`python3`, `ssh`, and `fzf`.

## ssh-pick

`ssh-pick` calls `ssh-find`, then connects to the selected record. OpenSSH
records connect through their alias so options such as `IdentityFile`,
`ProxyJump`, and `RemoteCommand` stay active. bssh records connect directly to
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
