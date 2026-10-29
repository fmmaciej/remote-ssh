# Installed CLI repair plan — R1

Date: 2026-10-28  
Status: concrete repair proposal for coordinator acceptance before implementation.  
Findings: **R0-B1**, the post-install guide assertion, and **R0-B2**, the full
smoke verification gate.

## Basis and unchanged purpose

This repair follows the accepted [implementation plan](install-cli-implementation-plan.md)
(SHA-256 `503e5fb19da5ff45dc3484cc8562dc8169bb7fb6be24e2c712d4f61b9ee38339`),
its accepted [plan audit](install-cli-plan-audit.md), the accepted
[failure-propagation addendum](install-cli-implementation-addendum.md)
(SHA-256 `ceddfb157e3bb6709d08b09b3d01f6eae1d1c205d7f9c3505749e3e6302bd09f`)
and [addendum audit](install-cli-addendum-audit.md). The
[process record](install-cli-process-record.md) records the user's approval;
the [implementation record](install-cli-implementation-record.md) records the
candidate and verification so far. These accepted artifacts remain unchanged.

The user-approved purpose remains publication of only the management CLI,
with explicit rcfile activation of the environment, safe copyable guidance,
and preserved installation, ownership and failure semantics. This repair adds
no runtime behavior, feature, dependency or user configuration change.

## Confirmed finding and source assessment

The independent R0 reproduction was:

```text
dev/.venv/bin/python -m pytest -q dev/tests/test_guide.py::test_remote_ssh_guide_supports_post_install_section
exit 1; 1 failed in 0.29s
```

The assertion at `dev/tests/test_guide.py:481` requires the literal substring
`bash --rcfile "{repo_dir}/shell/rc.sh"`. The renderer now uses Bash `printf %q`
for the dedicated interactive-command marker. For this ordinary checkout path,
it correctly emits an unquoted path. The accepted plan requires a shell-safe
command, including `-i`, rather than a particular quoting style. The guide
facade delegates directly to that renderer.

B1 blocks the required green full smoke. It does not establish a runtime or
quoting-security defect. Existing `test_post_install.py` cases execute the
rendered commands at unusual paths using Bash 3.2, Bash 5.x and available Zsh,
and verify real rcfile activation. Preserve those tests and the formatter.
The completed [R0 implementation audit](install-cli-implementation-audit.md)
returned **NOT ACCEPTED** for B1 and B2. The frozen full `just smoke`, with
`UV_OFFLINE=1`, returned exit 1: **4 failed, 924 passed, 58 skipped in 351.19s**.
Static checks passed. The completed implementation record and
`smoke-final-result.json` retain that unsuccessful result.

## Exact repair scope and change

Extend implementation ownership only to
`dev/tests/test_guide.py::test_remote_ssh_guide_supports_post_install_section`.
Do not edit other cases, shared fixtures, runtime code, templates, accepted
plans/audits or unrelated work. Existing `run_cmd` and `assert_ok` imports
already provide the required test helpers.

Replace only the literal-doublequote assertion with this semantic check:

1. Collect stripped output lines beginning with `bash --rcfile ` and assert
   there is exactly one. This must be the standalone local activation command;
   do not select an SSH or VS Code example or accept an arbitrary path mention.
2. Pass that exact extracted line to a fresh `bash --noprofile --norc -c`
   subprocess using `run_cmd`. Prepend a test-local shell function
   `bash() { printf '%s\0' "$@"; }` so the printed command is parsed by Bash
   and its arguments are captured without launching the real interactive
   shell. Use the isolated test environment, excluding `BASH_ENV` and `ENV`
   for this additional subprocess. Do not interpolate the expected path into
   the shell script and do not use `eval` or reproduce `%q` in the test.
3. Assert subprocess success and exact stdout equality to
   `"--rcfile\0" + str(repo_dir / "shell/rc.sh") + "\0-i\0"`.
   The NUL separators preserve argument boundaries and expose missing,
   split, altered or extra arguments. This accepts equivalent safe shell
   representations while still requiring the exact checkout rcfile and `-i`.
4. Preserve every other existing assertion: successful guide invocation, all
   four section headings, the VS Code default profile, absence of `Commands`,
   and absence of `@INSTALL_DIR@`. Also assert absence of the newly introduced
   `@INTERACTIVE_COMMAND@` marker.

Do not skip, xfail, deselect or catch this failure; do not weaken the expected
path to a substring or remove content assertions. Do not force the runtime
back to raw doublequoted interpolation. The semantic subprocess checks this
section's command contract; the existing unusual-path execution tests remain
the evidence for formatter safety and real environment activation.

## B2: verification environment, without unrelated code changes

Besides B1, the R0 failures were the tmux temporary socket error
(`Operation not permitted`) and both Bash 3.2/5.3 variants of the welcome
terminal-transport case with `controlling_terminal=True`, whose output contained
only `READY-TRANSPORT`. The reviewed tmux sources/tests and inherited welcome
sources/tests retain their recorded hashes. These failures do not establish an
installer regression; the welcome cause remains unconfirmed.

Do not change welcome or tmux runtime, tests, fixtures, timeouts or expectations
under this repair. The coordinator has completed the bounded targeted recheck
outside the sandbox with appropriate permission and `start_new_session=True`,
without an inherited controlling terminal. It ran the exact tmux case and all
four welcome transport variants (both Bash versions, with and without the
controlling PTY): **5 passed in 0.99s**, exit 0. Preserve the raw
[recheck log](install-cli-coordinator-evidence/r0-terminal-recheck.log) and
[command/result record](install-cli-coordinator-evidence/r0-terminal-recheck-result.json).
This demonstrates that B2 can be addressed through the execution environment
without source changes; it does not replace full smoke or establish the precise
cause of the earlier PTY failures. `start_new_session=True` is a verification
launcher setting, not a repository fixture change.

Run the final complete `just smoke` on the frozen R1 candidate outside the
sandbox using the same appropriate permissions and fresh-session setup.
Preserve exact command, environment/interpreter details, permission outcome,
stdout/stderr raw logs, exit status and matching source hashes.
Do not deselect, skip, xfail, suppress or alter
the cases to obtain green output. If PTY behavior still fails outside the
sandbox, report a separate blocker and investigate its source-level cause
read-only; do not expand this repair into welcome/tmux code changes. Acceptance
remains pending until the complete smoke passes, or the unresolved blocker is
reported to the coordinator and user under the existing round limit.

## Verification, freeze and independent acceptance

The implementer must first reconcile this narrow expansion with the coordinator
and the completed R0 audit. Only B1's one-case test edit and B2's verification
procedure are covered here; any additional confirmed finding requires its own
concrete repair decision before implementation.

Preserve R0 source fingerprints, raw failed logs and result records, including
`install-cli-implementation-evidence/final-source-hashes.json`,
`smoke-final.log`, `smoke-final-result.json`, the completed R0 audit and the
auditor's `guide-reproduction.json`. Do not overwrite them with R1 results.
Record the pre-repair hash of `dev/tests/test_guide.py`,
which was outside the original candidate hash list, and the one-case repair
diff. Verify that every previously frozen candidate source still matches and
that unrelated protected work is unchanged. After the edit, freeze a separate
R1 source-hash snapshot including `test_guide.py`; use distinct R1 evidence
filenames and check hashes again after verification.

Required checks on that final R1 candidate, in order:

```text
dev/.venv/bin/python -m pytest -q dev/tests/test_guide.py::test_remote_ssh_guide_supports_post_install_section
dev/.venv/bin/python -m pytest -q dev/tests/test_guide.py dev/tests/test_post_install.py
just smoke
```

Apply the B2 execution requirements to its targeted recheck and the complete
smoke command; the latter remains the unfiltered `just smoke` shown above.
The focused retest must pass, preserve section/marker assertions and exact
argv, and keep the existing unusual-path/real-activation cases green under
the recorded distinct Bash versions and available Zsh. The final full
`just smoke` must pass all static checks and the complete pytest suite against
the unchanged R1 snapshot. Retain command, environment/interpreter details,
exit status, output summary, raw logs and pre/post hashes in separate R1
evidence and the implementer's record. A focused pass or static-only pass
cannot substitute for full smoke.

A fresh independent R1 implementation audit must verify the scope, semantic
strength of the replacement assertion, preserved formatter and other tests,
frozen source hashes, R0 failure retention, B2 execution setup and raw results,
green focused/full results and
preservation of unrelated changes. This document is a repair plan, not a claim
of passing tests or implementation acceptance. Implementation/audit repair
rounds are limited to R1–R3; unresolved R3 findings return to the coordinator
and user, with no R4.

No runtime tests were run to prepare this document. No network, live asset
checks, real-HOME installation, staging, commit, push, publication or additional
agents are authorized by this repair. Only this document was written by the
repair planner.
