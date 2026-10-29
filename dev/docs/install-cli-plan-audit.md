# Installed management CLI — independent plan audit

Date: 2026-10-28  
Round: **R0**  
Verdict: **ACCEPTED**  
Blocking findings: **none**

This accepts the implementation plan for presentation to the user. It does not
approve the inherited draft implementation, authorize implementation, or certify
that the planned tests already pass.

## Audited material and independence

- Plan: [`install-cli-implementation-plan.md`](install-cli-implementation-plan.md),
  SHA-256 `503e5fb19da5ff45dc3484cc8562dc8169bb7fb6be24e2c712d4f61b9ee38339`.
- Process and baseline: [`install-cli-process-record.md`](install-cli-process-record.md)
  and [`worktree-before.json`](install-cli-planning-evidence/worktree-before.json).
- Repository contract: [`AGENTS.md`](../../AGENTS.md), plus the original
  `README.md`, `docs/install.md`, `docs/shell/start.md`, and `shell/env.sh` read
  from HEAD `39226a2d9074acf08279e7c3edde6a51cc2a629c`.
- The coordinator supplied the user's earlier function contract: publish only
  the management command through the selected bin directory; retain explicit
  rcfile activation for the environment and other helpers; do not edit startup
  profiles or change the default shell; retain runme delegation.
- Independently inspected the current dispatcher, install facade/helpers,
  post-install renderer/templates, shell entry files, guide, update, uninstall,
  prune, test fixtures, relevant subprocess tests, and smoke recipes. The
  inherited draft diffs were inspected as proposals, not accepted evidence.

All source fingerprints recorded in `worktree-before.json` still matched when
checked during this audit. The audit modified only this report.

## Checked criteria

| Criterion | Assessment and evidence |
| --- | --- |
| Activation boundary and project direction | The plan's lines 7–28 publish only `remote-ssh`, preserve explicit `bash --rcfile ... -i`, forbid profile/default-shell changes, and keep the dispatcher thin. This extends the original arrangement in `HEAD:shell/env.sh`, which adds checkout `bin` only inside the rcfile environment. “Only” concerns checkout helpers; existing pinned tool links remain part of installation. |
| Delegation and scope | Lines 19–21 and 195–204 preserve runme and existing install semantics. [`runme.sh`](../../runme.sh) ends by changing into the checkout and invoking the real `./bin/remote-ssh install`. Welcome changes are explicitly outside ownership; inherited draft hunks require a separate recorded disposition. |
| Early collision handling | Lines 108–142 require preflight before confirmation, tool installation, expected-tools writes, and preparation mutations, then a recheck and non-overwriting publication before tools. This directly corrects the inherited draft's late check after `install_tools` in [`install.sh`](../../tools/lib/commands/install.sh). Failure is explicitly propagated rather than relying solely on `set -e`. |
| Ownership, repeat installs, migration | Lines 63–94 specify exact canonical direct-link ownership, preservation of files/directories/hard links/broken links, rejection of other checkouts and relative/indirect equivalents, and preservation of older destinations when `INSTALL_BIN_DIR` changes. The initially absent link case also supports existing tool installations acquiring the CLI on their next successful install. No automatic adoption, overwrite, or link migration is required. |
| Paths and source selection | Lines 72–94 require a physical absolute source, original install-call working-directory semantics for relative destinations, and preservation of effective-checkout/`REMOTE_ENV_DIR` behavior. The proposed files can implement this without changing tool asset selection or adding a runtime dependency. |
| Safe publication | Lines 118–142 use the containing directory operand with the fixed source basename, check both status and resulting target, and explicitly bound the concurrency guarantee. A temporary local experiment with macOS `/bin/ln` returned exit 1 for an existing file, directory, broken link, and symlink to a directory; it preserved each entry and created no nested `remote-ssh` link. No broader parent-directory race guarantee is claimed. |
| Bootstrap portability | Lines 144–152 require relative/chained-link resolution relative to each link, quoted paths, portable one-link `readlink`, `pwd -P`, bounded traversal, and explicit failures while retaining override/doctor behavior. Bash 3.2 and 5.x are available locally, so the required cross-version tests are feasible. |
| Executable guidance and quoting | Lines 154–176 require full-path guide and session commands independently of PATH, conditional directory-aware PATH hints, literal `$PATH`, and executable Bash/Zsh quoting cases. The dedicated quoted interactive-command placeholder avoids the current template's raw path embedded in double quotes. Other guide formats remain outside scope. |
| Lifecycle | Lines 100–106 preserve management-link retention on uninstall and conservative release-only prune. The existing implementations enumerate tool definitions/managed releases rather than treating the CLI as a definition. Same-checkout updates retain the link target, and [`update.sh`](../../tools/lib/commands/update.sh) already starts installation from the refreshed checkout in a new process. No change to destructive update policy is implied. |
| Offline end-to-end evidence | Lines 208–264 require temporary HOME/XDG/checkouts, interpreter-bound children, network call markers, real runme/dispatcher/install routing, and separate ordinary shells with PATH present/absent. A local fake clone copying the candidate plus a pinned preinstalled fixture tool can exercise this without downloads. Tests also cover collisions before mutations, later tool failure, ownership, footer commands, and lifecycle retention. |
| Completion gate and authorization | Lines 266–297 require the final focused tests under both Bash versions and `just smoke`, reject blocked checks as passes, forbid live assets/real-HOME installs, and separate plan acceptance from explicit user implementation approval. [`dev/justfile`](../justfile) runs both `./smoke.sh` and pytest under its `smoke` recipe, matching the proposed gate. |

## Non-blocking implementation observations

1. The existing runme fixtures are deliberately insufficient for the new
   integration: [`prepare_runme_checkout`](../tests/conftest.py) writes an
   argument-recording CLI stub, and `write_fake_runme_git` has no clone branch.
   They remain useful for delegation tests. The new local fixture described in
   plan lines 243–250 must copy the real candidate and implement clone/update
   transport behavior; reusing those fixtures unchanged would not constitute
   the planned end-to-end evidence.
2. [`run_cmd`](../tests/conftest.py) has no subprocess timeout, and
   `isolated_env` copies the parent environment before replacing HOME/XDG/PATH.
   The plan already requires no hanging depth test and clearing startup
   injection/override variables. The new tests can satisfy both locally with a
   bounded subprocess call and a sanitized environment, without expanding
   shared-fixture scope. Existing facade tests also stub `install_bin_dir`;
   they cannot substitute for real publication tests after helpers are split.
3. The inherited [`test_install_cli.py`](../tests/test_install_cli.py) replaces
   `shell/rc.sh` with a no-op and lacks the tool installer entrypoint in its
   copied tree. It can support selected bootstrap assertions, but should not be
   counted as evidence for real rcfile activation or an actual tool-failure
   path. The new candidate fixture and failure cases required by the plan must
   supply the relevant real files or deliberate observable boundaries.

These observations identify fixture constraints, not missing implementation
deliverables at the planning stage. No plan revision is required for R0.

## Limits

This was a plan and feasibility audit. No implementation changes, installation,
test-suite run, network access, live asset check, staging, commit, or push were
performed. Only the publication primitive was exercised in disposable temporary
directories. The local experiment covers macOS/BSD `ln`; the implementer must
provide the planned targeted evidence on available supported platforms and
record platform limits. Bash version availability was inspected as 3.2.57 and
5.3.20, but the candidate has not been certified under either version by this
audit. Final implementation correctness, printed-command execution, baseline
preservation, and a passing smoke result remain the independent implementation
audit's responsibility after explicit user approval.
