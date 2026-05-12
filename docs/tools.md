# Tool Definitions

Tools are installed from exact GitHub Release asset manifests. Runtime install
does not generate asset names dynamically and does not use GitHub API discovery.

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

## Asset Policy

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

## Adding Or Updating Tools

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
