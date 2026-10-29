# Explicit shell command implementation record

Date: 2026-10-29
Status: implementation and full verification complete; independent implementation audit R0 ACCEPTED.

Authorization: user approved the R0 accepted plan with “Implementuj”. Plan SHA-256
`cf52fce5f2e665c04316d08c9f7f112a40a30733fb62de43f30101f1da1e1124`;
plan audit SHA-256
`edd51255423e71f8ce15bd46078262db2cf706253da40e2b69ceeeae8d9d0c5b`.

The baseline is the current worktree, including accepted installed-CLI and
unrelated welcome work. All 277 preplanning fingerprints matched before edits.
The implementation evidence directory contains baseline copies of the 13
existing owned files, the inherited dirty diff and a 574-file baseline manifest.
Two new owned files bring the final source scope to 15 files. Existing process,
plans, audits and evidence are preserved.

Actual available interpreters: Bash 3.2.57 (`/bin/bash`), Bash 5.3.20
(`/opt/homebrew/bin/bash`), Zsh 5.9 (`/bin/zsh`). Raw versions are recorded in
`shell-command-implementation-evidence/interpreters.json`.

Runtime follows the accepted contract: argument parsing before validation,
regular/readable effective rcfile, external PATH Bash through `type -P`, and
`exec` with exactly `--rcfile`, rcfile, `-i`. The parent shell, cwd, native exit
and signal behavior remain owned by Bash. Help never activates the environment.

Guide and footer use separate shell-safe full paths to checkout/installed CLI;
the guide retains its manual fallback and unchanged SSH/VS Code/Git templates.

Verification results will be appended before independent implementation audit.

## Development verification and scope clarification

First sandbox focused run: **175 passed, 10 failed, 91 seconds**, exit 1.
See `focused-first.log` and `focused-first-result.json`. Eight PTY failures
include forbidden `/bin/ps` in cleanup; some parent/nested assertions also
exposed the harness matching echoed input as readiness. The final harness
splits the marker into two input arguments, waits for the executed full marker
and then the next prompt, and always reaps the parent/closes descriptors even
if inventory fails. It verifies process inventory before creating a PTY child;
normal cleanup kills deepest descendants first across job-control groups.
The coordinator's external process check found no surviving task-owned shells.

The other two failures were a pre-existing installed-override test's lexical
expectation of the removed manual footer. The coordinator explicitly approved
a minimal scope addendum on 2026-10-29: adapt this assertion in
`test_install_respects_effective_checkout_override` to exact command arguments
and executing the new footer command, checking effective override and link.
This is the only addition beyond the plan's `footer_commands` extraction hunk
in `test_install_cli.py`.

Initial development lint failed on new test quoting/import order; the raw
failure is retained as `development-lint-first.log` with exit metadata. Those
errors were corrected before focused execution. Final relevant Ruff formatting,
Ruff lint, ShellCheck, Bash syntax and `git diff --check` all passed; raw commands
and statuses are in `static-final.*` and `static-syntax-additional.json`.
(The multi-file Bash syntax invocation parses its first file; the additional
record checks the remaining files individually under each real Bash.)

The stable 15-file candidate is fingerprinted in `candidate-before-focused.json`;
its feature-only diff is `candidate-before-focused.diff`, against baseline
copies rather than HEAD. Ready for the coordinator's outside-sandbox focused
run through the project Python 3.13 runtime. No full smoke has yet been run.

First outside-sandbox focused run: **179 passed, 6 failed, 107.54 seconds**.
Raw evidence belongs to the coordinator: `shell-command-coordinator-evidence/focused.log`
and `focused-result.json`. Two Zsh cases matched literal LEAKED diagnostics in
echoed input; two Bash cases completed activation/nested/parent-return checks
but timed out in the redundant final parent wait, then cleanup reported group
signal permissions. Two forced-cleanup cases also timed out reaping the direct
parent after using an assumed PID-equals-PGID group signal. The coordinator's
supervisor recorded unchanged hashes and zero surviving tracked processes.

The minimal final harness correction composes the full LEAKED diagnostic from
separate arguments and asserts the full marker. Cleanup retains deepest-first
individual descendant termination across process groups, then uses direct
Popen terminate/kill/wait for the direct child, without assuming its process
group. The final parent exit is still sent; its bounded wait/reap now belongs
to this same finally cleanup rather than an earlier duplicate wait.
No runtime change or new test case was added in response to these failures.

Ruff format/lint and diff checks passed after this correction (raw
`static-harness-final.*`). Final 15 source fingerprints and baseline-relative
feature diff are `final-source-hashes.json` and `final-source.diff`. Candidate
is frozen for the coordinator's `focused-rerun` and required full smoke.

Outside `focused-rerun`: **179 passed, 6 failed, 107.79 seconds**, exit 1.
All activation, parent-return, nesting and echo assertions now completed; the
six failures were direct-parent reap timeouts, including a second wait after
SIGKILL. Raw log/result remain under the coordinator evidence directory.

Read-only comparison with the existing `dev/tests/pty_shell.py` identified its
explicit macOS terminal teardown precaution: close the PTY master before
waiting for the killed child. The new local harness had kept the master open
until after wait. The final minimal correction closes the master after
inventory/deepest-descendant cleanup and before direct-parent terminate/kill/wait,
with a flag preventing double close and preserving a defensive finally path.
Runtime code is unchanged. A bounded diagnostic script was prepared as evidence
but has not been executed by the implementer.

Ruff formatting/lint and diff check passed after this correction; raw records:
`static-master-close-final.*`. The latest frozen 15-file candidate is
`final-master-close-source-hashes.json`, with the feature-only baseline diff in
`final-master-close-source.diff`. Earlier candidates and unsuccessful evidence
remain retained. Await outside focused verification and the full smoke gate.

## Historical coordinator interruption

The coordinator agent temporarily became unavailable with `Selected model is at capacity`.
At that checkpoint the implementer had not run the final outside focused retry or full smoke,
because these gates were explicitly assigned to the coordinator after the
sandbox limitation. The latest candidate contains the master-before-wait fix,
with static checks passing; earlier focused failures are not presented as final
verification. The independent implementation audit has not started.

`pending-coordinator-checkpoint.json` records all 264 protected inputs unchanged
and all 15 source fingerprints equal to the latest frozen candidate. Remaining
work at that checkpoint was the final outside focused check, required unfiltered
`just smoke` through project Python 3.13, result recording here, and a fresh
independent implementation auditor. This interruption has since been resolved. No source edits should be
made while those checks run. No staging, commit, push, live asset test, network
request or real-HOME install was performed by this implementation task.

## Final candidate verification

The coordinator resumed and ran `focused-final` outside the sandbox on the
latest `final-master-close-source-hashes.json` candidate: **185 passed in
73.11 seconds**, exit 0, no timeout. The seven focused modules were unfiltered:
`test_shell_command.py`, `test_entrypoint.py`, `test_install_cli.py`,
`test_post_install.py`, `test_guide.py`, `test_runme.py`, and `test_rc_flow.py`.
This includes the actual Bash 3.2/Bash 5.x and available Zsh cases, controlling
PTY parent/nested return and cleanup, no-TTY/manual equivalence, exec PID/signal,
preflight failures, installed/override paths and pre-install copyable guidance.

Raw log and exact command/result metadata are in
`shell-command-coordinator-evidence/focused-final.log` and
`focused-final-result.json`. The project Python 3.13 supervisor used offline
mode, DEVNULL stdin and a fresh session; it recorded all 15 source and 264
protected fingerprints unchanged, 602 tracked descendants and no survivors.

The required full, unfiltered offline `just smoke` subsequently passed on this
same frozen candidate: **996 passed, 58 skipped in 373.93 seconds**, exit 0,
no timeout. This is the full project gate, including static checks and pytest;
no selectors, additional skip/xfail rules or live asset test were introduced.
Raw log and exact command/result metadata are in
`shell-command-coordinator-evidence/smoke.log` and `smoke-result.json`.

The smoke supervisor used the project Python 3.13 runtime outside the sandbox,
offline mode, DEVNULL stdin and a fresh session. All 15 source and 264 protected
fingerprints remained unchanged; it tracked 2,357 descendants and recorded no
survivors. The final focused and full smoke results verify the latest
`final-master-close-source-hashes.json` candidate, rather than an earlier
unsuccessful candidate or HEAD alone.

Implementation and the required verification gates are complete. The fresh
independent [implementation audit R0](shell-command-implementation-audit.md)
returned **ACCEPTED**, with no findings. Report SHA-256:
`040f14db55ac3cd0989d444bcfa15018bd7a797cab98b5416570a51119fa8485`.
The coordinator's final closure check confirmed all 15 source and 264 protected
fingerprints unchanged, matching plan/audit fingerprints and a passing
`git diff --check`. No source file or test was changed after the successful
focused run or full smoke; this closure update changes only this record.
