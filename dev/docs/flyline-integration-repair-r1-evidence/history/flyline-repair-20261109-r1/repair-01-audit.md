type: audit
task_id: flyline-repair-20261109-r1
from: /root/flyline_auditor
to: /root
status: auditing
verdict: Pass
baseline: Unchanged baseline-1 R5 manifest and repair-01-plan.md; repair round 1
blockers[0]:
findings[0]:
suggestions[0]:
next_action: Coordinator archives this report after the audit path ends and completes the authorized local repair close-out. No further repair is required by this audit.

The current integrated repair meets the accepted local R5 repair contract and repair-01 plan. Audit-0 finding VAL-4-BUDGET is resolved on the changed round-1 source. The two valid round-0 failures remain valid historical results; they have not been erased, pooled, waived or invalidated. No required implementation, validation or documentation correction remains in the evaluated scope.

I remain independent: I did not plan, author or integrate either implementation round. I reviewed the frozen basis, audit 0, repair plan, integrated runtime/test/probe changes, pinned native source, current documentation, execution history and evidence. I edited no subject file. My tests and audit outputs were confined to disposable temporary paths.

Project root: `/Users/fm/Programming/00_Other/remote-ssh`.

Evidence shorthand `E` means `dev/docs/flyline-integration-repair-r1-evidence/`; `H` means `E/history/flyline-repair-20261109-r1/`; `R1` means `E/repair-01/`.

| R5 requirement | Assessment | Evidence and conclusion |
|---|---|---|
| **F3 — selection-scoped preflight** | **met** | Uninstall remains byte-identical to the independently audited round-0 implementation. Explicit names are validated before direct preflight; binary/bundle selections avoid `.active`; automatic selection requires inspection only when definitions include a library. Required preflight failure propagates before output collection or mutation. Independently reran all affected uninstall/library tests. |
| **F3 — unrelated paths, automatic discovery and atomic failures** | **met** | Independent tests pass explicit/automatic binary cases with `.active` as an ordinary file, directory symlink or broken symlink; preserved path/target and expected-tools behavior are asserted. Library/mixed/automatic selections reject invalid or unreadable required directories before link/release/config mutation. Controls without the unrelated path, valid mixed uninstall, format-1 records, aliases, unmanaged/outside-prefix paths and lifecycle/prune protections pass. |
| **F1 — late ownership and backend preservation** | **met** | The late `__atuin_initialized`/selected-backend guard is unchanged. It executes before resolver/loading and excludes late external Atuin while allowing successfully selected managed Atuin. Module 23/backend selection, reload policy and finalization ordering were not changed by repair 01. Independent affected tests and native ownership gate pass. |
| **F1 — full-rc and positive coverage** | **met** | OS/host late-hook fixtures cover both Atuin toggles, exact external callbacks/bindings, actual repeated `rcrc`, later edits and fresh nested Bash. Independent native OS/host cases report `skipped:external:bash`, preserved external state and zero managed resolver/load/settings/unload calls. Managed Bash, Atuin and NOBIND cases pass; early external/Bash/skim and once-per-process regressions remain covered. |
| **F2 — exact read-only builtin/function/alias detection** | **met** | Direct `builtin declare -F flyline` and `builtin alias flyline` replace the captured type lookup without mutating external owners. Exact enabled/disabled entries are still matched from read-only `builtin enable -a`, after toggle/TTY/Bash guards and without an external text filter. Independent tests cover actual functions/aliases, enabled/disabled entries, unrelated names and normal loading. Native externally disabled R5 stays disabled, with no managed calls or duplicate-load warning. |
| **F2 — stale markers** | **met** | Inherited FLYLINE strings alone still do not establish ownership. Independent absent/unrelated cases and native managed activation pass with stale inherited markers. No additional ownership cache or backend reselection was introduced. |
| **F4 — exact variable rollback** | **met** | Declaration snapshots and restore code are unchanged from audited round 0. Independent matrix covers each variable's unset, exported-unset, empty/nonempty exported and unexported scalar state across load/settings failures, including quoted/whitespace values, existence, declarations and child environments. Native ownership gate independently passes all 24 rollback cases. |
| **F4 — active/unload-failure controls and Readline** | **met** | Independent default tests retain intentional managed markers on success and failed unload, with the recovery warning. Native settings-failure ownership cases and both new real combined-call failures unload successfully, restore exact marker declarations and execute Readline vi editing from `ac` to actual argument `bc`. No premature execution occurs in the new native failure cases. |

| Validation clause | Assessment | Evidence and conclusion |
|---|---|---|
| **VAL-1-MATRIX — Bash 3.2/5.3 affected tests** | **met** | Independently ran all three affected files with the existing runtime_bash matrix, PATH `/opt/homebrew/bin:/usr/bin:/bin`, no pytest cache provider and bytecode disabled: **151 passed, 26 skipped in 41.52s**. Bash 3.2 management/graceful skipping runs; its activation-mutation cases remain intentionally skipped. Log: `/private/tmp/flyline-audit-r1-focused.log`. |
| **VAL-1-RED-FIRST — original regression sequence** | **met** | Audit-0 assessment and immutable retained red/green logs establish F3 → F1 → F2 → F4 with cause-specific failures before their fixes. Repair 01 preserves those regressions and adds combined-call failure coverage. The repair is an equivalent implementation correction, not a new feature requiring invented behavioral failures. |
| **VAL-2-PROBE — offline native ownership gate** | **met** | Reviewed the unchanged ownership.py isolation, explicit paths, expected/actual state, timeout/nonzero behavior and transcript retention. Independently reran current source with exact R5, Bash 5.3.20 and Atuin 18.14.1: **32/32 pass**. Output: `/private/tmp/flyline-audit-r1-ownership-20261109/results.json`. |
| **VAL-3-NATIVE — lifecycle/history/hash** | **met** | Current R1 retained lifecycle **4/4** and managed native Bash/skim/Atuin history **3/3** pass, including editable selection, cancellation, Up/k, persistence, status/duration and reload. Independent ownership/settings runs add direct current-source recovery and positive activation evidence. Independently hashed the actual library as `ac989a041026f49df1d3b544290ee3e67b497a0d3f82fe4785cd3c106e431d57`. |
| **VAL-4-METHOD — current startup protocol** | **met** | R1/startup-declaration.json identifies changed source/settings probe and exactly one acceptance run. The unchanged harness writes the original 30/60 ms budgets before eight scenarios × 20 measured rounds, with two warmups. All **160/160** measured samples are state-valid and retained. Independently recomputed every scenario's median/p95/min/max from raw samples with no differences from recorded statistics. No additional performance sampling was performed in this audit. |
| **VAL-4-BUDGET — current startup acceptance** | **met** | All four changed-source comparisons pass the original median ≤30 ms and p95 ≤60 ms incremental limits. Exact independently recomputed deltas appear below. This resolves the audit-0 finding for the repaired source, while both earlier failed datasets remain preserved as failures. |
| **VAL-5-FULL — full/static/diff checks** | **met** | Reviewed R1/smoke.json and complete smoke log: Bash syntax, ShellCheck, Ruff and mypy **23 source files** pass; pytest reports **1555 passed, 56 skipped in 458.65s**. Independent `git diff --check` passes. Full smoke was not rerun wholesale during this audit. |
| **VAL-5-DOCS — current status and links** | **met** | R7 plan/current repair record/README describe the changed-source result and preserved failures; final SDD acceptance remains assigned to execution/audit history. Requirement body and thresholds remain unchanged. Independently ran the local checker with output redirected to `/private/tmp/flyline-audit-r1-local-links.json`: **161 checks across 16 documents**, all pass. |
| **VAL-5-EVIDENCE — preservation/provenance** | **met** | Independently verified baseline **5** snapshot hashes; round-0 **9** frozen subject snapshots; round-1 **11** snapshots and corresponding current files; all **8** R1 source fingerprints; **361** historical evidence hashes. Audit-0 bytes retain SHA `c814fa77d01c347f087acd730f7850ce58c5f7ccecdb5f1550e6efc1a8e5b214`. All checks match. Verification output: `/private/tmp/flyline-audit-r1-verification.json`. |
| **SCOPE — local compatibility and exclusions** | **met** | The only round-1 runtime delta is 29-flyline.sh. F3 and F4 remain unchanged. No new runtime dependency, per-command hook, native code/bytes/pin/build, budget, production definition, release or platform scope was introduced. Loading remains opt-in, after late hooks and once per Bash process. |

| Repair-01 plan requirement | Assessment | Evidence and conclusion |
|---|---|---|
| **R1-1 — tutorial first; root flags plus cursor** | **met** | Tutorial disable remains first. Root options and the immediately following terminal cursor setter share one supported invocation. Directly inspected pinned src/cli.rs: root options are parsed alongside the subcommand and applied before SetCursor. Values and native write order are retained. |
| **R1-2 — Vim plus first conditional binding** | **met** | Bound Atuin/skim profiles combine explicit Vim enable with the unchanged first Ctrl-R action; the second Emacs binding remains separate and unchanged. NOBIND/no-widget paths explicitly enable Vim without user bindings. Pinned Key dispatch sets vim_mode before processing Bind. |
| **R1-3 — direct guards with exact builtin inspection** | **met** | Function/alias checks are direct, read-only and precede exact enabled/disabled builtin inspection. Independently rerun actual function/alias tests and real disabled-builtin gate pass. Ordinary executable lookup is not used as builtin ownership evidence. |
| **R1-4 — F4 unchanged** | **met** | Source comparison confirms snapshots/restoration unchanged; no `${var@a}` substitution was introduced. Independent full rollback matrix remains green. |
| **R1-VERIFY — effective settings and combined failures before qualification** | **met** | Independently executed settings.py against the exact frozen round-0 module. All four profiles have byte-identical complete `settings --all` and Ctrl-R key-list output; all twelve mandatory effective values and expected two/zero user bindings pass in both variants. Both real invalid combined calls unload, restore exact marker declarations, warn and demonstrate `bc` Readline recovery. Output: `/private/tmp/flyline-audit-r1-settings-20261109/results.json`. Recorded integration history places semantic/native gates before the one acceptance run. |

Pinned-source assessment: read only the authorized local R5 checkout's src/cli.rs, src/settings.rs and src/bash_builtin.rs and its Git pin/diff. HEAD is `d037c075ed30a61080873985ea2621d743ddfc64`, with no diff in these files. CLI SHA is `7974da24e519bf24e9d5f49f71050736b6ee322eaaf9e8e7788bd91bd221995e`; settings SHA is `4f43f8c4d0f2373fc3d72a58bdfb24f0ac395e83b08926eca0ad15650fb0a5b0`; builtin SHA is `d154a8da1d57c07bc74dbb5af33020bf503945c8e4b0dac650fa81487357c862`.

The shared HOME in the settings comparison does not allow the old variant to supply omitted settings to the new process. Each variant starts fresh Bash and loads the library; pinned bash_builtin.rs:383 calls reset_settings(), while settings.rs:469–485 owns process-local defaults and reset. The compared CLI setters mutate that in-memory state. Source inspection and independent native output support semantic equivalence, rather than call-count reasoning alone.

Current-source startup deltas, independently recomputed from all raw samples:

| Backend / HOME | Median overhead (ms) | p95 overhead (ms) | Original 30/60 ms limits |
|---|---:|---:|---|
| Bash / fresh | 12.5701045 | -12.272709 | pass |
| Bash / warm | 8.6956875 | -3.647708 | pass |
| Atuin / fresh | 17.505021 | -92.715583 | pass |
| Atuin / warm | 25.4900205 | 44.771625 | pass |

Finding disposition: **VAL-4-BUDGET resolved on round-1 source** (`74ee8407729bb3a4cc125eaf0b512200d86104de2759bd28688d5d6ecee2c305`). R1/startup/results.json SHA is `7729fde0b22c237f1ac510e1365d89701570f0b843b13c9c41d7a15cd49815db`.

The initial round-0 dataset still fails cold Atuin at **47.691959/59.533167 ms**, and its sole predeclared confirmation still fails at **47.292208/93.353541 ms** (median/p95). Both have 160 valid measured samples, with independently matching raw statistics. The initial dataset retains SHA `545a202b7700b3a4ba5981360b1be4bcbc16dad745b81304b8ffd96a3c5a5355`; confirmation retains SHA `1fe248860b6a4f4aa630b9a2cd89ea5c086c5fdea114ecb4a2455c8be08936b1`.

The new disabled cold-Atuin measurements have high tails. Negative p95 deltas describe the recorded comparison and do not establish stable causal acceleration. This audit applies the predeclared acceptance protocol; it neither invents a stronger repeatability requirement nor infers a Rust root cause. Changed source plus all required passing comparisons resolves the current gate without invalidating old failures or relaxing budgets.

Technical/regression conclusion: the source delta matches the repair plan, preserves effective settings/bindings and ownership/rollback semantics, and passes the required current local checks. No new technical defect or required correction was found. One automatic repair round was used; a second was not needed for this result.

Omissions and limitations: full smoke, lifecycle and managed-history results were reviewed from retained current-source evidence instead of redundantly rerunning all of them. The complete affected matrix, native settings/equivalence/failure gate and native ownership gate were independently rerun. No new startup/performance measurement was taken. Full editor/multiplexer requalification was not required for this shell-only equivalent initialization change. Linux, SSH, weak hosts, other architectures and other native Bash builds remain unverified and outside the authorized local macOS arm64 acceptance. No production release/manifest or Git mutation is implied by Pass. No approval wait occurred.

The coordinator owns archival and final workflow close-out after this read-only audit path ends.
