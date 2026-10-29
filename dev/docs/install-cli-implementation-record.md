# Installed CLI implementation record

Date: 2026-10-28. Fresh implementer; implementation authorized by the user as recorded by the coordinator. Contract: accepted R0 plan SHA-256 `503e5fb19da5ff45dc3484cc8562dc8169bb7fb6be24e2c712d4f61b9ee38339`. No plan edits.

## Baseline and draft disposition before runtime edits

All 20 source fingerprints from `install-cli-planning-evidence/worktree-before.json` matched before edits; HEAD remains `39226a2d9074acf08279e7c3edde6a51cc2a629c`. Raw inherited diff and untracked test snapshot are in `install-cli-implementation-evidence/`.

| Inherited hunk | Disposition |
| --- | --- |
| bin/remote-ssh bootstrap | Revise: retain one-link relative resolution, add physical paths, explicit errors and 40-link bound. |
| install.sh error guard | Revise: preflight before confirmation, publish before tools, explicit propagation. |
| dirs.sh link preparation | Revise: retain existing helper chmod, split nonmutating preflight and safe publication, canonical absolute exact ownership. |
| post_install.sh footer | Revise: full-path guide, conditional directory-aware PATH and shell-safe interactive placeholder. |
| 00-interactive.in local/SSH wording and -i | Retain wording/-i; revise quoting and explain activation boundary. |
| docs/install.md inserted guidance | Retain install versus activation distinction; revise PATH, custom dir, collision and lifetime/lifecycle details. |
| test_post_install.py added assertions | Revise for full-path and conditional footer; retain unrelated template ordering checks. |
| untracked test_install_cli.py | Revise/extend: real rcfile, real tool installer boundary, collision/failure/order/bootstrap/lifecycle coverage. |
| Welcome runtime, tests, docs and process/planning artifacts | Out of scope; preserve exact bytes. |

No unrelated hunks exist in the scoped inherited installer files. AGENTS.md and test_runme.py start clean. conftest.py will remain unchanged; local fixtures suffice. No subagents, network/live assets, real-HOME installation, staging, commit or push.

## Narrow batch-failure addendum

Coordinator and independent auditor accepted [addendum](install-cli-implementation-addendum.md) (SHA-256 `ceddfb157e3bb6709d08b09b3d01f6eae1d1c205d7f9c3505749e3e6302bd09f`), [audit](install-cli-addendum-audit.md). This permits only explicit mkdir/per-tool guards in `tools/lib/install/install.sh`, preserving one full-array facade call. The temporary per-tool facade approach was replaced before the final candidate; existing expected-tools stubs remain unchanged. The helper guards prevent Bash conditional contexts from suppressing early errors. Failure tests cover first/middle attempts, existing expected-tools sentinel, retained successful tool and CLI, plus invalid INSTALL_PREFIX.

## Implementation decisions

- Preflight computes the physical executable source, validates its preparation eligibility, makes relative INSTALL_BIN_DIR absolute against the caller PWD, and checks literal ownership without filesystem writes. Confirmation remains after that check.
- Publication creates/canonicalizes the destination directory only after confirmation, rechecks ownership, prepares the CLI executable and uses non-overwriting `ln -s SOURCE BIN_DIR/`. It checks the result and exact target; a failed ln also rechecks for a helpful collision diagnostic. Race coverage is limited to the final entry, as planned.
- Existing checkout-helper executable preparation remains separate after tool installation. Only remote-ssh is newly linked. A failed tool batch leaves the published CLI available and skips environment preparation, expected-tools and completion output.
- Bootstrap follows portable one-link readlink targets relative to each link directory, canonicalizes directories physically, rejects unresolved source paths and stops at 40 links. REMOTE_ENV_DIR and doctor fallback remain in place.
- Footer prints the installed location plus independently executable full-path guide and rcfile commands. PATH comparison recognizes physical directory aliases; exports retain literal $PATH. A dedicated quoted interactive-command template marker avoids interpolating raw shell arguments. Other templates retain their original format/order.
- conftest.py, runme runtime, assets/definitions, hooks, welcome runtime/tests/docs, prune and uninstall were not edited. New runme integration uses the real candidate/runtime with a local fake clone/update transport. All new install subprocesses have a 20-second timeout, isolated temporary HOME/XDG, and selected-interpreter env-bash binding. Optional update and Git identity shell integrations are disabled in this fixture so activation tests cannot invoke transport or read user identity configuration.

## Verification progress and preserved failures

Raw output is retained under `install-cli-implementation-evidence/`; final commands/environment/status are separate JSON records. Initial focused command was `uv run --project dev pytest -q dev/tests/test_install_cli.py dev/tests/test_post_install.py dev/tests/test_runme.py` (exit 1: 60 passed, 6 failed). The failures were a fixture assumption that the optional navi-dependent `cheats` alias always exists; activation now checks the guaranteed `rhelp` alias.

The second focused command added `dev/tests/test_install_expected_tools.py` (exit 1: 76 passed, 12 failed). Six new failure-fixture cases referred to nonexistent `bin/sshf`; the actual helper is `bin/ssh-find`. Six printed-command cases successfully activated the real shell, then the fail-fast Git stub marked local `git config` reads as network. Disabling the optional Git session identity integration avoids this unrelated operation; network boundaries remain fail-fast and their absence is asserted. Neither run involved actual network traffic.

The third focused run used the same four modules (exit 0: 94 passed, 52.45s), including the completed helper-addendum tests, real runme clone/update path and runtime binding assertions. Two final small runtime cleanups occurred while that run was in progress (diagnostic recheck after ln failure, and canonical footer path assigned to the existing local repo_dir). Therefore that pass is preliminary; the frozen candidate is checked again in `focused-final.log`. Scoped shellcheck returned 0, with raw output in `scoped-shellcheck.log`.

The final source snapshot is `final-source-hashes.json`. `interpreters.json` records Bash 3.2.57 and Bash 5.3.20 version output, selected env-bash child binding, and Zsh 5.9. Printed guide/local activation commands run in both selected Bash versions and Zsh -f; real shell markers/aliases are checked only after explicit rcfile activation. Ordinary runme-followup shells load no rcfile and assert no marker, prompt, function, alias or checkout helper leakage. Startup files are byte-snapshotted before/after.

## Frozen R0 verification outcome

The frozen final focused run passed **94/94 in 44.70s**, exit 0 (`focused-final.log`, `focused-final-result.json`). Pre/post-focused and post-smoke source hashes match `final-source-hashes.json` exactly. Final Ruff check, Ruff format --check and git diff --check each returned 0 (`static-final.log` / `static-final-result.json`). Scoped shellcheck command was `shellcheck bin/remote-ssh tools/lib/commands/install.sh tools/lib/install/dirs.sh tools/lib/install/install.sh tools/lib/install/post_install.sh`, exit 0.

**The full R0 smoke did not pass.** `just smoke`, with UV_OFFLINE=1 and the existing task cache, returned 1. Bash syntax, complete shellcheck, Ruff and mypy passed; full pytest reported **924 passed, 58 skipped, 4 failed in 351.19s**. Raw output is `smoke-final.log`; command/timestamps/environment/status and unchanged-source assertion are `smoke-final-result.json`. Those existing names identify the first frozen R0 candidate and must not be overwritten by a later repair run.

Failures preserved for independent review:

1. `test_guide.py::test_remote_ssh_guide_supports_post_install_section`, line 481: existing assertion requires literal double quotes around a simple rcfile path; the new shell-safe %q renderer emits this simple argument without quotes. Full focused printed-command execution passes; nevertheless this is a failing required suite case and requires the separately planned repair.
2. `test_tmux.py::test_tmux_checkout_paths_reload_and_confirmed_restart`: tmux cannot create its temporary Unix socket, reporting `Operation not permitted`. This is a sandbox permission limitation; the coordinator was asked to perform the required check with appropriate permission. No tmux source/test was changed and no workaround attempted.
3. `test_welcome_bundled.py::test_bundled_and_external_replay_preserve_text_and_terminal_transport` with controlling_terminal=True, on both Bash versions: output_tail contains only READY-TRANSPORT instead of rendered text plus the marker. Cause is unconfirmed; these pre-existing welcome changes/tests are out of installer scope. The coordinator received the exact failures; no welcome edit or speculative repair was attempted.

The source remains frozen for the independent R0 implementation audit. `candidate-R0.patch` records the full owned diff against HEAD, including the initially untracked install-CLI tests. It was reviewed against the inherited draft disposition; unrelated work remains preserved. Completion is **pending** the separate repair process and a passing complete smoke, not inferred from focused tests. No staging, commit, push, live assets or real-HOME installation occurred. Available publication-race evidence uses local macOS/BSD ln; no Linux host was available.

## R1 narrowly planned semantic test repair

The coordinator accepted [repair plan](install-cli-repair-plan.md), SHA-256 `afc10272f6d7f4567a437d234849d9a5011bfc04b05f61009b9355b9dfcbcb6d`. Pre-edit verification matched all **12 frozen R0 sources**, **178 protected files**, and **3 coordinator checkpoint files**. No runtime/other test/fixture edit was made. R0 evidence and completed audit remain intact.

Only `test_remote_ssh_guide_supports_post_install_section` was changed: it extracts exactly one standalone activation command, parses it with a fresh Bash and test-local argument-capture function, and checks the exact NUL-separated `--rcfile`, checkout rcfile and `-i` arguments. BASH_ENV and ENV are excluded for this subprocess. Existing content assertions remain; the new interactive placeholder must also be absent. Pre/post test-file hashes and the one-case diff are preserved in `install-cli-implementation-evidence/r1/`. The initial R1 snapshot contains 13 sources.

Initial R1 checks: exact case **1 passed/0.33s**, focused guide + post-install **26 passed/15.71s**, scoped Ruff check and git diff --check exit 0. Ruff format --check returned **1** because the new capture_env comprehension is 107 columns and needs multiline formatting. This is an implementer formatting omission. It was reported before any post-freeze edit; the initial R1 source hashes remain unchanged and all raw logs/results are retained. The coordinator was asked for a same-case formatting correction followed by a new freeze and required repeat checks. This initial R1 candidate is not ready for full smoke.

For B2, the coordinator's separate permission-enabled fresh-session targeted recheck passed **5 tests**, covering tmux and all four welcome transport variants. See `install-cli-coordinator-evidence/r0-terminal-recheck.log` and its result JSON (`outside_sandbox=true`, `start_new_session=true`). Welcome and tmux sources/tests remain unchanged; precise cause of the earlier PTY behavior is not claimed. The final full smoke will be run by the coordinator outside the sandbox on the final R1 snapshot.

### R1 final local checks and handoff

The coordinator authorized the same-case multiline formatting fix. Initial R1 files/logs/hashes remain at `install-cli-implementation-evidence/r1/`, explicitly marked pre-format by `initial-freeze-invalidated.json`; the final R1 snapshot and all repeated checks are separate under **`install-cli-implementation-evidence/r1/final/`**. Only the new capture_env comprehension changed during this finalization. `format.diff` records that change; `repair.diff` records the full authorized one-case change against the original test file. The final 13-source hash manifest SHA-256 is `d66ef774b5518865f9576e8a3c0b10808743f7d0ddb0b155aedba37bbc3c55f3`.

Repeated final exact case: **1 passed in 0.38s**, exit 0. Final guide + post-install focused: **26 passed in 15.56s**, exit 0, including existing unusual-path real activation under Bash 3.2/5.3 and Zsh. Whole-file Ruff check returned 0; scoped formatter on the exact repaired function (stdin filename `dev/tests/test_guide.py`, using dev configuration) returned 0; git diff --check returned 0. Post-focused hashes match all 13 frozen sources, and all 178 unrelated protected hashes still match. No source edit followed this final freeze.

Whole-file Ruff format --check still returns 1 because two other pre-existing cases need unrelated formatting (git-setup assertion near line 17 and config-string literal near line 118). Raw formatter diffs for the preserved original test file and final file are `preexisting-format-diff.log` and `current-format-diff.log`; neither final diff hunk touches the repaired case. They are retained as an explicit pre-existing formatting limitation. The coordinator instructed preserving those out-of-scope bytes and using the scoped format check; no formatting failure was suppressed or relabeled as a whole-file pass.

**Ready for coordinator full R1 smoke** outside the sandbox with `start_new_session=True`, using `r1/final/source-hashes.json`. The implementer did not run another full smoke. Acceptance remains pending the full smoke result and a fresh independent R1 audit.

### R1 coordinator full smoke: timeout, verification still pending

The coordinator launched the complete, unfiltered `just smoke` outside the sandbox with `start_new_session=True` and `UV_OFFLINE=1`, against the final 13-source snapshot at `r1/final/source-hashes.json`. An earlier launcher attempt pointed at the superseded pre-format snapshot and stopped at the source precheck before any tests; it is not a smoke result. The corrected full run used the final snapshot.

**The corrected R1 full smoke timed out after 1200 seconds and did not pass.** The launcher raised `TimeoutExpired` before normal `r1-smoke-result.json` metadata could be written. Preserve the [raw smoke log](install-cli-coordinator-evidence/r1-smoke.log) and [timeout result](install-cli-coordinator-evidence/r1-smoke-timeout-result.json), which records outcome `timeout`, timeout_seconds 1200, coordinator session exit 1, outside_sandbox=true and start_new_session=true. The log confirms syntax, ShellCheck, Ruff and mypy passed before pytest; termination subsequently produced recipe exit 143. There is no completed pytest summary or passed-suite result for this attempt.

The coordinator reported that disposable pytest-1198 state places the stall at the first `test_upstream_atuin_full_rc_lifecycle`, before `atuin.calls` was created. This observation neither counts that case as passed nor establishes a CLI regression. After verifying the remaining processes belonged to this run, the coordinator terminated process group 28838. The coordinator is conducting bounded read-only environment diagnostics before deciding on any retry; Atuin, runtime, tests and fixtures remain unchanged. The implementer did not run another suite or change source files.

The fresh R1 auditor reports B1 closed, with the 13-source and 178-protected-file checks matching, and its own 38 probes plus exact-case reproduction passing. **B2 and overall acceptance remain pending a successful complete smoke and the final independent audit verdict.** This report is not acceptance. For this record-only update, the implementer again verified all 13 final source hashes and all 178 protected hashes match; all earlier R0/R1 logs, failures, snapshots and audit material remain preserved.

### R1 final complete smoke passed; independent acceptance pending

The coordinator's subsequent full, unfiltered `just smoke` completed with **exit 0: 928 passed, 58 skipped in 340.90s**. The complete raw output is [r1-smoke-retry.log](install-cli-coordinator-evidence/r1-smoke-retry.log); exact command, launcher settings, elapsed time, status and source fingerprints are in [r1-smoke-retry-result.json](install-cli-coordinator-evidence/r1-smoke-retry-result.json). The [retry launcher](install-cli-coordinator-evidence/retry-r1-smoke.py) ran outside the sandbox in a new session, with stdin DEVNULL, project Python 3.13, UV_OFFLINE=1 and PYTHONUNBUFFERED=1, removing PYTEST_ADDOPTS, BASH_ENV, ENV and REMOTE_ENV_DIR. No cases were deselected. The required static checks and full pytest suite passed. The recorded before/after hashes both equal the final 13-file R1 manifest.

Before that retry, the bounded read-only Atuin diagnostic passed **6 cases** (approximately 12 seconds); preserve its [raw log](install-cli-coordinator-evidence/r1-atuin-diagnostic.log), [command/result metadata](install-cli-coordinator-evidence/r1-atuin-diagnostic-result.json) and [launcher](install-cli-coordinator-evidence/diagnose-atuin-start.py). This diagnostic and the subsequent full pass do not establish the precise cause of the earlier hang. The earlier supervisor used Python 3.15, whereas the retry used project Python 3.13 with DEVNULL/unbuffered settings. These are launcher differences, not a demonstrated single cause, and no Atuin/runtime/test/fixture change was made.

The earlier 1200-second R1 timeout remains a failed/incomplete verification attempt in its original log and timeout JSON. The R0 smoke's 4 failures, all preliminary focused failures, and their snapshots/logs are likewise preserved; the new passing run does not relabel or overwrite them.

For this record-only finalization, the implementer verified **13/13 final source hashes**, **178/178 protected hashes**, the accepted original plan, its original plan audit, the failure-propagation addendum and the R1 repair-plan hashes. The preserved R0 audit also still matches the coordinator's pre-R1 fingerprint and saved snapshot. Proof inputs are [final source manifest](install-cli-implementation-evidence/r1/final/source-hashes.json), [protected manifest](install-cli-planning-evidence/protected-before-implementation.json), [process record](install-cli-process-record.md), [pre-R1 checkpoint](install-cli-coordinator-evidence/pre-r1-checkpoint.json) and the retry result's matching before/after source maps. No source edit or additional test run was performed by the implementer.

**The complete verification gate now has a passing R1 result. Final implementation acceptance remains pending the fresh independent R1 audit verdict.** The implementation record is ready for that audit; it does not substitute for the auditor's acceptance.
