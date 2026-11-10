# Published Flyline R5 release

The user published the [experimental prerelease](https://github.com/fmmaciej/flyline/releases/tag/remote-ssh-v1.10.0-pr974.aae68bb4.r5).
The generated [production definition](../../../tools/defs/flyline.sh) is the
authoritative installer manifest. The [prepared candidate](flyline.sh) is retained
as a historical comparison input; its values match the generated definition.

Source repository: [fmmaciej/flyline](https://github.com/fmmaciej/flyline).
Tag: `remote-ssh-v1.10.0-pr974.aae68bb4.r5`.
Source commit: `d037c075ed30a61080873985ea2621d743ddfc64`.
Artifact version: `1.10.0-pr974.aae68bb4.r5`.

The six published attachments are:

- `flyline-1.10.0-pr974.aae68bb4.r5-aarch64-apple-darwin.tar.gz`
- `SHA256SUMS` (covers the other five attached payload files)
- `provenance.json`
- `qualification.json`
- `LICENSE-MIT`
- `BUILDING.md`

The archive contains exactly `libflyline.dylib`, `LICENSE-MIT` and
`provenance.json`. Its SHA-256 is
`38a7c65eb6e3c8c7458cdebea36607ae2e5577279b96ce2f6e2907b5ff9afaf3`;
the library SHA-256 is
`ac989a041026f49df1d3b544290ee3e67b497a0d3f82fe4785cd3c106e431d57`.
The loose local dylib is not a release attachment.

See the [promotion plan and results](../../docs/flyline-release-promotion-plan.md)
for generation, comparison and isolated public-release lifecycle verification,
and the [fork qualification record](../../docs/flyline-fork-integration-record.md)
for the existing native measurements. Publication did not rebuild the binary.
The public BUILDING.md removes an obsolete publication-deferred sentence; the
public SHA256SUMS covers all attached payload files. Provenance and qualification
remain byte-identical to the reviewed R5 inputs.

Flyline remains opt-in and outside all install profiles. Native qualification
is limited to local macOS arm64 with Homebrew Bash 5.3.20. Linux, Intel macOS,
weak hosts and SSH transport require separate qualification.
