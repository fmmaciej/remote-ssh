# Local fork release candidate

Release publication is **deferred by the user** (2026-11-09). No release or
release tag was created, and the candidate [manifest](flyline.sh) remains
outside `tools/defs` so runtime never receives an unavailable download URL.
The former asset-only release proposal in `fmmaciej/remote-ssh` is superseded.
Historical R4 review files survive in its evidence source snapshots.

Source repository: [fmmaciej/flyline](https://github.com/fmmaciej/flyline).
Published source branch: [remote-ssh-vim](https://github.com/fmmaciej/flyline/tree/remote-ssh-vim).
Pinned source commit: `d037c075ed30a61080873985ea2621d743ddfc64`.
The original `master` is unchanged. Six patch commits are followed by separate
build/documentation; upstream ancestry and the unchanged Cargo.lock are retained.

Candidate identity: `1.10.0-pr974.aae68bb4.r5`.
Proposed future tag: `remote-ssh-v1.10.0-pr974.aae68bb4.r5`, at the source commit
above. This prefix avoids the upstream `v*.*.*` release workflow, whose version
and asset assumptions do not fit this downstream package. The tag is not created.

The local ignored directory `dev/flyline/dist/1.10.0-pr974.aae68bb4.r5/` contains:

- `flyline-1.10.0-pr974.aae68bb4.r5-aarch64-apple-darwin.tar.gz`
- `SHA256SUMS` (the runtime archive digest)
- `provenance.json`, `qualification.json`, `LICENSE-MIT`, `BUILDING.md`
- A loose dylib retained for explicit local native probes.

The [notes](notes.md), [build instructions](BUILDING.md), and
[fork qualification record](../../docs/flyline-fork-integration-record.md)
make this payload reviewable. Source already lives in the real fork history;
GitHub's future release source archive will correspond to its actual tag.
There is no need for an unrelated remote-ssh tag or a reconstructed source bundle.

If the user later resumes publication, verify the immutable payload, publish
these files as a prerelease in **fmmaciej/flyline**, then download and verify the
asset before promoting the manifest and extending production snapshot tests.
Do not add Flyline to default install profiles. No Linux/Intel macOS asset is
proposed; their native qualification remains separate work.
