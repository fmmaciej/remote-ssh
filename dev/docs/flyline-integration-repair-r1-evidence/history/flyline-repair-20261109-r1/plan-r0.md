# R5 execution mapping — round 0

The accepted implementation plan is the unchanged R5 `Post-audit repair plan`, frozen under `baseline-1/files/dev/docs/flyline-implementation-plan.md`. This mapping records ownership and verification without changing its requirements. Planner: `/root/flyline_planner`; coordinator: `/root`; implementer and technical integration: `/root/flyline_implementer`.

| Order / requirement | Files / result | Acceptance |
| --- | --- | --- |
| 1 / F3 | `uninstall.sh`, uninstall/library tests; selection-scoped library preflight | Binary-only unrelated `.active` succeeds; library and mixed invalid directories fail before mutation; expected set and targets preserved. |
| 2 / F1 | `29-flyline.sh`, lifecycle tests | Late external Atuin OS/host hooks are excluded; selected managed Atuin remains supported; no backend reselection. |
| 3 / F2 | `29-flyline.sh`, lifecycle tests | Enabled/disabled exact builtin detection is read-only; functions/aliases and stale strings behave as required. |
| 4 / F4 | `29-flyline.sh`, lifecycle tests | Exact set/unset, scalar value and export attribute restoration at both failure stages; failed unload retains recovery state. |
| 5 / combined gates | New `ownership.py`, existing native probes and startup harness; repair record/evidence | Real R5 external ownership and Readline recovery, Bash/skim/Atuin history; eight scenarios, 20 measured rounds, predeclared 30/60 ms limits; focused tests, smoke, diff and live document links. |
| 6 / independent audit | Separate auditor after integrated handoff | Frozen basis, plan and technical regressions reviewed independently with `met`/`unmet`/`unverifiable` coverage; `Pass` required. |

Each F regression is run red for its audited cause before the fix and green afterward. Bash 3.2 validates management and graceful editor skipping; Homebrew Bash 5.3 is the native target. The R5 library hash/source pin remain unchanged. Current worktree and frozen historical evidence must be preserved.

Excluded: SSH/Linux, live asset checker, startup-file edits, releases, production manifest promotion, stage/commit/push. No additional dependency or feature is authorized. A true requirement change returns to the human; ordinary in-scope audit fixes use the same cycle with at most two repair rounds.
