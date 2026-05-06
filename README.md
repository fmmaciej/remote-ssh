# Remote-ssh

Remote-ssh is a lightweight, shell-first framework for bootstrapping useful SSH
sessions on remote machines. It provides a small Bash-based session environment,
bundled dotfiles, helper commands, and pinned standalone CLI tools downloaded
from GitHub Releases.

The runtime target is a fresh or minimally configured Unix-like host. The normal
installation path intentionally avoids package managers, source builds, Python,
`jq`, and GitHub API discovery.

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
fd rg fzf bat yazi nvim nu starship eza zoxide atuin
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

## Notes

- `runme.sh` is not meant to be run from a local clone.
- No developer tooling from `dev/` is required on remote hosts.
- The working copy used for development may differ from the installed copy.
- Review the remote install script before running it on production machines.
- There is no general `remote-ssh` entrypoint yet.
- To update an installed checkout, use `git pull` in
  `~/.local/share/remote-ssh`, then run `./install.sh`.

## License

Code is licensed under MIT.
Documentation is licensed under CC BY 4.0.
