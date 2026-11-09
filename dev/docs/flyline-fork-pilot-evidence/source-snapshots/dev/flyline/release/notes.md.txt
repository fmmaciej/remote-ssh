# Flyline 1.10.0 + Vim PR #974 — experimental macOS arm64

Custom build `1.10.0-pr974.aae68bb4.r5`; this is not an official Flyline release.

Based on upstream `ca910967af35579a2d455a071aa939778d8f6171` (v1.10.0) and
Vim PR #974 head `aae68bb4acb43d7462bbe4abffedd6e2b10bd889`, with six
recorded patches. The patches reconcile the PR with 1.10.0, fix uppercase vi
dispatch/dot-repeat, add undo transactions/counts/vi history, satisfy current
toolchain lints, restore Bash input safely when unloading the builtin, and
restore the original command/cursor/undo history when cancelling native fuzzy
history search after editing its query.

Qualified locally: macOS arm64, Homebrew Bash 5.3.20. Native vi, history with
Atuin 18.14.1/skim 5.9.0/Starship 1.24.1, Bash default completion with optional
Carapace 1.8.2, direct PTY/tmux 3.8/Zellij 0.44.2, load/unload and measured
performance are covered by the accompanying pilot. This is bounded experimental
Vim support, not a promise of complete Vim compatibility. macOS Bash 3.2 is not
supported for activation. Linux, weak remote hosts, SSH transport and other
architectures remain unverified. No system Bash upgrade is performed.

The runtime archive contains exactly `libflyline.dylib`, `LICENSE-MIT` and
`provenance.json`. SHA-256 of its library:
`ac989a041026f49df1d3b544290ee3e67b497a0d3f82fe4785cd3c106e431d57`.
Archive SHA-256:
`38a7c65eb6e3c8c7458cdebea36607ae2e5577279b96ce2f6e2907b5ff9afaf3`.
See `SHA256SUMS` for all attached payload files and `qualification.json` for
the bounded native results and measurements. These macOS results do not qualify a weak Linux host.

The source is the real upstream history plus six patch commits and the build
helper in [fmmaciej/flyline](https://github.com/fmmaciej/flyline/tree/remote-ssh-vim).
Release source commit: `d037c075ed30a61080873985ea2621d743ddfc64`.
Source tree: `eca6115674f2890a3a6e1c1ee6ef5fe57968039b`.
The unchanged Cargo.lock and patch digests/applied commit IDs are in provenance.
Rust/Cargo 1.99.1 and locked native builds are required; see BUILDING.md.
GitHub's source archive will correspond to the actual downstream source tag.

Publication is deferred by user. This text describes a prepared local payload,
not an existing Release or tag. The R5 measurements are recorded in the fork
qualification record; do not substitute historical R4 figures for this binary.

Flyline remains optional and off by default. Atuin keeps history storage;
Flyline provides editing/Tab UI and registered Bash completers supply candidates.
Carapace is a separate provider integration. Runtime installation never builds
Rust or downloads Actions artifacts. Existing sessions retain loaded code after
updates; recovery is a new shell with `REMOTE_SSH_ENABLE_FLYLINE=0`.
