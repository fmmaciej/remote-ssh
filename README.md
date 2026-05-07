# Remote-ssh

Remote-ssh is a lightweight, shell-first framework for bootstrapping useful SSH
sessions on remote machines. It provides a small Bash-based session environment,
bundled dotfiles, helper commands, and pinned standalone CLI tools downloaded
from GitHub Releases.

The runtime target is a fresh or minimally configured Unix-like host. The normal
installation path intentionally avoids package managers, source builds, `jq`,
and GitHub API discovery. Python is not needed for the core installer, but the
optional `sshf` helper currently uses a Python parser for SSH config files.

## Quick Start

`runme.sh` is the remote install script. It is intended to be executed directly,
for example through `curl | bash`, and not from a local repository checkout.

```bash
curl -fsSL https://raw.githubusercontent.com/fmmaciej/remote-ssh/main/runme.sh | bash
```

The script clones or updates this repository in:

```text
~/.local/share/remote-ssh
```

Then it runs `install.sh`.

## Local Install

From a checked-out repository:

```bash
./install.sh
```

With no arguments, this installs the default tool set:

```text
fd rg sd dust fzf bat yazi nvim zellij nu starship eza zoxide atuin navi tspin vector
```

To install only selected tools:

```bash
./install.sh fd rg fzf
```

Installed tool versions are placed under:

```text
~/.local/opt/<tool>-<version>
```

Symlinks are created in:

```text
~/.local/bin
```

## Interactive Shell

After installation, start a shell with the remote-ssh environment:

```bash
bash --rcfile "$HOME/.local/share/remote-ssh/shell/rc.sh" -i
```

The post-install output also prints an example SSH config using:

```text
RemoteCommand bash --rcfile '<install-dir>/shell/rc.sh' -i
```

## Shell Helpers

The remote-ssh shell loads a few small helpers:

- `remote-ssh`: main entrypoint for install, check, update, doctor, and prune.
- `remote-ssh-help`: show available commands, aliases, paths, and Git SSH notes.
- `starship-help`: explain the bundled Starship prompt symbols.
- `remote-ssh-check`: report pinned tools, local install symlinks, and PATH.
- `remote-ssh-git-setup`: opt in to the bundled Git and SSH include files.
- `remote-ssh-git-identity`: inspect Git identity and SSH auth state.
- `sshf`: pick a host from your SSH config with `fzf`, then run `ssh`.
- `cheats`: open private `navi` cheatsheets from `dots/navi/cheats`.

Main entrypoint commands:

```bash
remote-ssh install [tool ...]
remote-ssh tool install rg
remote-ssh check [--strict] [tool ...]
remote-ssh update
remote-ssh doctor
remote-ssh prune [--apply]
remote-ssh help [section]
```

`remote-ssh prune` is dry-run by default. It prints old installed tool release
directories and removes them only when called with `--apply`.

Private cheatsheets are stored in:

```text
dots/navi/cheats
```

Remote-ssh shells prepend that directory to `NAVI_PATH`, so `navi` and the
`cheats` alias can search project-local snippets without copying them into a
global user directory.

`sshf` reads host aliases from `$HOME/.ssh/config`, including `Include` files,
and ignores wildcard entries such as `Host *`. It currently uses
`scripts/ssh_hosts.py`, so this helper requires `python3`. The dependency is
intentional for now because the parser is more reliable than a shell-only
version; a future version may replace it or add a fallback.

## Repository Structure

| Path | Role |
| --- | --- |
| `runme.sh` | Remote installer for `curl | bash` |
| `install.sh` | Local installer and default tool selection |
| `tools/defs/` | Pinned tool definitions with exact GitHub release assets |
| `tools/lib/install-tool/` | Runtime tool installer |
| `tools/lib/generate-def/` | Developer-only manifest generation helpers |
| `shell/` | Bash/Zsh-oriented shell environment |
| `bin/` | Helper commands exposed in remote-ssh sessions |
| `dots/` | Bundled configuration files |
| `dev/` | Optional developer tooling and tests |

## Tool Definitions

Tools are installed from exact GitHub Release asset manifests. Runtime install
does not generate asset names dynamically and does not use GitHub API discovery.

Each `tools/defs/<tool>.sh` defines a pinned release:

```bash
TOOL_NAME="example"
GH_REPO="owner/repo"
RELEASE_TAG="v1.2.3"
VERSION="1.2.3"
BINARY_NAME="example"

ASSETS=(
  "linux:x86_64:musl|example-v1.2.3-x86_64-unknown-linux-musl.tar.gz"
  "darwin:aarch64:any|example-v1.2.3-aarch64-apple-darwin.tar.gz"
)

CHECKSUMS=(
  "example-v1.2.3-x86_64-unknown-linux-musl.tar.gz|<sha256>"
  "example-v1.2.3-aarch64-apple-darwin.tar.gz|<sha256>"
)
```

Supported release asset formats:

- `.tar.gz`
- `.tgz`
- `.zip`
- raw executable assets

Unsupported by design:

- source archives that need building
- `.deb`
- `.rpm`
- `.apk`
- package manager installs

Exact manifests are pinned. `tools/install-tool.sh <tool>` installs the pinned
`VERSION`; `latest` and arbitrary version arguments are rejected for manifest
based definitions.

When a selected asset has a matching `CHECKSUMS` entry, the installer verifies
its SHA-256 before extraction or installation. Some upstream projects do not
publish checksum files for every asset yet; those remaining entries are tracked
as follow-up hardening work.

## Runtime Requirements

Runtime requirements are intentionally small:

- `bash`
- `git` for `runme.sh`
- `curl`
- `tar`
- `find`
- `sed`
- `grep`
- `unzip` only when the selected asset is a `.zip`
- `sha256sum` or `shasum` when the selected asset has a pinned checksum

Optional helper requirements:

- `python3` for `sshf`

Developer tooling may require more, but it is isolated in `dev/`.

## Development

Useful commands:

```bash
just smoke
just lint
just fmt
just test-assets-live
```

`just smoke` is the default verification for normal changes.

`just test-assets-live` uses the network and GitHub Releases API to verify that
pinned assets exist. Run it only when you explicitly want live asset validation.
If GitHub API rate limits are a problem, create `dev/.env` and set `GITHUB_TOKEN`
or `GH_TOKEN`.

Generate a draft tool definition from GitHub Releases:

```bash
tools/generate-def.sh chmln/sd
tools/generate-def.sh BurntSushi/ripgrep --tool rg --tag 15.1.0
tools/generate-def.sh nushell/nushell --tool nu --version 0.112.2
tools/generate-def.sh chmln/sd --list
```

Without `--tool`, the tool name is inferred from the repository basename.
Use `--tool` when the repository name differs from the installed binary name.
`--tag` and `--version` both select an exact GitHub release tag; without either
option the generator uses the latest release.

## Notes

- `runme.sh` is not meant to be run from a local clone.
- No developer tooling from `dev/` is required on remote hosts.
- The working copy used for development may differ from the installed copy.
- Review the remote install script before running it on production machines.
- To update an installed checkout, run `remote-ssh update`.

## License

Code is licensed under MIT.
Documentation is licensed under CC BY 4.0.
