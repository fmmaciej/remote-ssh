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

## ssh-pick

`ssh-pick` reads host aliases from `$HOME/.ssh/config`, including `Include`
files, and ignores wildcard entries such as `Host *`. The picker shows matching
`HostName`, `/etc/hosts` IP addresses, `user`, and `port` when they can be
resolved locally.

Examples:

```bash
ssh-pick
ssh-pick --query lab-a
ssh-pick --query 10.1.2
ssh-pick --query 10.1.2.3 uptime
```

`--query` filters by alias, resolved hostname, or IP address. If the query has
one match, `ssh-pick` connects immediately; otherwise it opens `fzf` with the
matching rows.

Set `SSH_PICK_CONFIG` before loading `rc.sh` to use a specific OpenSSH config
for the picker. If it is unset, `ssh-pick` uses `SSH_CONFIG`, then
`$HOME/.ssh/config`, then `BSSH_SSH_CONFIG` when that file exists. Set
`SSH_HOSTS_FILE` to test or override the hosts-file lookup; it defaults to
`/etc/hosts`.

It currently uses `scripts/ssh_hosts.py` plus `ssh -G`, so this helper requires
`python3`, `ssh`, and `fzf`.

The dependency is intentional for now because the parser is more reliable than
a shell-only version; a future version may replace it or add a fallback.
