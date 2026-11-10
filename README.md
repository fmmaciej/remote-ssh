# Remote-ssh

Remote-ssh makes a new SSH session feel like your own shell.

It sets up a small Bash environment, dotfiles, helper commands, and a pinned set
of standalone CLI tools. It does not use the system package manager. Tools are
downloaded as release binaries, so the setup stays local to your user account.

## Why This Exists

Remote machines are often shared, temporary, or barely configured. Remote-ssh is
for making them usable quickly without changing global settings or getting in
other users' way.

It is worth trying if:

- you use shared accounts and cannot change system-wide configuration,
- you could change global settings, but do not want to affect other users,
- you want your usual tools without depending on apt, yum, brew, or similar,
- you want a shell setup that is already tuned for how you work,
- you often need to make a fresh remote machine comfortable in a few minutes.

## Quick Start

Download `runme.sh`, review or edit the `RUNME_TOOLS` list, then run it:

```bash
curl -fsSLO https://raw.githubusercontent.com/fmmaciej/remote-ssh/main/runme.sh
chmod +x runme.sh
cat runme.sh
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
./runme.sh --profile full --yes
./runme.sh --yes fd rg sk zoxide
./runme.sh fd rg sk zoxide
```

## Local Install

From a checked-out repository:

```bash
./bin/remote-ssh install --profile full --yes
./bin/remote-ssh install --profile quick --yes
./bin/remote-ssh install --profile mini --yes
./bin/remote-ssh install fd rg sk
./bin/remote-ssh install --yes fd rg sk
```

Successful installations are remembered automatically under the effective install
prefix, bound to the physical prefix/bin pair. Installations are additive;
profiles select tools for one invocation. `install` and `uninstall` require
explicit choices. `update` refreshes the project and repairs only the managed
set. See [migration and recovery](docs/install.md#managed-set-and-migration).

Installed tool versions are placed under `~/.local/opt/<tool>-<version>`, with
symlinks in `~/.local/bin`.

## Main Commands

```bash
remote-ssh install [--yes] tool [tool ...]
remote-ssh install --profile <name> [--yes]
remote-ssh setup
remote-ssh uninstall [--yes] tool [tool ...]
remote-ssh list
remote-ssh check [tool ...]
remote-ssh ssh setup
remote-ssh ssh status [host]
remote-ssh git setup
remote-ssh git status [ssh-host]
remote-ssh update
remote-ssh update check
remote-ssh prune [--apply]
remote-ssh scripts --list
remote-ssh guide [section]
remote-ssh help
```

`remote-ssh --help` is intentionally short. Use `remote-ssh guide` for a dynamic
guide generated from the currently loaded shell configuration.

## Runtime Requirements

- `bash` 3.2 or newer
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

- `python3`, `ssh`, and `sk` for `ssh-find` and `ssh-pick`

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
