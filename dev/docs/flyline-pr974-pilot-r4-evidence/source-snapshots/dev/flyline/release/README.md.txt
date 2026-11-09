# Reviewable release candidate

Nothing in this directory publishes a release or enables production installation.
The [manifest](flyline.sh) is deliberately outside `tools/defs` until the exact
asset exists. The [release text](notes.md), source bundle, checksum file,
provenance and build instructions are prepared for review.

Proposed public repository: `fmmaciej/remote-ssh`.
Proposed prerelease tag: `flyline-1.10.0-pr974.aae68bb4.r4`.
Asset-only tag anchor: existing remote-ssh main commit
`25ba525e6e9bfc8a90a8a68fc6b28c6f6ea435fc`, verified 2026-11-09.
This does not commit or publish unrelated working-tree changes. The attached
source bundle, not GitHub's automatic remote-ssh source archives, contains
the patched Flyline source. The release notes make this distinction explicit.

Local artifacts are in the ignored directory
`dev/flyline/dist/1.10.0-pr974.aae68bb4.r4/`:

- `flyline-1.10.0-pr974.aae68bb4.r4-aarch64-apple-darwin.tar.gz`
- `flyline-1.10.0-pr974.aae68bb4.r4-source.bundle`
- `SHA256SUMS`, `provenance.json`, `qualification.json`, `LICENSE-MIT`, `BUILDING.md`

The loose dylib is retained locally for explicit native probes; the archive is
the sole runtime asset. Developer artifact preparation and testing do not
authorize public release creation. Obtain approval for this concrete payload
after the qualification/checks finish, then publish it as a prerelease. Verify
the actual downloaded archive against the recorded digest before promoting
`flyline.sh` into `tools/defs`. Extend the production manifest snapshot tests
at promotion and update user docs from pending to available. Do not add it to
any default tool/profile list. Run focused checks and static smoke again.

No Linux or Intel macOS asset is proposed. Do not claim support from upstream
CI or a successful cross-compilation. A native weak Linux pilot is deferred
at the user's request and remains separate work.
