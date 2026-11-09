# Flyline 1.10.0 + PR #974 native pilot

Date: 2026-11-08. Result: **native vi acceptance failed; runtime integration withheld**.

The [integration plan](flyline-implementation-plan.md#stage-0-build-and-validate-the-pr-candidate)
requires correct native vi editing before installer/session changes. This run
implements the source port, developer build and bounded vi fixes, then exercises
the candidate on macOS arm64. It does not complete the integration plan.

## Delivered implementation

- [Candidate preparation/build tooling](../flyline/README.md), with exact source
  and patch checksums, an unchanged base lockfile, a recorded local source
  commit/tree, pinned Rust, locked builds, and local archives with provenance.
- A recorded [patch series](../flyline/inputs.json) containing the reconciled
  PR and corrections for uppercase vi dispatch, Normal-mode literal insertion,
  cursor positioning, and real dot-repeat. The PR's original dot action was a
  stub. The dispatcher corrections are necessary when porting its older key
  definitions onto the newer stable dispatcher.
- [Offline native PTY probes](../flyline/pilot.py) and a clean Readline control,
  plus subprocess-backed tests of source preparation, checksums, lockfile
  preservation, and output protection. Developer scripts are included in
  standard static checks.

No Flyline tool definition, library installation layout, session activation,
history adapter, default tool change, or external release was shipped. The
source remains a developer candidate, not a supported Flyline fork.

## Source and build identity

| Input | Identity |
| --- | --- |
| Stable base | `v1.10.0`, `ca910967af35579a2d455a071aa939778d8f6171` |
| PR #974 head | `aae68bb4acb43d7462bbe4abffedd6e2b10bd889` |
| Candidate | `1.10.0-pr974.aae68bb4.r1` |
| Local port commit | `3b8d358e2c389c3ee420a492a6313757cd7d9639` |
| Source tree | `5db364b34259a19ed3c88a25242f6bb4f6eac8f4` |
| Base archive SHA-256 | `7994f94058328ef31edc89d888b8fbc156fe6c5e693cb40feafd8786fab13ef0` |
| Unchanged Cargo.lock SHA-256 | `3162250ee645024bf56933a723a300f1850464d31acbbc0ba156eb80301085e9` |
| Rust | `rustc 1.99.1 (58cf8f9c3 2026-10-13)` |
| Cargo | `1.99.1 (5f94df478 2026-08-27)` |
| Target | `aarch64-apple-darwin`, native release build |

Preparation was repeated into another unused directory and produced identical
port commit/tree/provenance. These are local commits reconstructing the source
archive and patch series; they are not published upstream commits. The package
version remains 1.10.0 internally; the shipped provenance distinguishes it from
official Flyline. Actual binary identity is in the
[build provenance](flyline-pr974-pilot-evidence/provenance.json).

The archive contains exactly the library, `LICENSE-MIT`, and `provenance.json`.
Its checksum is recorded in [SHA256SUMS](flyline-pr974-pilot-evidence/SHA256SUMS).
The local archive and library are under
`/private/tmp/remote-ssh-flyline-build/artifact-r1-packaged/`; they were not
published and are not permanent installation URLs.

The isolated toolchain emitted a warning about `rust-objcopy` being unable to
find `libLLVM.dylib` while stripping debug information. Build and native loading
succeeded. This developer build warning is retained in the log; it must be
resolved/qualified for a distributable release. macOS dependencies were
inspected with `otool -L`; the result is in the evidence directory.

## Native result

| Platform / Bash | Load | vi probes | Support decision |
| --- | --- | --- | --- |
| macOS arm64, Homebrew Bash 5.3.20 | Pass | 13/17 pass | Candidate fails acceptance |
| Same host/Bash, clean Readline | N/A | 17/17 controls pass | Existing editing baseline |
| Linux glibc x86_64 | Unverified | Unverified | Not supported by this candidate |
| macOS Intel, Linux aarch64/musl | Unverified | Unverified | Deferred |
| macOS system Bash 3.2 | Not attempted | Not attempted | Outside planned activation support |

Passing candidate probes cover the original `ac` → `bc` replacement, deletion,
word deletion/change, yank/paste, return to insert mode, dot-repeat of deletion,
replacement and change-plus-insertion, Unicode input/yank/paste, unbound Normal
keys not becoming text, ordinary Up history recall, and the PR's undo/redo pair.
There was no observed command execution before the explicit final Enter in
these probes.

Four required probes still fail:

| Probe | Expected | Observed |
| --- | --- | --- |
| Undo a quick `r` replacement | Restore `ac` | No captured command; prompt becomes empty. Snapshot merging crosses the intended vi change boundary. |
| `2h`, then replace | `aXcd` | `abXd`: horizontal motion ignores the count. |
| Normal-mode `k` | Recall `capture seeded` | No captured command. PR binds `k` to line movement rather than history at the first line. Ordinary Up works. |
| Normal-mode `/seeded`, accept and edit | Recall the seeded command without executing it | No captured command. The PR lacks a Normal-mode `/` history-search binding. |

The [native results](flyline-pr974-pilot-evidence/native/results.json) include
actual executed arguments, pre-submit line state, early-execution checks,
resource observations, and escaped transcripts. Missing argument frames count
as failures; they do not by themselves establish a crash or performance limit.
The [Readline control](flyline-pr974-pilot-evidence/readline/results.json) passes
the same four cases.

One expectation in the older plan/documentation needs correction before a
future integration: clean Bash 5.3.20 binds vi-command Ctrl-R to history search,
not Vim redo. The [binding dump](flyline-pr974-pilot-evidence/readline-bindings.txt)
and control show this distinction. The PR adds Vim redo; the harness tests that
as its own behavior. The undo-only failure remains independent of that
difference. Existing session bindings have not been changed.

## Validation and remaining gates

Upstream unit tests with the patched source and locked dependencies pass:
**1083 passed, 1 ignored** across the workspace library targets. The new local
source-preparation tests pass. Native tests are separate from those results;
green unit tests do not qualify the candidate.

`just smoke` passes: **1411 passed, 30 skipped** (452.92 seconds), including
the five new source-preparation tests. Static checks and `git diff --check`
also pass. The [smoke log](flyline-pr974-pilot-evidence/smoke.log) records the
completed run. An earlier sandboxed attempt was interrupted after existing
PTY tests could not execute `ps`; the full rerun outside that restriction passed.
Source/evidence [fingerprints](flyline-pr974-pilot-evidence/fingerprints.json)
and [validation summary](flyline-pr974-pilot-evidence/validation.json) are retained.
No live asset check was run.

Atuin/skim/Starship adapters, combined Carapace `complete -D`, full terminal
lifecycle tests, SSH/tmux/Zellij, Linux native execution, and the repeated
performance comparison remain unverified. Performance acceptance was not
inferred from Rust, unit-test speed, individual PTY resource samples, or the
old 1.9.0 benchmark. The weak-host recommendation therefore remains unchanged.

Continue by fixing vi undo transaction boundaries, counted motions and history
behavior in a new bounded patch revision, rerunning this matrix, and then
completing the remaining Stage 0 compatibility/performance gates. Keep runtime
integration withheld until those gates pass. Every source change must bump
the candidate identity and regenerate its provenance/artifacts.

Upstream inputs were rechecked on this date:
[stable release](https://github.com/HalFrgrd/flyline/releases/tag/v1.10.0) and
[open PR #974](https://github.com/HalFrgrd/flyline/pull/974).
