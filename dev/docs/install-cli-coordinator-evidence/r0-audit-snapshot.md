# Installed management CLI — independent implementation audit

Date: 2026-10-28  
Round: **R0**  
Verdict: **NOT ACCEPTED**

The candidate implements the intended distribution and activation boundary,
and the reviewed installation paths satisfy the planned ownership and failure
rules. Acceptance is blocked by a confirmed stale guide assertion and the
unsuccessful required complete smoke run. Passing focused tests do not replace
that gate. No additional installer runtime defect was established in this audit.

## Blocking findings

### R0-B1 — the changed guide output breaks an existing required suite case

Location: [`dev/tests/test_guide.py:481`](../tests/test_guide.py:481), interacting
with [`post_install.sh:37`](../../tools/lib/install/post_install.sh:37).

Reproduction against the frozen candidate:

```text
dev/.venv/bin/python -m pytest -q dev/tests/test_guide.py::test_remote_ssh_guide_supports_post_install_section
exit 1: 1 failed in 0.29s
```

The test requires the literal substring `bash --rcfile "<simple path>"`.
The new `%q` renderer produces the equivalent simple argument without quotes,
followed by `-i`, so the assertion fails. The full smoke independently reports
the same failure. [Reproduction and input hashes](install-cli-implementation-audit-evidence/guide-reproduction.json).

Required behavior: retain a meaningful regression check for the rendered
interactive command, its actual rcfile argument and explicit interactive flag,
while accepting shell-safe serialization. The accepted plan does not require
literal double quotes for simple paths. The unusual-path execution checks on
Bash and Zsh must continue to pass. This is a test/output integration finding,
not evidence that `%q` is unsafe. A separate repair planner must authorize the
narrow test-scope adjustment before source/test edits.

### R0-B2 — the complete smoke acceptance gate remains unresolved

[`smoke-final-result.json`](install-cli-implementation-evidence/smoke-final-result.json)
records `just smoke`, `UV_OFFLINE=1`, exit **1**. Its full pytest result is
**4 failed, 924 passed, 58 skipped in 351.19s**. Bash syntax, shellcheck, Ruff
and mypy passed. Besides B1, the preserved failures are:

- `test_tmux.py::test_tmux_checkout_paths_reload_and_confirmed_restart`:
  the temporary socket cannot be created (`Operation not permitted`).
- Both Bash variants of
  `test_welcome_bundled.py::test_bundled_and_external_replay_preserve_text_and_terminal_transport`
  with `controlling_terminal=True`: the PTY output contains only
  `READY-TRANSPORT`, rather than the rendered text plus that marker.

These are verification blockers, not established CLI regressions. The tmux
diagnostic indicates a permission restriction; the welcome failure's cause is
unconfirmed. Tmux files are unchanged against HEAD, and all protected inherited
welcome files retain their pre-implementation hashes. The failing welcome path
depends on terminal transport, including `/dev/tty`, outside this install change.

Required behavior: obtain a successful complete smoke run against the repaired
final candidate with appropriate execution permissions and terminal facilities,
and preserve commands, environment, logs, exit status and matching source hashes.
Do not hide these failures, count them as passes, or change unrelated welcome or
tmux behavior to obtain a green result. If a limitation remains, acceptance must
remain pending and its cause must be reported. The observed four failures are
fully retained in [the R0 smoke log](install-cli-implementation-evidence/smoke-final.log).

## Independence, baseline and scope

I read the repository contract, accepted plan, R0 plan audit, accepted addendum
and its audit, process record, final implementation record and implementation
evidence. The plan fingerprint remains
`503e5fb19da5ff45dc3484cc8562dc8169bb7fb6be24e2c712d4f61b9ee38339`;
the addendum remains
`ceddfb157e3bb6709d08b09b3d01f6eae1d1c205d7f9c3505749e3e6302bd09f`.
HEAD remains `39226a2d9074acf08279e7c3edde6a51cc2a629c`.

I reviewed the final scoped diff against HEAD and the implementation record's
inherited-hunk disposition. Independently reconstructing seven tracked draft
files from HEAD plus the archived inherited patch reproduces their recorded
pre-process hashes. The archived untracked install-CLI test also matches its
baseline hash. [Reconstruction evidence](install-cli-implementation-audit-evidence/inherited-draft-consistency.json).
This supports the recorded reuse/revision decisions instead of treating the
inherited draft as approved work.

All **178** protected files match
`protected-before-implementation.json`. The accepted plan and plan/addendum
audits retain their recorded hashes. No unrelated runtime, welcome, assets,
runme, shared fixture, expected-tools test, prune or uninstall changes were
introduced by this candidate. The added `install_tools` guards are exactly the
addendum's narrow extension. The final diff archived independently by this
audit and the implementer's `candidate-R0.patch` have the same SHA-256:
`c2eec81d46e5c11fec02b3a9b7dad9e4e677c39a84c432231058f57bafae3ef7`.

## Implementation and evidence assessment

| Contract | Independent assessment |
| --- | --- |
| Ownership before side effects | The facade selects/validates tools, then calls preflight before confirmation or publication. Preflight performs no mkdir/chmod/config write. It accepts only an absent destination or a symlink with the literal canonical source target. Files, directories, hard links, broken links, foreign checkouts and equivalent relative/chained/spelling links are preserved. Candidate tests observe source modes, destination inodes, config absence and no network calls; my probe also preserved an existing expected-tools file on collision. |
| Safe publication | After confirmation, publication creates and physically resolves the bin directory, rechecks ownership, prepares the CLI, and calls non-overwriting `ln -s SOURCE BIN_DIR/`. It checks status and final literal target; a failed ln rechecks for a collision diagnostic. Controlled mkdir/ln fixtures test newly occupied files/directories/directory symlinks and assert no nested link, replacement, tools or config. This covers the planned final-entry race, without claiming parent-directory locking. |
| Failure propagation | The facade retains one complete-array `install_tools ... || return 1` call. The addendum guards both its mkdir and each ordered tool attempt. Tests exercise the real facade/batch helper in a conditional context, first/middle tool errors and an invalid prefix, preserving an existing expected-tools sentinel and first successful tool. My independent probes complement them with absent expected-tools for first/middle errors on both Bash versions. No later tools/config/footer follow; the published CLI still executes help. |
| Source and destination paths | Source uses physical absolute checkout bin plus `/remote-ssh`; relative bin overrides are anchored to the caller's PWD and canonicalized after creation. Custom/default/relative/absent destinations and effective-checkout override are exercised. My probe adds a relative bin-directory symlink alias and verifies canonical target/reuse with metacharacter paths. Older destinations remain in place. |
| Thin bootstrap | The dispatcher adds only portable one-link `readlink`, relative-link rebasing, physical directories and a 40-link bound with explicit failure. No rcfile is loaded. Direct, installed, relative/chained, unrelated-CWD, missing/deep-link, override and doctor fallback checks exercise this on Bash 3.2 and 5.x. The depth fixture changes only the initial path expression in a disposable copy to reach the script-level bound beyond kernel traversal limits. |
| Footer and guide | Full-path guide and local activation commands work independently of PATH. `%q` is inserted through a dedicated quoted interactive marker; PATH export keeps literal `$PATH`. Directory-by-directory comparison includes physical aliases and avoids substring matches. Candidate tests and my independent probes execute printed commands in clean Bash and Zsh using paths with spaces, quotes, dollars and shell metacharacters. Other guide templates/order remain in scope only for preservation. B1 concerns an older literal-format assertion. |
| Real installation and fresh shell | The new runme fixture copies the real candidate via a fake Git transport; it does not replace dispatcher or install routing. It uses a pinned managed fixture binary and fail-fast observable network boundaries, then reruns runme to exercise update delegation/idempotence. Separate ordinary shells with/without bin in PATH load no rcfile, assert no environment/prompt/alias/function/helper leakage, run CLI help/guide, and apply only the printed export where appropriate. Startup files are byte-snapshotted. |
| Explicit activation | Footer and rendered-guide commands load the real copied `shell/rc.sh`, then observe real environment markers and `rhelp`. No no-op rcfile is counted as activation evidence. Bash child resolution is explicitly bound through a fixture `bash` symlink to each selected runtime. Optional network/identity hooks are disabled in the temporary environment. |
| Lifecycle and delegation | Runtime runme/update/uninstall/prune code is unchanged. Existing update code starts installation from the refreshed checkout in a new process. Lifecycle tests remove a managed fixture tool and eligible stale release, preserving CLI, checkout, foreign directory and startup files; CLI help still runs. The management command is not added to assets, definitions or expected-tools. |
| Scope and activation boundary | Only management CLI publication is added; existing tool links retain their contract. Checkout helper chmod preparation remains separate. No profile writing, chsh/default-shell change, automatic prompt activation or publication of other checkout helpers is added. AGENTS/install/guide text documents checkout lifetime, collisions, PATH responsibility and deliberate manual removal. |

The prior plan audit's fixture observations were addressed: the runme integration
does not reuse the argument-only dispatcher stub; new subprocesses are bounded
and sanitized; the install fixture contains the real rcfile and tool entrypoint;
one successful absent-bin test exercises the real tool staging pipeline through
only a fixture download boundary. Shared `conftest.py` remains unchanged.

## Executed checks and final fingerprints

- Independently read and assessed runtime/tests/docs and the scoped diff; checked
  unchanged lifecycle/update sources and startup activation files.
- Ran [`audit_probe.py`](install-cli-implementation-audit-evidence/audit_probe.py)
  using disposable checkouts/HOME/XDG, minimal environment and 15-second child
  timeouts. Both **Bash 3.2.57** and **Bash 5.3.20** passed. Printed-command
  execution also used **Zsh 5.9**. No actual network access or real-HOME install
  was performed. [Results and fingerprints](install-cli-implementation-audit-evidence/independent-probes.json).
- Independently reproduced B1 with the single bounded guide test; no full suite
  was run concurrently by this auditor.
- Reviewed the final verbose focused log: **94 passed in 44.70s**, exit 0,
  including distinct interpreter IDs and selected-env-bash binding tests.
- Reviewed final static checks, full smoke exit/log and completed implementation
  record; independently ran `git diff --check`, exit 0.
- Independently confirmed all 12 entries in `final-source-hashes.json` equal
  post-focused, post-smoke and current files. Runtime examples: dispatcher
  `7d50575adc99e0e508bc46b7a0c010c2b453d5c2ac0942218c02e2c2edc70cc4`,
  facade `e48b1da0f9c1cbe0abcd0b4c704a2fdc61ea414d3b110c9579f507dedde888e9`,
  batch helper `4d49d6d1793484fa59a651ab69b9b352fe491a5e285f761c369c70fce97bf623`.
  Tests: install CLI
  `b423dc09c3c8b8c93ced9557ac5d919c1b222d49027fb47be4579ec7cb344c08`,
  post-install
  `cf60a4b1ec3faf03444ca954f9e4adf3c60822e408ea916f8f7c27e34e8772b9`,
  runme `41d68304363d08bb5fa4f713450e23c61553fc850e943a42805b0eefd0b9346a`.
  The full exact manifest is retained in the linked independent results.

## Non-blocking observations and limits

- Publication-race execution evidence uses local macOS/BSD `ln`; no Linux host
  was available. The source avoids GNU-only canonicalization flags, but this
  audit does not claim Linux execution evidence.
- Real Git transport and GitHub assets are deliberately replaced by observable
  local boundaries. This is sufficient for routing/publication/failure contracts;
  it is not a live release-asset validation. No live asset check was requested.
- The batch error tests preserve completed tools rather than introducing a
  transaction, as required. Parent-directory replacement races remain outside
  the accepted guarantee.
- The three unrelated smoke failures remain unresolved verification evidence;
  their cause must not be inferred solely from file preservation or focused
  passes. They do not authorize unrelated source repairs.

I modified only this report and its dedicated audit-evidence directory. No
implementation source, implementation tests, plans, other audits or
implementation record was edited. No staging, commit, push, live asset check,
real-HOME installation or child-agent delegation occurred. Repairs require the
separate planner before implementation, followed by R1 re-audit; R1–R3 remain
the available repair audit rounds.
