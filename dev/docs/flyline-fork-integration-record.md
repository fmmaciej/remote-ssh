# Flyline fork integration record

Date: 2026-11-09. Candidate: **1.10.0-pr974.aae68bb4.r5**.
Status updated 2026-11-10: source and [R5 prerelease](https://github.com/fmmaciej/flyline/releases/tag/remote-ssh-v1.10.0-pr974.aae68bb4.r5)
published; public payload verified and generated production manifest enabled.
The [promotion plan and results](flyline-release-promotion-plan.md) record
this follow-up. Native measurements below remain the original R5 evidence.

## Source ownership and history

The user supplied [fmmaciej/flyline](https://github.com/fmmaciej/flyline), a real
fork of HalFrgrd/flyline. The downstream
[remote-ssh-vim branch](https://github.com/fmmaciej/flyline/tree/remote-ssh-vim)
contains six patch commits followed by one build/documentation commit. It is
based on the real stable 1.10.0 commit, retaining upstream ancestry. The fork's
`master` was not changed. No upstream PR, comment or message was sent, and no
remote-ssh working-tree commit or push was made.

| Item | Identity |
| --- | --- |
| Stable base | `ca910967af35579a2d455a071aa939778d8f6171` |
| PR #974 input | `aae68bb4acb43d7462bbe4abffedd6e2b10bd889` |
| Code after six patches | `27d2f687eec8807f39f81da4969520a2e06305a5` |
| Final fork commit | `d037c075ed30a61080873985ea2621d743ddfc64` |
| Fork source tree | `eca6115674f2890a3a6e1c1ee6ef5fe57968039b` |
| Unchanged Cargo.lock SHA-256 | `3162250ee645024bf56933a723a300f1850464d31acbbc0ba156eb80301085e9` |
| R5 library SHA-256 | `ac989a041026f49df1d3b544290ee3e67b497a0d3f82fe4785cd3c106e431d57` |
| R5 archive SHA-256 | `38a7c65eb6e3c8c7458cdebea36607ae2e5577279b96ce2f6e2907b5ff9afaf3` |

The [commit map](flyline-fork-pilot-evidence/port-commits.json) records every
patch digest and applied commit. Rust source is unchanged from the qualified
[R4 pilot](flyline-pr974-pilot-record.md). The genuine upstream checkout also
retains an original tracked demo GIF that the historical archive reconstruction
had omitted through .gitignore. New downstream files contain only build metadata,
a builder and documentation. R4's reconstructed commits/artifacts/evidence remain
historical; their hashes and performance are not substituted for R5.

## Build and future release boundary

Build logic now lives in the fork's
[remote-ssh directory](https://github.com/fmmaciej/flyline/tree/remote-ssh-vim/remote-ssh).
Its builder verifies the requested commit, clean checkout, ancestry, unchanged
lockfile, native target and Rust/Cargo 1.99.1, then uses locked dependencies,
refreshes Git/build-time metadata and packages library/MIT/provenance. The
integration project's `candidate.py build-fork` checks its pinned commit and
identity before delegating; it does not build on runtime hosts. Three new source
rejection regressions and a fork-pin consistency test cover this entrypoint.

The new binary is rebuilt from the actual fork commit and qualified by its exact
hash. [Provenance](flyline-fork-pilot-evidence/provenance.json) records source
repository/commit/tree, real patch commits, toolchain, commands and library member.
The fixed SOURCE_DATE_EPOCH is a reproduction clock. Bit-identical native output
across SDKs/linkers/caches/paths is not promised. The final build succeeded with a
nonfatal macOS linker diagnostic falling back to /tmp when the sandbox denied
DARWIN_USER_TEMP_DIR lookup; it is retained in the build log. No stripping failure
occurred.

The published tag is `remote-ssh-v1.10.0-pr974.aae68bb4.r5`, at the exact
source commit above. Its prefix avoids the upstream `v*.*.*` release workflow,
which assumes an unmodified Cargo.toml version and a different asset matrix.
The release belongs to **fmmaciej/flyline**, whose source archive matches its
real tagged source. The former asset-only tag proposal in remote-ssh is
superseded. Publication was initially deferred during this qualification record;
the user later published the tag and prerelease through GitHub's web interface.

The ignored local payload is `dev/flyline/dist/1.10.0-pr974.aae68bb4.r5/`.
The [release packet](../flyline/release/README.md) documents the public payload.
`tools/defs/flyline.sh` is now generated from that verified release; normal
`remote-ssh tool install flyline` is available. Existing default profiles and
expected-tools config remain unchanged.

## Native local validation

Validation remains **local macOS only**, per the user: macOS 27.2 arm64 with
Homebrew Bash 5.3.20. System Bash 3.2 retains its guard/management support;
no native loading is claimed for it. Linux, weak remote hosts, Intel macOS,
other Bash builds and SSH transport remain unverified. No SSH test host or global
installation/configuration was used. Git transport to the supplied GitHub fork
is separate from remote-host testing.

| Probe | R5 result |
| --- | --- |
| Real installer/activation plus vi | [32/32](flyline-fork-pilot-evidence/native/results.json) |
| Load/unload/Readline restoration | [4/4](flyline-fork-pilot-evidence/lifecycle/results.json) |
| Managed Bash native/skim/Atuin history | [3/3](flyline-fork-pilot-evidence/history/results.json) |
| Readline/Flyline × optional Carapace callback | [4/4](flyline-fork-pilot-evidence/completion/results.json) |
| Direct PTY, tmux and Zellij | [3/3](flyline-fork-pilot-evidence/terminal/results.json) |

The matrix checks actual executed arguments and rejects early submission. It
covers vi editing/counts/undo/redo/dot/history, editable history selection,
cancellation after editing a search query, Up/k navigation, backend preservation
on reload, Bash persistence, Atuin exit/duration/no duplicate selection, generic
`complete -D`, dynamic Git candidates, quoted paths, Unicode/multiline input,
paste/resize/Ctrl-C/Ctrl-D and terminal restoration. Helpers use isolated HOME,
checkout, prefix, databases and private multiplexer sessions. Pinned external
binaries are Atuin 18.14.1, skim 5.9.0, Starship 1.24.1, Carapace 1.8.2,
tmux 3.8 and Zellij 0.44.2. The Carapace callback is still a separate developer
prototype, not shipped provider runtime support.

## R5 measurements

All predeclared budgets pass for this exact library. The
[interactive run](flyline-fork-pilot-evidence/performance/report.json) uses 30
measured rounds plus two warmups across three editors and fresh/warm HOME
(180 measured PTYs, 12 warmups), with randomized order. Fresh HOME is not an OS
page-cache flush. Medians/p95 below are local fixture observations, not weak-host
or SSH predictions.

| Metric (median / p95) | Readline | R5 |
| --- | --- | --- |
| Startup fresh HOME (ms) | 21.535 / 23.473 | 31.563 / 48.301 |
| Startup warm HOME (ms) | 22.087 / 23.832 | 34.075 / 37.649 |
| Single key fresh (ms) | 0.107 / 0.211 | 0.364 / 0.442 |
| Single key warm (ms) | 0.107 / 0.218 | 0.443 / 0.571 |
| File Tab warm (ms) | 3.430 / 8.595 | 6.804 / 8.886 |
| Idle RSS warm (MiB) | 7.188 / 7.312 | 11.297 / 12.422 |

Budgets were retained: startup overhead median/p95 ≤30/60 ms versus Readline;
single-key median/p95 ≤2/8 ms; vi insertion p95 ≤8 ms; extra median RSS ≤12 MiB;
file Tab median/p95 ≤50/150 ms; 4 KiB paste p95 ≤500 ms; sampled idle CPU ≤1%
of one core. Idle CPU uses a coarse one-second ps sample and does not prove zero
idle work. Paste has only two measured samples per HOME case, so its tail is
exploratory. No large history DB/file tree or CPU-isolated/remote machine was tested.

The [full-session startup run](flyline-fork-pilot-evidence/startup/results.json)
uses the real managed runtime, Starship and Atuin on/off, with 20 measured samples
per scenario (160 measured), two warmups plus warm-HOME priming. All four paired
comparisons pass the predeclared 30 ms median / 60 ms p95 overhead limits:

| Backend / HOME | Disabled median (ms) | R5 median (ms) | Overhead (ms) |
| --- | --- | --- | --- |
| bash / fresh | 180.13 | 188.29 | 8.15 |
| bash / warm | 127.79 | 140.64 | 12.85 |
| atuin / fresh | 204.92 | 217.02 | 12.10 |
| atuin / warm | 156.36 | 170.73 | 14.37 |

Startup-command timings complement actual first-input PTYs. The startup suite
retains historical scenario order; scheduling noise is not a demonstrated speed-up.

## Checks and evidence

Upstream library tests: **1087 passed, 1 ignored**. Required rustfmt and Clippy
with warnings denied pass. Rustdoc completes with existing documentation warnings
and recorded SDK/linker diagnostics; unrelated documentation was not rewritten.
The fork builder also passes Ruff and mypy. The integration's source-preparation/
fork-pin tests pass **9 tests**. The complete repository smoke result and final
static/diff validation are recorded below when the current run finishes.

Full [just smoke](flyline-fork-pilot-evidence/smoke.log) passes: **1467 passed,
30 skipped** in 319.57 seconds, including the nine candidate/fork-pin checks.
Bash syntax, ShellCheck, Ruff and mypy pass. `git diff --check` and local document
link checks pass. The R1 test-source reference was frozen to its exact historical
bytes when the fork tests extended that file; recorded hashes are unchanged.
Both historical R1 and R4 evidence inventories still verify.


The [evidence inventory](flyline-fork-pilot-evidence/fingerprints.json) binds the
checks to snapshots of the fork build helper, integration entrypoint, manifest,
runtime and test sources. No `just test-assets-live` or unrestricted Docker
suite was run. At the original qualification close-out, the source branch and
local validated payload were the completed scope. The later user-published
release and production promotion are recorded separately in the
[promotion plan and results](flyline-release-promotion-plan.md).
