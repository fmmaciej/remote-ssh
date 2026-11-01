# Tool Definitions

Tools are installed from exact GitHub Release asset manifests. Runtime install
does not generate asset names dynamically and does not use GitHub API discovery.

## Listing Tools

```bash
remote-ssh tool list
remote-ssh tool list --installed
remote-ssh tool list --all
```

The list is an alphabetical `TOOL` / `STATUS` table built from all definitions
in `tools/defs/`, including tools outside the default installation profiles.
Without options, it shows tools supported on the current platform and all
managed installations. `--installed` limits it to managed installations;
`--all` includes unsupported tools. These options cannot be combined.
All arguments are validated before showing `--help`; help does not suppress
conflicting filters, unknown options, or unexpected tool arguments.

- `installed`: an executable tool symlink points to a release with a valid
  remote-ssh ownership record. Relative symlinks and older managed releases count.
- `available`: the pinned manifest has a matching asset for this platform, but
  no managed installation was detected.
- `unsupported`: no matching asset exists and no managed installation was
  detected; shown only with `--all`.

Installed tools remain visible even if the current manifest no longer supports
the platform. System binaries, unmanaged files, broken links, and legacy
releases without a valid ownership record do not count as managed installations.
Binary aliases do not create additional rows. An empty result prints
`No tools found.` and exits successfully.

For single-binary legacy installations, `remote-ssh check` may still report `ok`
and the installer may skip the pinned version even though the list shows
`available`. These commands accept the legacy versioned symlink without requiring
an ownership record. Absolute and relative targets are matched equivalently.
Directory symlinks and `..` are resolved physically. For pinned-version checks,
marked installations need a valid ownership record whose version exactly matches
the pinned version; for example, `15.1.0.1` does not match `15.1.0`.
Legacy matching accepts only
`<tool>-<version>` or `<tool>-<version>.<PID>-<RANDOM>`, with decimal digits in
both suffix fields. An existing invalid record, including a broken record
symlink, blocks legacy matching; `check --strict` fails and installation is not
skipped. A target outside the installation prefix is never a pinned installation.
To migrate a legacy installation to a marked release, use, for example,
`FORCE=1 remote-ssh tool install rg`; see [installed paths](install.md#installed-paths).

The list does not depend on or modify `expected-tools`. Use
`remote-ssh guide tools` for installation profiles and `remote-ssh check` for
pinned-version, installation-health, alias, and PATH diagnostics. Listing tools
does not run their binaries or access the network.

## Definition Contract

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

`BINARY_ALIASES=(...)` is optional. For example, `nu` also installs `nushell`.

### Bundled runtimes

Single-binary installation is the default. Tools such as Neovim also need their
packaged runtime and libraries. Declare an explicit bundle layout and one root
for each exact asset:

```bash
INSTALL_LAYOUT="bundle"
BINARY_PATH="bin/nvim"
BUNDLE_ROOTS=(
  "nvim-linux-x86_64.tar.gz|nvim-linux-x86_64"
  "nvim-macos-arm64.tar.gz|nvim-macos-arm64"
)
```

`BINARY_PATH` is relative to the declared package root. The installer preserves
that root's contents in the release directory and points the tool symlink at
the nested executable. Bundle mode currently accepts `.tar.gz` and `.tgz`
archives containing ordinary files and directories only. Before extraction it
rejects paths outside the declared root, absolute paths, traversal, links, and
special files. Keep the asset and root mappings explicit when updating a bundle
definition; the generator's default single-binary output needs this manual step.

Old single-file Neovim installations are considered incomplete and repaired by
a normal pinned reinstall. `remote-ssh check` can report `incomplete-local`.

## Asset Policy

Supported release asset formats:

- `.tar.gz`
- `.tgz`
- `.tar.xz`
- `.zip`
- raw executable assets

`.tar.xz` extraction requires tar with xz support. GNU tar also needs `xz` in
PATH; macOS tar has built-in support. Extraction failures leave active tool
symlinks unchanged. Single-binary installs support this format; bundle installs
still require `.tar.gz` or `.tgz`.

Unsupported by design:

- source archives that need building
- `.deb`
- `.rpm`
- `.apk`
- package manager installs

Exact manifests are pinned. `tools/install-tool.sh <tool>` installs the pinned
`VERSION`; `latest` and arbitrary version arguments are rejected for manifest
based definitions.

For manual debugging through the public CLI, `remote-ssh tool install <tool>`
installs selected pinned tools without changing the user's saved
`expected-tools` set. Regular users should prefer `remote-ssh install`.

When a selected asset has a matching `CHECKSUMS` entry, the installer verifies
its SHA-256 before extraction or installation. Some upstream projects do not
publish checksum files for every asset yet; those remaining entries are tracked
as follow-up hardening work.

Download, hash calculation, checksum verification, and extraction failures stop
installation with a nonzero exit status before switching any active symlinks.

## Adding Or Updating Tools

Generate a draft tool definition from GitHub Releases:

```bash
tools/generate-def.sh chmln/sd
tools/generate-def.sh BurntSushi/ripgrep --tool rg --tag 15.1.0
tools/generate-def.sh nushell/nushell --tool nu --version 0.112.2
tools/generate-def.sh skim-rs/skim --tool sk --tag v5.9.0
tools/generate-def.sh chmln/sd --list
```

Without `--tool`, the tool name is inferred from the repository basename.
Use `--tool` when the repository name differs from the installed binary name.
`--tag` and `--version` both select an exact GitHub release tag; without either
option the generator uses the latest release.

Preferred workflow:

1. Run `tools/generate-def.sh owner/repo [--tool name] [--tag tag]`.
2. Add or update `tools/defs/<tool>.sh`.
3. Add the tool to `DEFAULT_TOOLS` only if it should be a default candidate.
4. Update asset contract tests in `dev/tests/test_tool_assets.py`.
5. Add or update `dots/navi/cheats/<tool>.cheat` when useful.
6. Update `runme.sh` `RUNME_TOOLS` and the default tool list in
   `docs/install.md` if defaults changed.
7. Run `just smoke`.
8. Run `just test-assets-live` only when explicitly requested.

`DEFAULT_TOOLS` is not a promise that every listed tool installs on every
platform. It is filtered by exact manifest support for the current platform.

## Development Checks

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
If GitHub API rate limits are a problem, create `dev/.env` and set
`GITHUB_TOKEN` or `GH_TOKEN`.
