type: audit
task_id: flyline-repair-20261109-r1
from: /root/flyline_auditor
to: /root
status: auditing
verdict: Findings
baseline: Frozen R5 manifest, initial implementation round 0
blockers[1]:
  Mandatory startup budget remains unmet.
next_action: Coordinator records this audit, preserves incomplete status, and obtains a concrete scope decision for further performance work. No additional ordinary F1–F4 repair was identified.

I independently reviewed the frozen R5 repair contract, original F1–F4 findings, required R4/R5 records, execution mapping/history, current runtime changes, regression tests, native ownership probe and retained validation evidence. I had no planning or implementation authorship. No subject files were edited.

Project root: `/Users/fm/Programming/00_Other/remote-ssh`.

Evidence shorthand `E` below means `dev/docs/flyline-integration-repair-r1-evidence/`.

| Requirement | Assessment | Evidence and conclusion |
|---|---|---|
| **F3 — selection-scoped preflight** | **met** | `uninstall.sh:151` adds direct preflight after explicit name validation. Binary/bundle selections bypass `.active`; automatic discovery checks it only when definitions include a library. Required failures propagate directly before collection or mutation. |
| **F3 — unrelated paths and binary controls** | **met** | Independent focused run passes explicit and automatic binary tests for ordinary files, directory symlinks and broken symlinks, preserving the path/target and expected-tools behavior. Existing automatic discovery without the unrelated path also passes. |
| **F3 — atomic library/mixed rejection** | **met** | Library, mixed and automatic selections reject invalid `.active` before changes. Tests check selected releases, binary links, exact expected-tools bytes and unrelated targets. The unreadable-directory cases ran successfully under this user; their permission escape hatch did not account for the 26 skips. |
| **F3 — lifecycle regressions** | **met** | Valid mixed uninstall, format-1 releases, aliases, unmanaged/outside-prefix paths, library lifecycle and prune tests pass in the independent affected suite. |
| **F1 — late ownership and backend preservation** | **met** | `29-flyline.sh:75` checks the current `__atuin_initialized` marker against the selected backend before resolver/load/settings. Managed `atuin` remains eligible; other selected backends exclude the late external owner. Module 23 and `rc.sh` are unchanged from source-before. |
| **F1 — full-rc scenarios** | **met** | Full-rc OS/host fixtures cover both Atuin toggles, preserved callbacks/bindings, repeated actual `rcrc`, later binding edits and fresh nested Bash. Independent native tests confirm all four real late-Atuin cases remain `skipped:external:bash`, with no managed resolver/load/settings/unload calls. |
| **F1 — positive and preserved paths** | **met** | Managed Bash, Atuin and `ATUIN_NOBIND` activation pass independently with the real R5 library. Existing early external, Bash/skim and once-per-process cases pass. No backend reselection or second ownership cache was introduced. |
| **F2 — exact read-only builtin detection** | **met** | `29-flyline.sh:80` reads `builtin enable -a` and matches only exact enabled/disabled Flyline entries. The probe follows toggle/TTY/Bash guards and uses Bash matching without an external filter. Function/alias exclusions remain effective. |
| **F2 — external state and stale markers** | **met** | Independent tests cover enabled, disabled, actual function/alias, unrelated builtin name and absent builtin. Native externally disabled R5 remains disabled, produces no duplicate-load warning and receives no managed calls. Stale inherited markers permit normal managed activation. |
| **F4 — exact rollback** | **met** | `29-flyline.sh:91–119` independently snapshots set/unset state, value and export attribute, then restores them without replaying function-local declarations. Independent tests cover both variables, all six states, both failure stages, quoted/whitespace values and child environments. |
| **F4 — loaded-state controls and Readline** | **met** | Successful activation retains managed values/export behavior. Failed unload retains recovery markers and warning. Native settings-failure cases independently restore attributes and execute actual Readline vi editing producing argument `bc`. |

| Validation clause | Assessment | Evidence and conclusion |
|---|---|---|
| **VAL-1-MATRIX — affected tests on Bash 3.2/5.3** | **met** | Independently ran all three affected files with `/bin/bash` 3.2.57 and PATH-selected Homebrew Bash 5.3.20: **147 passed, 26 skipped in 39.70s**. Skips are the expected Bash 3.2 activation-mutation cases; its management and graceful fallback tests execute. |
| **VAL-1-RED-FIRST — regression-first sequence** | **met** | Retained commands/logs and execution history establish F3 → F1 → F2 → F4 red/green order. Red failures match the audited causes: F3 rejects unrelated paths; F1 fails external ownership state; F2 fails only disabled-builtin ownership; F4 fails declaration/export restoration. |
| **VAL-2-PROBE — offline native ownership gate** | **met** | Reviewed `ownership.py` and `managed.py`: explicit required paths, isolated managed installations/PTYS, supplied local archive interception, expected/actual results, retained transcripts, timeout/wrong-state failure and no download behavior. Independent current-source execution passes **32/32**. |
| **VAL-3-NATIVE — lifecycle/history/hash** | **met** | Independently repeated ownership/rollback gate; reviewed retained lifecycle **4/4** and Bash/skim/Atuin history **3/3**, including editable selection, cancellation, Up/k, persistence, status/duration and reload. Independently hashed the actual library: `ac989a041026f49df1d3b544290ee3e67b497a0d3f82fe4785cd3c106e431d57`. |
| **VAL-4-METHOD — startup measurement protocol** | **met** | Each retained full dataset contains eight scenarios × 20 valid measured samples, with two warmups and saved 30/60 ms budgets. Reviewed unchanged harness/state checks and independently recomputed every scenario’s median/p95/min/max exactly from raw samples. All 320 measured samples remain present. |
| **VAL-4-BUDGET — startup acceptance** | **unmet** | Cold Atuin overhead is **47.691959 ms median / 59.533167 ms p95** initially, and **47.292208 / 93.353541 ms** in the sole predeclared confirmation. The median limit is 30 ms and p95 limit 60 ms. Both full runs fail. |
| **VAL-5-FULL — repository checks** | **met** | Reviewed final `just smoke` command/log: Bash syntax, ShellCheck, Ruff, mypy and **1551 passed, 56 skipped**. Independent `git diff --check` passes. The initial SC2046 failure and its correction remain preserved. Full smoke was not redundantly rerun during this audit. |
| **VAL-5-DOCS — status and local links** | **met** | Current R6 plan and repair record explicitly retain incomplete status and startup failure. Accepted requirement body remains unchanged. Independently ran the local checker with output redirected to `/private/tmp`: current expanded document set passes **135 checks across 12 documents**. The earlier saved 132/11 result predates the additional history document. |
| **VAL-5-EVIDENCE — provenance and preservation** | **met** | Independently verified all **5 baseline snapshot hashes**, **9 final source fingerprints**, all source-before snapshot hashes and **361 historical evidence fingerprints**. Archived executed ownership source is AST-equivalent to the formatted source; the independent native rerun also directly validates the current source. |
| **SCOPE — compatibility and exclusions** | **met** | Runtime changes are confined to the two planned Bash modules, with no new runtime dependency or per-command hook. Source pin/native bytes remain unchanged; production `tools/defs/flyline.sh` is absent. Local-only evidence is accurately bounded. No native defect requiring fork changes was established. |

Required finding:

**[P2] VAL-4-BUDGET: cold Atuin startup does not satisfy the mandatory completion gate.**

Evidence: `E/startup/results.json`, `E/startup-confirmation-1/results.json`, their predeclared budgets and `E/startup-confirmation-declaration.json`.

Impact: functional repairs and green full tests cannot establish completion under the accepted R5 contract. The result must remain incomplete and cannot receive `Pass`.

The guard diagnostic’s 3.85 ms increment and enabled-before/current diagnostic’s 2.627916 ms paired median increment narrow attribution only. They do not identify a Rust defect, establish an old on/off acceptance pass, or invalidate either valid failure. No further benchmark was run during this audit.

I found **no additional required F1–F4 implementation or validation correction** within the accepted shell repair scope. Further performance work needs a concrete scope decision; changing the threshold would be a requirement change.

suggestions[0]:

Omissions and limits: full smoke, lifecycle and managed-history suites were assessed from retained evidence rather than repeated wholesale; affected regressions and the complete new native ownership gate were independently rerun. Full editor performance/multiplexer requalification was unnecessary under the shell-only contract. Linux, SSH, other architectures/Bash builds and weak-host behavior remain unverified and excluded. No audit approval wait occurred.

Independent native evidence: `/private/tmp/flyline-audit-native-ownership-20261109/results.json`.

Independent documentation evidence: `/private/tmp/flyline-audit-local-links-20261109.json`.
