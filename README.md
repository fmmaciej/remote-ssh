# Remote-ssh

Remote-ssh is a lightweight, shell-first framework for bootstrapping useful SSH
sessions on remote machines. It provides a small Bash-based session environment,
bundled dotfiles, helper commands, and pinned standalone CLI tools downloaded
from GitHub Releases.

The shell environment is Bash-first. Start it with
`bash --rcfile <remote-ssh>/shell/rc.sh -i`; sourcing `shell/rc.sh` from Zsh is
not supported.

The runtime target is a fresh or minimally configured Unix-like host. The normal
installation path intentionally avoids package managers, source builds, `jq`,
and GitHub API discovery. Python is not needed for the core installer, but the
optional `ssh-find` and `ssh-pick` helpers currently use a Python parser plus
`ssh -G` for SSH config lookup.

## Why This Exists

I often work on remote, shared machines where I do not have a dedicated user
account. Over the years I built a small personal workflow around fast shell
navigation, search, editing, Git, logs, and pinned CLI tools. Remote-ssh keeps
that workflow portable and isolated, so I can make a temporary session feel
familiar without changing the machine globally or disrupting other users.

It is worth trying if you work on shared accounts, move between short-lived
remote machines, want your own tools without using the system package manager,
or need a repeatable shell setup that stays out of everyone else's way.

## Quick Start

Download `runme.sh`, review or edit the `RUNME_TOOLS` list, then run it:

```bash
curl -fsSLO https://raw.githubusercontent.com/fmmaciej/remote-ssh/main/runme.sh
chmod +x runme.sh
$EDITOR runme.sh
./runme.sh
```

The script clones or updates this repository in:

```text
~/.local/share/remote-ssh
```

Then it runs `remote-ssh install` with the selected tools. The installer prints
the final tool list and asks for confirmation before installing.

If you already know the desired set, pass tools directly:

```bash
./runme.sh fd rg fzf zoxide
./runme.sh --yes fd rg fzf zoxide
```

For a non-interactive quick install without editing the bootstrap list:

```bash
curl -fsSL https://raw.githubusercontent.com/fmmaciej/remote-ssh/main/runme.sh | bash -s -- --profile quick --yes
```

## Local Install

From a checked-out repository:

```bash
./bin/remote-ssh install --profile quick --yes
./bin/remote-ssh install --profile mini --yes
./bin/remote-ssh install --full --yes
./bin/remote-ssh install fd rg fzf
./bin/remote-ssh install --yes fd rg fzf
```

The selected tool set is saved in:

```text
~/.config/remote-ssh/expected-tools
```

Installed tool versions are placed under `~/.local/opt/<tool>-<version>`, with
symlinks in `~/.local/bin`.

## Main Commands

```bash
remote-ssh install [tool ...]
remote-ssh install --profile <name> [--yes]
remote-ssh install --full [--yes]
remote-ssh setup
remote-ssh uninstall [--yes] [tool ...]
remote-ssh tool list
remote-ssh check [--strict] [tool ...]
remote-ssh ssh setup
remote-ssh ssh status [host]
remote-ssh git setup
remote-ssh git status [ssh-host]
remote-ssh update
remote-ssh update check
remote-ssh doctor
remote-ssh prune [--apply]
remote-ssh scripts --list
remote-ssh guide [section]
remote-ssh help
```

`remote-ssh --help` is intentionally short. Use `remote-ssh guide` for a dynamic
guide generated from the currently loaded shell configuration.

## Runtime Requirements

- `bash`
- `git` for `runme.sh`, `remote-ssh update`, and update checks
- `curl`
- `tar`
- `find`
- `sed`
- `grep`
- `date`
- `unzip` only when the selected asset is a `.zip`
- `sha256sum` or `shasum` when the selected asset has a pinned checksum

Optional helper requirements:

- `python3`, `ssh`, and `fzf` for `ssh-find` and `ssh-pick`

## More Documentation

- [Install flow](docs/install.md)
- [Shell helpers and runtime behavior](docs/shell.md)
- [Helper scripts](docs/scripts.md)
- [Tool definitions and pinned assets](docs/tools.md)
- [Developer tooling](dev/README.md)
- [TODO](docs/TODO.md)

## License

Code is licensed under MIT.
Documentation is licensed under CC BY 4.0.
