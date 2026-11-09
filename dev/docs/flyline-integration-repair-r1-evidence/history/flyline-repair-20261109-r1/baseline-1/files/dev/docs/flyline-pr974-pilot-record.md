# Flyline 1.10.0 + PR #974 native pilot

Date: 2026-11-09. Candidate: **1.10.0-pr974.aae68bb4.r4**.

The local macOS integration implements the pinned source port, bounded vi and
history/unload fixes, managed library lifecycle, and opt-in session activation.
The patched release and production definition are **not published**. The
[release review packet](../flyline/release/README.md) contains the concrete
proposed payload; no installation URL is enabled in `tools/defs` yet.

The user explicitly requested local macOS validation only. No SSH connection,
remote installation, startup-file edit, default-shell change, public release,
remote-ssh working-tree commit, push, or upstream message was performed. Linux and weak remote hosts
remain unverified. The original [R1 report](flyline-pr974-pilot-record-r1.md)
and its evidence remain unchanged; its 13/17 failure is historical.

## Source and artifact identity

| Input | Identity |
| --- | --- |
| Stable base | v1.10.0, `ca910967af35579a2d455a071aa939778d8f6171` |
| PR #974 head | `aae68bb4acb43d7462bbe4abffedd6e2b10bd889` |
| Local port commit | `ce6529bc45bd0609cdde576877098e66492fc757` |
| Source tree | `d70b582492f52e526e122c93527cf98a59ac5d1e` |
| Unchanged Cargo.lock SHA-256 | `3162250ee645024bf56933a723a300f1850464d31acbbc0ba156eb80301085e9` |
| Library SHA-256 | `e73823eeeb046eb31b9941e1f951ec6aa346c0a3cf4ec0331fe188e55da77cc4` |
| Archive SHA-256 | `d535d6b8fef325458f043d76a43d03dba763dc9857c04417d0322a922b234c7a` |
| Toolchain | Rust 1.99.1 / Cargo 1.99.1, native `aarch64-apple-darwin`, locked release |

[Provenance](flyline-pr974-pilot-r4-evidence/provenance.json) pins the base
archive, all six patch hashes, local reconstructed parent, build commands and
library member. Local port commits reconstruct an upstream archive; they are
not original upstream commits. The upstream package still reports 1.10.0;
provenance/custom identity distinguish this build. SOURCE_DATE_EPOCH is a fixed
reproduction clock, not the actual build date.

The [patch series](../flyline/inputs.json) contains:

1. Reconciled PR #974 on 1.10.0.
2. Uppercase vi dispatch, unbound Normal keys, cursor clamping and real dot-repeat.
3. Undo transactions, counted movement and vi `k`/`j`, `/`/`?`, `n`/`N` history.
4. Bounded current-toolchain lint fixes.
5. Safe Bash input restoration on unload. Earlier unloading could dereference a
   null saved-stream name and pop active parser input, causing SIGSEGV.
6. Separate native fuzzy-history query buffer. Cancellation restores the original
   command, cursor, selection and undo history; acceptance edits the original
   buffer rather than retaining query changes in its undo history.

The build uses an isolated toolchain/cache and leaves the developer's global
Rust unchanged. Its rust-objcopy/libLLVM lookup issue was corrected; the final
[build log](flyline-pr974-pilot-r4-evidence/build.log) has no stripping warning.
The builder refreshes package/build-script metadata before packaging. Earlier
artifact hashes are exploratory and do not inherit final qualification.
Reproducible source and archive packaging do not promise identical library
bytes across paths, caches, SDKs or linkers; qualify each distributed hash.

The archive contains exactly `libflyline.dylib`, `LICENSE-MIT` and
`provenance.json`. Dependencies are the macOS system libraries listed in
[otool output](flyline-pr974-pilot-r4-evidence/otool.txt); the build-path entry
is the dylib's own install name. The self-contained Git source bundle retains
MIT licensing and the complete local source history. Local deliverables are in
`dev/flyline/dist/1.10.0-pr974.aae68bb4.r4/` (ignored build output), with
`SHA256SUMS` and [build instructions](../flyline/release/BUILDING.md).

## Native qualification

| Platform / Bash | Result | Scope |
| --- | --- | --- |
| macOS 27.2 arm64, Homebrew Bash 5.3.20 | Pass | This artifact and bounded local matrix |
| Same host, clean Readline | 32/32 controls | Ctrl-R history differs from the PR's redo |
| macOS system Bash 3.2 | Activation skipped | Guard and management compatibility tested; no native library loading claimed |
| Linux glibc/musl, Intel macOS, Linux aarch64 | Unverified | No asset proposed |
| SSH / weak remote host | Unverified | Deferred at user request |

- [32/32 vi probes](flyline-pr974-pilot-r4-evidence/native/results.json), through
  the real installer and optional activation in a temporary checkout: original
  `ac` → `bc`, insert/Normal movement, deletion/change/yank/paste, quick undo,
  redo, dot-repeat, counts, Unicode and ordinary/vi history, including draft
  restoration and undo preservation during vi search. None executed before the
  explicit final Enter. [Readline controls](flyline-pr974-pilot-r4-evidence/readline/results.json)
  preserve their actual Ctrl-R history behavior instead of pretending it is redo.
- [4/4 load/unload probes](flyline-pr974-pilot-r4-evidence/lifecycle/results.json):
  disposable `bash -i -c`, unload, rc rollback and later unload, followed by
  actual Readline vi editing. Mocks are not used to establish native ABI support.
- [3/3 managed history profiles](flyline-pr974-pilot-r4-evidence/history/results.json):
  Bash native, Bash/skim 5.9.0 and Atuin 18.14.1, with Starship 1.24.1 and
  real shell hooks. Selection remains editable, cancellation also restores the
  command after query edits, Up/k work, reload preserves the backend, Bash
  persists history, and Atuin records exit 1/duration without duplicate selection.
- [4/4 editor/provider combinations](flyline-pr974-pilot-r4-evidence/completion/results.json):
  Readline/Flyline with optional Carapace 1.8.2 `complete -D`, flags/values,
  dynamic Git refs, file/quoted-space paths and actual Tab plus vi controls.
  No provider invocation at startup or ordinary typing. The callback remains
  a developer prototype; provider runtime delivery is a separate task.
- [Direct PTY, tmux 3.8 and Zellij 0.44.2](flyline-pr974-pilot-r4-evidence/terminal/results.json):
  vi editing, Unicode paste, multiline input, Ctrl-C recovery, resize, Ctrl-D
  and terminal canonical/echo restoration. Only private test sessions were used.

The history harness now waits for raw input readiness after PROMPT_COMMAND's
marker: sending Ctrl-R before raw mode can let tty reprint consume it. With
that race removed, the [R3
control](flyline-pr974-pilot-r4-evidence/exploratory/native-query-cancel-r3.json)
still leaves `draftsearch_query`, while the
[R4 result](flyline-pr974-pilot-r4-evidence/history/results.json) restores `draft`.
That comparison justifies patch 6. Restrictive-sandbox socket/ps failures are
not compatibility results; primary terminal/resource runs used the required
local permissions.

## Performance

The final library passes all predeclared budgets. The [interactive
run](flyline-pr974-pilot-r4-evidence/performance/report.json) has 30 measured samples
per editor/HOME combination (180 measured PTYs plus 12 warmups), seeded randomized
order, and unchanged fixtures. Fresh/warm refer to isolated HOME state, not an OS
page-cache flush.

| Metric (median / p95) | Readline | Official 1.10.0 | Patched R4 |
| --- | --- | --- | --- |
| Startup, fresh HOME (ms) | 15.462 / 24.266 | 27.678 / 47.229 | 30.081 / 38.061 |
| Startup, warm HOME (ms) | 18.382 / 24.232 | 25.906 / 37.725 | 25.604 / 35.240 |
| Single key, fresh (ms) | 0.124 / 0.265 | 0.367 / 0.459 | 0.375 / 0.454 |
| Single key, warm (ms) | 0.120 / 0.279 | 0.379 / 0.560 | 0.388 / 0.554 |
| File Tab, fresh (ms) | 3.670 / 6.601 | 5.246 / 5.931 | 5.268 / 5.711 |
| File Tab, warm (ms) | 3.441 / 11.433 | 5.784 / 8.245 | 5.818 / 8.115 |
| Idle RSS, warm (MiB) | 7.188 / 7.250 | 11.156 / 12.219 | 11.297 / 12.281 |

R4 vi insertion p95 is 1.62/1.75 ms (fresh/warm). The 4 KiB bracketed-paste p95 is
5.60/2.36 ms, with only two measured paste samples per HOME case: treat that sparse
paste tail as exploratory. Idle RSS overhead is about 4.1 MiB median. Idle CPU samples
are 0 or approximately 1% of one core; the one-second ps sampling is coarse and does not
establish zero idle work. There were no invalid PTY samples.

Budgets were written before sampling: startup median/p95 overhead ≤30/60 ms versus
Readline, single-key median/p95 ≤2/8 ms, vi insertion p95 ≤8 ms, extra median idle RSS
≤12 MiB, file Tab median/p95 ≤50/150 ms, paste p95 ≤500 ms, sampled idle CPU ≤1% of one
core.

The [full-session run](flyline-pr974-pilot-r4-evidence/startup/results.json) uses the
actual managed install/runtime, Starship, Atuin on/off, 20 measured samples per scenario
(160 measured), two warmups plus warm-HOME priming. All four on/off comparisons pass the
separately predeclared 30 ms median / 60 ms p95 overhead limits:

| Backend / HOME | Disabled median (ms) | Enabled median (ms) | Median overhead (ms) |
| --- | --- | --- | --- |
| bash / fresh | 203.03 | 212.73 | 9.70 |
| bash / warm | 150.77 | 157.98 | 7.21 |
| atuin / fresh | 226.69 | 243.46 | 16.77 |
| atuin / warm | 173.29 | 186.52 | 13.23 |

These are local fixture measurements, not a weak-host or SSH latency prediction. The
startup-command benchmark complements actual first-usable-input PTYs; it does not
replace them. No CPU isolation, large history database, large repository/file tree, or
network transport was qualified. Full-session cases retain the historical benchmark
ordering; differences within scheduling noise, including a negative p95 delta, are not
evidence of a speed-up.

## Runtime and management changes

The `bash-builtin` layout requires an exact library member/checksum, readable
regular payload, exact Linux libc selection, disposable PATH-Bash load probe,
immutable release and absolute `.active/<tool>` link. Format-2 library records
coexist with format-1 executable records. Install/reinstall, expected sets,
update's existing install path, inventory, check/doctor, uninstall and conservative
prune understand libraries. No fake executable or new remote runtime dependency
is introduced. Prune aborts when active-library enumeration fails. Old working
links survive failed download/checksum/member/probe/switch attempts; open shells
retain their mapped code across updates.

Finalization runs after OS/host hooks. `REMOTE_SSH_ENABLE_FLYLINE=0` is the
default, including config-file support. Interactive TTY/TERM/Bash, owned active
library, external editor and external history guards precede loading. Actual
builtin state determines ownership, not inherited FLYLINE_VERSION. Verified
settings explicitly enable Vim, use Bash history and disable suggestions,
flycomp prompts, animations, mouse and tutorial. Atuin/skim Ctrl-R applies only
to insert/Emacs contexts, respects ATUIN_NOBIND and does not submit a selection
or replace Up/Normal-mode history and redo. Initial settings failure unloads
only the managed attempt. Disabled/skipped/failed/active outcomes are finalized
once per process; reload preserves later user bindings. New shells select anew.

[User documentation](../../docs/shell/flyline.md) explains activation, platform
limits, custom prefixes, history ownership, new-shell updates and recovery:
`REMOTE_SSH_ENABLE_FLYLINE=0 remote-ssh shell`. No default profile/tool list changed.

## Repository checks and delivery boundary

Full [just smoke](flyline-pr974-pilot-r4-evidence/smoke.log): **1463 passed,
30 skipped** (335.14 seconds). After the final resolver optimization, the
[focused management/ownership/prune/uninstall/asset
checks](flyline-pr974-pilot-r4-evidence/focused-management.log)
pass **171 tests**. Source preparation/checksum/lockfile checks pass **5 tests**
with the final six-patch record. Final static checks and diff validation are
recorded separately; developer scripts are covered by Ruff/mypy. Upstream
workspace library tests pass **1087, 1 ignored**; default and all-feature Clippy
with warnings denied plus rustfmt pass. No unrestricted Docker suite or
`just test-assets-live` was run.

The [evidence fingerprints](flyline-pr974-pilot-r4-evidence/fingerprints.json)
identify the exact checked scripts/runtime/records. Earlier startup results
retain the 31.01 ms warm-Bash overhead failure against a predeclared 30 ms
limit. The resolver was then simplified to avoid validating the same owned
record twice and resolving the link again; budgets were not relaxed.

The remaining delivery step is public prerelease publication of the prepared
payload, downloaded-asset digest verification, and promotion of the reviewed
manifest into `tools/defs` with its production snapshot tests/docs. Proposed
repository/tag/anchor are in the review packet. It does not commit unrelated
working-tree changes. Until publication is approved and completed, normal
`tool install flyline` is intentionally unavailable. Linux and weak-host
qualification remain separate follow-up work.
