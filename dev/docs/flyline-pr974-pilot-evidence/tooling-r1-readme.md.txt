# Flyline candidate tooling

Developer-only implementation of Stage 0 in the
[integration plan](../docs/flyline-implementation-plan.md). The current candidate
**fails native vi acceptance**; see the [pilot record](../docs/flyline-pr974-pilot-record.md).
It is not an installable remote-ssh tool and must not be published as supported.

Inputs are Flyline 1.10.0 at `ca910967af35579a2d455a071aa939778d8f6171`
and PR #974 at `aae68bb4acb43d7462bbe4abffedd6e2b10bd889`.
The [input record](inputs.json) pins the patch bytes:

1. `0001-upstream-pr974.patch` ports the PR onto 1.10.0, retaining the new
   editing helpers introduced on the stable branch. Its two fewer added blank
   lines account for the difference from the original PR's addition count.
2. `0002-vi-key-dispatch-and-repeat.patch` normalizes uppercase vi bindings
   for the newer dispatcher, prevents literal insertion from unbound Normal
   keys, keeps the Normal cursor on a character, and implements recorded-key
   `.` replay with unit regressions. This remains a prototype, including its
   undo grouping and less common Vim sequences.

The patch license is [MIT](LICENSE-MIT), as offered by upstream. Preserve that
license when distributing modified source or libraries.

## Reproduce a developer candidate

Use Python 3.13+, Git, a native C linker, and the pinned Rust **1.99.1** toolchain.
Pass the real Cargo binary in that toolchain's `bin/`, not a rustup shim. Rust
and Cargo are developer dependencies; remote hosts must never run these steps.
The scripts do not download sources or install anything. First obtain the
exact archive:

```bash
curl --fail --location \
  https://codeload.github.com/HalFrgrd/flyline/tar.gz/ca910967af35579a2d455a071aa939778d8f6171 \
  --output /private/tmp/flyline-1.10.0-source.tar.gz
python3 dev/flyline/candidate.py prepare \
  --archive /private/tmp/flyline-1.10.0-source.tar.gz \
  --output /private/tmp/flyline-candidate-source
python3 dev/flyline/candidate.py build \
  --source /private/tmp/flyline-candidate-source \
  --cargo /path/to/rust-1.99.1/bin/cargo \
  --target aarch64-apple-darwin \
  --output /private/tmp/flyline-candidate-artifact
```

Choose unused output directories. The source archive and patches are verified
before preparation. Preparation records a deterministic local Git commit/tree;
its reconstructed parent is explicitly distinguished from the original upstream
commit. The base `Cargo.lock` must remain unchanged. `build` requires that clean
tracked tree, records the toolchain and target, and rejects common ambient compiler
overrides. Add `--offline` once the locked dependencies are cached. No moving
dependency update is performed.

The other initial native target is `x86_64-unknown-linux-gnu`. The builder
rejects cross-compilation for this pilot. Neither target becomes supported
merely by producing a library. No Linux native result is available yet.

Output contains the library, license, provenance, a deterministically packaged
`.tar.gz`, and `SHA256SUMS`. Archive members are exactly `libflyline.dylib`
(or `libflyline.so`), `LICENSE-MIT`, and `provenance.json`. This pins the source
and records an artifact; it does not promise bit-identical binaries across
different OS SDKs/linkers. Do not use these files as runtime assets until the
plan's acceptance and management requirements pass.

## Native probes

Run only in disposable PTYs; a loaded library executes inside the child Bash.
The harness uses a fresh HOME, allowlisted environment, fixed terminal, local
fixture commands, and the existing terminal-probe emulator. It snapshots the
library bytes so another developer build cannot overwrite a mapped test file.
It does not source user shell configuration or download binaries.

```bash
python3 dev/flyline/pilot.py --bash /opt/homebrew/bin/bash \
  --library /private/tmp/flyline-candidate-artifact/libflyline.dylib \
  --output /private/tmp/flyline-native-results
python3 dev/flyline/pilot.py --bash /opt/homebrew/bin/bash --readline \
  --output /private/tmp/flyline-readline-results
```

On Linux pass the selected native Bash and `.so`. A failing probe returns 1;
JSON results and escaped transcripts are retained. `--case NAME` selects a
regression, and can be repeated. Tests compare executed arguments and also
reject command execution before the final explicit Enter. A timeout is a
failed probe, not evidence of a native crash.

Readline's clean Ctrl-R history binding is not assumed to implement Vim redo.
The `undo-redo` control therefore expects the undo to remain applied with
Readline, while Flyline's PR-specific redo is tested separately. All other
editing/history expectations are shared. `undo` is a separate regression so
an undo/redo pair cannot mask an incorrect undo boundary.

For upstream unit tests, use `cargo test --workspace --lib --locked` in the
prepared source with the same toolchain. Do not run the unrestricted upstream
test suite: its integration tests start Docker containers. Run `just smoke`
for repository verification; native probes require explicit local artifacts
and are not downloaded or executed by default tests.
