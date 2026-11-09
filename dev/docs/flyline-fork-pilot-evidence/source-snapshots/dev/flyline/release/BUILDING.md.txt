# Build from the real fork history

Developer machines only; runtime hosts must use a prebuilt package.

```bash
git clone https://github.com/fmmaciej/flyline.git /tmp/flyline-source
git -C /tmp/flyline-source switch --detach d037c075ed30a61080873985ea2621d743ddfc64
python3 /tmp/flyline-source/remote-ssh/build.py \
  --expected-commit d037c075ed30a61080873985ea2621d743ddfc64 \
  --cargo /path/to/rust-1.99.1/bin/cargo \
  --target aarch64-apple-darwin \
  --output /tmp/flyline-artifact
```

Use Python 3.13+, native macOS arm64, the real Rust/Cargo 1.99.1 binaries and
an SDK/linker. Add `--offline` once locked dependencies are cached. Do not
update Cargo.lock. The helper verifies HEAD, clean source, ancestry and the
lockfile, refreshes Git/build-time metadata and packages the library, MIT license
and provenance. The integration project's `candidate.py build-fork` delegates
to this exact pinned helper after checking the fork identity.

The source tree is `eca6115674f2890a3a6e1c1ee6ef5fe57968039b`; upstream base
is `ca910967af35579a2d455a071aa939778d8f6171`, with Vim PR head
`aae68bb4acb43d7462bbe4abffedd6e2b10bd889`. `remote-ssh/build.json` records the
six real patch commits/digests and unchanged lockfile. MIT notices are retained.

Build paths, caches, SDKs and linkers can change native bytes. A rebuilt hash
must pass the explicit native/integration matrix before distribution. The
published source branch is not a published binary Release: the user deferred
Release/tag creation. Do not substitute a moving branch or compile remotely.
