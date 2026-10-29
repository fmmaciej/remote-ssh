# AGENTS.md

## Project Overview

`remote-ssh` is a lightweight, shell-first framework for bootstrapping useful
SSH sessions on remote hosts. The runtime target is a fresh or minimally
configured Unix-like machine.

Keep runtime dependencies small. Core runtime shell code should assume only
basic tools such as `bash`, `curl`, `tar`, `find`, `sed`, `grep`, `mktemp`,
`date`, and `uname`. `git` is required by `runme.sh`, `remote-ssh update`, and
the optional login-time update check. `unzip` is needed only when a selected
asset is a `.zip`; `sha256sum` or `shasum` is needed only when the selected
asset has a pinned checksum. The optional `sshf` helper currently requires
`python3` because it uses `scripts/ssh_hosts.py`; keep that dependency explicit
until the project decides on a shell fallback or replacement.

Developer tooling in `dev/` may use richer tools, but nothing in `dev/` should
be required on remote hosts.

## Repository Layout

- `runme.sh`: remote installer with editable first-install `RUNME_TOOLS`.
- `bin/remote-ssh`: the main public CLI and thin dispatcher for
  `remote-ssh` subcommands.
- `tools/defs/*.sh`: pinned GitHub release tool definitions.
- `tools/lib/commands/`: implementation of public `remote-ssh` subcommands.
  Larger subcommands may keep private modules below their own subdirectory,
  such as `tools/lib/commands/git/`, `tools/lib/commands/git/status/`,
  `tools/lib/commands/guide/`, or `tools/lib/commands/update/`, while the
  top-level command file remains the public facade.
- `tools/lib/common/`: shared tooling helpers.
- `tools/lib/install/`: environment install defaults, dirs, checks, post-install.
- `tools/lib/install-tool/`: single-tool GitHub asset installer.
- `tools/lib/generate-def/`: developer-only manifest generation helpers.
- `shell/`: remote shell environment loaded by `bash --rcfile`.
- `bin/`: user-facing helper commands exposed in remote-ssh sessions.
- `dots/`: bundled configuration files.
- `docs/`: detailed user and maintainer docs. Keep README short and put
  install details in `docs/install.md`, shell/runtime details in
  `docs/shell.md`, and tool definition workflow in `docs/tools.md`.
- `dev/lib.sh`: small helper library for developer scripts only; keep it
  separate from runtime `lib/*.sh`.
- `dev/smoke.sh`: developer static checks for Bash syntax, `shellcheck`,
  `ruff`, and `mypy`.
- `dev/tests/`: pytest subprocess/integration tests.

## User-Facing Helpers

- `remote-ssh` is the main entrypoint:

  ```bash
  remote-ssh install [tool ...]
  remote-ssh install --full [--yes]
  remote-ssh tool install <tool ...>
  remote-ssh tool list
  remote-ssh check [--strict] [tool ...]
  remote-ssh git setup
  remote-ssh git status [ssh-host]
  remote-ssh update
  remote-ssh update check
  remote-ssh doctor
  remote-ssh prune [--apply]
  remote-ssh guide [section]
  remote-ssh help
  ```

  `remote-ssh --help` and `remote-ssh help` should stay concise CLI usage.
  Longer shell configuration guidance belongs in `remote-ssh guide`. Tool
  reports live under `remote-ssh check`; do not reintroduce a separate check
  entrypoint.
- Installation publishes only the management CLI from checkout helpers into
  `INSTALL_BIN_DIR` as a direct absolute symlink to this checkout's
  `bin/remote-ssh`. Ordinary terminals can use it when that directory is in PATH.
  The environment and other checkout helpers require explicit
  `bash --rcfile <checkout>/shell/rc.sh -i` activation. Installation never edits
  user startup files or changes the default shell.
- Do not reintroduce a root `install.sh` wrapper. Local installs should use
  `./bin/remote-ssh install ...`; `runme.sh` delegates to that command after
  cloning or updating the repo.
- `remote-ssh git setup` and `remote-ssh git status [ssh-host]` support the
  opt-in Git SSH identity flow. Do not reintroduce separate Git helper
  entrypoints.
- `remote-ssh update` is the only update command that should mutate the
  checkout. `remote-ssh update check` and the login-time update check are
  informational only: they may use `git ls-remote`, but they must not fetch,
  pull, install, or modify the working tree.
- `remote-ssh guide starship` explains the bundled Starship prompt symbols.
- `navi` provides private cheatsheets from `dots/navi/cheats`; remote-ssh
  shells prepend that directory to `NAVI_PATH` and expose `cheats='navi'`.
- `log` and `logrun` are shell functions from `shell/rc.d/25-log.sh` for
  capturing command output to a file while still streaming it through `tspin`
  when available.
- `sshf` lists SSH config hosts with `scripts/ssh_hosts.py`, lets the user pick
  one with `fzf`, then runs `ssh`. This is optional functionality and currently
  requires `python3`.

Tool installs are platform-aware. `DEFAULT_TOOLS` is the full candidate list
used by `remote-ssh install --full`; unsupported entries are skipped with a
clear report. `runme.sh` keeps an editable `RUNME_TOOLS` bootstrap list for the
first install. Without arguments it calls `bin/remote-ssh install` with that
list; with arguments it forwards them to `remote-ssh install` verbatim. Keep
install option semantics in `remote-ssh install`, not in `runme.sh`.
`REMOTE_SSH_REF` is the only runme-level selector; it may pin the cloned or
updated checkout to a branch, tag, or fetchable Git ref before install.
Installs that choose or reset the expected tool set prompt for confirmation
unless `--yes` is passed; saved expected-tool reinstalls do not prompt.

The user's maintained tool set is stored as one tool per line in
`${XDG_CONFIG_HOME:-$HOME/.config}/remote-ssh/expected-tools`. Blank lines and
`#` comments are ignored. `remote-ssh install`, `remote-ssh update`,
`remote-ssh check`, and `remote-ssh doctor` use that expected set when no tools
are provided explicitly. Do not treat this file as cache or generated repo
state; it is user configuration.

## Tool Asset Contract

Tool definitions use exact GitHub release asset manifests. Do not reintroduce
runtime template generation for asset names.

Each `tools/defs/<tool>.sh` should define:

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

`BINARY_ALIASES=(...)` is optional. For example, `nu` also installs `nushell`.
`CHECKSUMS=(...)` is optional but preferred whenever a trustworthy SHA-256 is
available. Runtime verifies a checksum before extracting or installing the
asset.

Runtime installation must select an asset from `ASSETS`; it must not use GitHub
API discovery, `jq`, Python, source builds, package manager packages, or dynamic
asset-name templates.

Supported runtime assets:

- `.tar.gz`
- `.tgz`
- `.zip`
- raw executable assets

Do not add support for source archives, `.deb`, `.rpm`, `.apk`, or package
manager installs unless the project direction explicitly changes.

## Platform Selection Rules

Use the existing platform detection in `tools/lib/common/platform.sh`.

For Linux glibc hosts, prefer a matching `musl` asset when available, then
`glibc`/`gnu`, then `any`. For Linux musl hosts, prefer `musl`, then `any`.
For macOS, use `darwin:<arch>:any`.

If no asset matches, errors should include the detected platform and the
available `ASSETS` entries.

## Version Policy

Exact manifests are pinned. Runtime installs only the definition's `VERSION`.

- `tools/install-tool.sh <tool>` installs the pinned version.
- `tools/install-tool.sh <tool> latest` should fail clearly.
- `tools/install-tool.sh <tool> <other-version>` should fail clearly.

Updating versions is a developer workflow: regenerate or edit the definition,
run tests, optionally run the live asset checker, then commit.

## Adding Or Updating Tools

Preferred workflow:

1. Run `tools/generate-def.sh owner/repo [--tool name] [--tag tag]`.
2. Add or update `tools/defs/<tool>.sh`.
3. Add the tool to `DEFAULT_TOOLS` only if it should be a default candidate.
4. Update `dev/tests/test_tool_assets.py`.
5. Add or update `dots/navi/cheats/<tool>.cheat` when useful.
6. Update `runme.sh` `RUNME_TOOLS` and the default tool list in
   `docs/install.md` if `DEFAULT_TOOLS` changed.
7. Run `just smoke`.
8. Run `just test-assets-live` only when explicitly requested.

`DEFAULT_TOOLS` is not a promise that every listed tool installs on every
platform. It is filtered by exact manifest support for the current platform.
Keep `RUNME_TOOLS` in sync with it. Do not add parallel OS-specific default
arrays unless this policy changes.

## Tool Generator Workflow

The preferred generator workflow is:

```bash
tools/generate-def.sh owner/repo
tools/generate-def.sh owner/repo --tool name --tag v1.2.3
tools/generate-def.sh owner/repo --list
```

Without `--tool`, the generator infers the tool name from the repository
basename. Use `--tool` when the repo name and installed binary differ, such as
`BurntSushi/ripgrep --tool rg`. The generator should emit `CHECKSUMS` whenever
GitHub release metadata exposes SHA-256 `digest` values.

## Install Policy

The normal install path should install the pinned remote-ssh version even if a
system tool with the same name exists elsewhere in `PATH`. A tool may be skipped
only when `$INSTALL_BIN_DIR/<tool>` is a managed symlink pointing at the pinned
version under `$INSTALL_PREFIX`.

Tool installs stage the new release directory before switching symlinks. Keep
that property intact: a failed reinstall should not remove the previously
working binary. Old inactive release directories can be reported with
`remote-ssh prune`; deletion requires `remote-ssh prune --apply`.

`remote-ssh prune` must remain conservative:

- dry-run by default,
- only considers direct child directories of `$INSTALL_PREFIX`,
- only considers names matching known tool definitions,
- protects directories currently referenced by tool symlinks and aliases,
- never removes files, symlinks, or unknown directories.

## Tests And Checks

Use:

```bash
just smoke
```

`just smoke` is the default verification for normal changes.

Do not run:

```bash
just test-assets-live
```

unless explicitly asked. It uses the network and GitHub API.

When changing tool definitions or asset selection, update
`dev/tests/test_tool_assets.py`, plus the live checker in
`dev/check_assets_live.py` if needed.

When changing `runme.sh`, update `dev/tests/test_runme.py`.

When changing developer tooling, keep it isolated in `dev/`. `dev/lib.sh`
contains helper functions for developer scripts; do not source runtime
`lib/*.sh` just to support developer checks.

When changing public entrypoints or helper commands in `bin/`, update pytest
subprocess tests under `dev/tests/`. Static checks include executable helper
scripts in `bin/`, not only `*.sh` files.

Prefer pytest tests under `dev/tests/` for new behavior that can exercise
public commands as subprocesses, especially `runme.sh` and `remote-ssh`
subcommands. Tests may still launch Bash subprocesses when they need to source
shell rc files, aliases, init hooks, Bash functions, or tool definitions.

Public `remote-ssh` subcommand behavior belongs in `tools/lib/commands/`, with
one facade file per subcommand. Larger subcommands may use private submodules
below their command directory. Keep `bin/remote-ssh` as routing, usage, and
bootstrap only.

Login shell hooks in `shell/rc.d/` must stay cheap and easy to disable. Any
network-capable hook, such as the update check, should be throttled, cache its
result under `${XDG_STATE_HOME:-$HOME/.local/state}/remote-ssh`, and support an
environment toggle before `rc.sh` is loaded.

## Editing Guidance

- Prefer small, focused shell changes.
- Preserve runtime portability and avoid adding dependencies to the remote path.
- Keep README as a short project start page. Put detailed usage and maintainer
  information in `docs/install.md`, `docs/shell.md`, `docs/tools.md`, or
  `dev/README.md`.
- Keep developer-only GitHub API usage isolated in `tools/generate-def.sh` and
  `tools/lib/generate-def/`.
- Do not revert unrelated working-tree changes.
- Use `rg` for searching and `just smoke` for verification.
