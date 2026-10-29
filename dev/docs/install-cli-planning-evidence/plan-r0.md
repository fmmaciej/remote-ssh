# Installed management CLI implementation plan

Status: proposed for independent plan audit R0; implementation is not approved.

## Purpose and project contract

Make the management command available from an ordinary local or SSH terminal
after installation, without first starting the remote-ssh shell. Install only
`remote-ssh` into `INSTALL_BIN_DIR` (default `$HOME/.local/bin`) as a symlink to
the installing checkout's `bin/remote-ssh`. Starting the complete environment
remains an explicit `bash --rcfile <checkout>/shell/rc.sh -i` operation.

This is a small extension to CLI distribution, rather than automatic shell
activation. Existing tool binaries already use `INSTALL_BIN_DIR`, the main CLI
already owns installation and diagnostics, and shell configuration already
belongs to the explicit rcfile session. Document that extension in `AGENTS.md`.
Do not edit user startup files, change the default shell, activate prompt or
aliases in an ordinary terminal, or expose the other checkout helpers there.
Keep `bin/remote-ssh` a thin bootstrap/dispatcher. Put installation decisions in
`tools/lib/commands/install.sh` and `tools/lib/install/`. Keep runme delegation,
pinned asset selection, confirmations, expected-tools, and tool staging intact.

The link refers to a checkout, not a copied executable or an independent
release. Moving or deleting that checkout can break the link. An update in the
same checkout naturally updates the command. No additional runtime dependency,
network discovery, metadata store, new install option, or new shell command is
needed. `readlink` is already used by the runtime; use its portable one-link
form rather than GNU-only `readlink -f` or `realpath`.

## Evidence and inherited changes

The coordinator owns `dev/docs/install-cli-process-record.md` and
`dev/docs/install-cli-planning-evidence/worktree-before.json`. They record the
starting HEAD, dirty-file inventory, and hashes. Read those before implementation
and preserve them as the pre-process evidence. The current worktree also
contains independent welcome changes; those are outside this change's ownership.

Earlier work already modifies `bin/remote-ssh`, installation helpers, install
documentation, the interactive guide template, and post-install tests, and adds
`dev/tests/test_install_cli.py`. These are unapproved proposals. After the user
approves the audited plan, the implementer must inventory their diffs against
HEAD and the recorded hashes, classify each relevant hunk as reusable, needing
revision, or outside scope, and record that decision. Do not automatically
accept them, replace whole dirty files, or revert unrelated work.

Observed gaps in that proposal to address explicitly:

- Link collision detection currently happens in `install_bin_dir`, after
  `install_tools`; an installation can change tools before rejecting the CLI.
- Post-install output always prints a PATH export, but the guide invocation
  still uses the bare command and can fail when copied by itself.
- The existing test exercises direct install and a relative link, but does not
  run the complete runme-to-real-install-to-fresh-shell path.
- The current symlink bootstrap has no explicit bounded failure policy.

If a relevant file changes during the process, report the changed baseline and
reconcile ownership before continuing. Preserve all unrelated changes.

## Link ownership, collision, and lifecycle decisions

The following rules are deliberate and must be documented and tested.

| Situation at `$INSTALL_BIN_DIR/remote-ssh` | Result |
| --- | --- |
| Absent, including an initially absent bin directory | Create an absolute symlink to the current source. |
| Symlink whose literal target equals this installation's absolute source | Reuse without replacing it. |
| Regular file, directory, or hard link, even with identical contents | Fail and preserve it. |
| Broken symlink or link to any other source | Fail and preserve it. |
| Link to another remote-ssh checkout, even a valid installation | Fail; never automatically switch ownership. |
| Relative, chained, or differently spelled link that resolves to the same source | Treat as a collision; installed-link ownership uses the exact target written by this installer. |

Derive the source using the physical absolute checkout `bin` directory
(`cd ... && pwd -P`) plus `/remote-ssh`, and check that the source exists and
is executable or can receive the existing executable-bit preparation before
publishing. The installed link always has this canonical absolute target.
CLI bootstrap may follow relative/chained links even though install ownership
deliberately accepts only the direct canonical link. Explain this difference
in maintainer-facing tests/comments, without presenting it as a new CLI feature.

Use both `-e` and `-L` when checking a destination so broken symlinks count as
occupied. A collision diagnostic names the destination and expected source,
explains that no replacement was made, and tells the user to inspect/move/remove
the existing entry deliberately, or select a different `INSTALL_BIN_DIR`. Do
not print a destructive cleanup command or invent a force/overwrite option.

An overridden `INSTALL_BIN_DIR` changes only the destination of this install.
Do not search other directories, remove an older link, or migrate links. Keep
relative override support: interpret the destination relative to the install
caller's original working directory and compute an absolute path for checking,
publishing, and printed commands; do not let internal `cd` operations change
its meaning. Keep inherited environment semantics for tool installation and
`REMOTE_ENV_DIR`; do not silently retarget the CLI to an unrelated checkout.
The link source is the effective checkout supplying this install's libraries
and `BIN_DIR`, under the existing explicit override semantics.

The user retains responsibility for placing the selected directory in PATH.
Another earlier PATH entry can still shadow this CLI; do not promise that
adding a link makes bare-command resolution succeed in every shell.

`uninstall` continues to manage tool definitions and their ownership records.
It leaves the management symlink, checkout, and SSH/Git configuration in place.
`prune`, including `--apply`, keeps its current conservative release-directory
contract and does not remove or treat this link as an installed tool. Do not
add `remote-ssh` to the tool definitions, expected-tools, or asset manifests.
Document that full manual removal includes inspecting the management symlink
and removing it only when it still belongs to the checkout being removed.

## Installation ordering and failure behavior

1. Parse options and preserve help/error behavior; load requirements and select
   supported tools using existing semantics. Invalid input must not create a
   management link or new user configuration.
2. Compute and inspect the intended source/destination without installing tools.
   Reject an existing collision before confirmation and before `install_tools`,
   expected-tools writes, shell preparation, or other install mutations.
3. Show the existing selected-tool summary and obtain the existing confirmation.
   A rejected confirmation leaves the CLI and configuration unchanged.
4. Prepare the destination directory after confirmation, then recheck ownership
   and publish/reuse the CLI before beginning tool installation. Use a
   non-overwriting symlink creation operation; never use `ln -sf` or remove a
   conflicting destination. Pass the containing bin directory as the directory
   operand (`ln -s "$command_source" "$destination_bin_dir/"`), relying on the
   fixed source basename `remote-ssh`, rather than passing the final command
   path as an operand that could become a directory. Thus a newly occupied
   `remote-ssh` entry fails instead of receiving a nested link. Check the
   creation result and resulting exact target. On failure, return nonzero
   before tools.
5. Install selected tools and finish the existing environment/expected-tools
   flow. Preserve failure reporting and emit no success hint if the overall
   install fails. A CLI link published before a later tool failure remains
   available for diagnosis/retry; no rollback removes a pre-existing working
   link. Do not expand this task into a transaction for all selected tools.

Use a small named preflight/publication helper in `dirs.sh`, with explicit
error propagation from the command facade. Preserve existing executable-bit
preparation for checkout helpers; publishing only the main CLI is a separate
responsibility. Do not rely solely on `set -e` for function error propagation.

The directory-race requirement is limited to a final `remote-ssh` entry that
becomes occupied. It does not require defending concurrent replacement of
parent directories or a general filesystem locking system. Prove the directory
operand technique with the targeted test on the supported local platforms.

## Bootstrap and user guidance

The management CLI must locate its actual checkout when executed directly,
through the installed absolute link, or through relative/chained symlinks.
Resolve relative targets against each link's directory. Use quoted paths,
`pwd -P`, portable `readlink`, and Bash 3.2-compatible constructs. Bound link
traversal (for example, 40 links) and fail clearly on unresolved paths or excess
depth; do not hang. Preserve the existing `REMOTE_ENV_DIR` handling and doctor
fallback. Do not load `shell/rc.sh` from the management CLI.

Keep the successful post-install footer short: an installed CLI location, a
working full-path guide command, and a working full-path local-session command.
Use the actual effective checkout, not the default runme location. Quote shell
arguments safely for copy/paste into Bash and Zsh, including spaces, single
quotes, dollar signs, and shell metacharacters. Never expand the user's PATH
into the printed export; leave its reference literal.

Print a PATH instruction only if the effective bin directory is absent from
the install process's PATH (compare entries as directories, not substrings;
recognize an existing directory alias where practical). It states that a new
terminal needs that directory configured too and that the installer does not
modify startup files. This inspection is a hint about the current environment,
not a claim about future login-shell profiles. The guide command must work even
when this hint is ignored. Detailed startup-file examples, local versus SSH
usage, collision/reinstallation behavior, and manual removal belong in
`docs/install.md` and `remote-ssh guide post-install`.

Keep the guide's interactive command safe for unusual checkout paths too.
Extend the renderer/template with a dedicated already-quoted interactive
command placeholder if necessary; do not interpolate an unescaped raw path
inside double quotes and call it shell-safe. Preserve the other guide sections
and their ordering. Do not broaden this change into rewriting SSH/VS Code/Git
template formats.

## File ownership and scope

The implementer owns only these changes, accommodating pre-existing hunks:

| File | Planned responsibility |
| --- | --- |
| `AGENTS.md` | Record external availability of only the management CLI, explicit environment activation, and preserved startup files. |
| `bin/remote-ssh` | Minimal portable symlink-aware bootstrap and bounded error handling. |
| `tools/lib/commands/install.sh` | Call preflight before mutation and publication before tool installation; propagate errors. |
| `tools/lib/install/dirs.sh` | Source/destination calculation, ownership check, safe publication/reuse; retain helper preparation. |
| `tools/lib/install/post_install.sh` | Short PATH-independent footer, conditional PATH hint, safe interactive-command rendering. |
| `docs/post-install.d/00-interactive.in` | Local/SSH activation boundary and safe generated interactive command. |
| `docs/install.md` | Installation/activation distinction, PATH, custom destination, collisions, checkout lifetime, and CLI retention/removal. |
| `dev/tests/test_install_cli.py` | Direct-install ownership, bootstrap, failure ordering, path and lifecycle integration tests. |
| `dev/tests/test_post_install.py` | Footer and guide rendering assertions, PATH cases, executable printed commands. |
| `dev/tests/test_runme.py` | Add real-install integration behind runme while preserving existing delegation tests. |

Use existing `conftest.py` fixtures directly. A small test-only fixture extension
there is allowed only if the complete runme integration cannot reasonably stay
local to its test module; record the reason. Do not change runtime `runme.sh`,
tool definitions, assets, shell hooks, welcome implementation, prune, or
uninstall merely to accommodate this feature. Existing lifecycle behavior is
verified by new integration assertions. No README expansion is needed.

The coordinator owns the plan, audit, and implementation-record artifacts as
process evidence. Any need to expand runtime scope goes back to the coordinator
and plan audit rather than becoming an incidental implementation change.

## Verification plan

All tests run in temporary copied checkouts with temporary `HOME`, XDG config
and state paths, selected tool directories, and controlled PATH. Clear inherited
`REMOTE_ENV_DIR`, `BASH_ENV`, `ENV`, and other shell startup injection variables
unless a test deliberately supplies them. Never install into the real HOME,
modify actual startup files, contact GitHub, or run live asset checks.

Use the existing `runtime_bash` parametrization and explicitly bind child
`/usr/bin/env bash` resolution to that interpreter. Record version output and
exercise Bash 3.2 and Bash 5.x; do not silently count two paths to the same
interpreter as cross-version evidence. Where available, run printed commands
in fresh Zsh (`-f`) too. Do not rely on the installer's environment being
modified for the subsequent fresh shell.

Required focused cases:

1. Direct installation creates only `remote-ssh` from the checkout's helpers,
   with an exact absolute target. Test default and custom destination, relative
   destination, space/metacharacter paths, and an absent destination directory.
2. Reinstallation reuses the same direct canonical link; changing destination
   creates a new link and preserves the original. Another checkout at the same
   destination fails. Regular files, directories, hard links, broken links,
   relative equivalents, and indirect equivalents are preserved as collisions.
3. Collision failure occurs before any tool installer/download marker,
   expected-tools write, or checkout preparation. Existing selected-tool
   failure and confirmation semantics remain intact. Test a destination that
   becomes occupied before publication with controlled fixtures; assert no
   overwrite or nested symlink. A tool failure after publication leaves the CLI
   usable but emits no completion footer.
4. Run real CLI help and guide through the installed link and relative/chained
   links from an unrelated working directory. Test depth failure without a
   hang, direct invocation, `REMOTE_ENV_DIR`, and doctor fallback regression.
5. With and without the effective bin directory in PATH, execute the footer's
   guide and local-shell commands. Verify conditional PATH instructions, safe
   quoting, literal PATH, short output, guide order, and no unresolved markers.
   Only copy the printed export into the test shell when testing that action.
6. Complete runme integration: give a fake `git clone` a local candidate tree
   to copy into the temporary `$HOME/.local/share/remote-ssh`, with a fake `.git`
   marker for later update tests. Run the real `runme.sh`, real dispatcher, and
   real install facade with `--yes demo`. Use a tiny fixture definition and
   preinstalled managed pinned demo binary (plus fail-fast network stubs), so
   no install download is needed. Stub only Git transport and asset/network
   boundaries, not install or CLI routing. Re-run runme against the same fixture
   with fake successful update operations to verify idempotence/delegation.
7. After runme exits, start a separate clean Bash process without rc loading.
   In the PATH-present case, `command -v remote-ssh`, help, and guide must work;
   in the PATH-absent case, bare command lookup fails as expected, full-path
   guide still works, and applying the printed export makes lookup work. Use
   the actual footer path; do not preload checkout `bin` or `shell/rc.sh`.
   Assert no prompt, alias, environment marker, or helper leaked into this
   ordinary shell, and snapshot temporary startup files before/after.
8. After a successful fixture install, uninstall a managed tool and then run
   prune dry-run/apply against eligible fixture releases. The CLI link,
   checkout, foreign paths, and user startup files survive; the CLI still runs.

Keep fixtures meaningful: tool/network stubs record calls, and tests assert the
absence of calls rather than merely checking an exit status. Preserve existing
runme argument/selector tests and uninstall/prune ownership tests.

After focused tests pass, run `just smoke` once against the final candidate.
Its pytest suite is required in addition to syntax, shellcheck, ruff, and mypy.
Record command, interpreter versions, exit status, and output summaries in the
implementation record. Run additional checks only for a failure or unresolved
concern. A blocked dependency/cache download is a reported verification limit,
not a passing smoke result. Never run `just test-assets-live` for this task.

## Acceptance criteria and agent workflow

Accept the implementation only when the documented link policy matches tested
behavior, early collisions change no install state, runme delegates to real
installation successfully, and a fresh ordinary shell with configured PATH can
run the CLI without rcfile activation. All printed recovery commands work
without PATH, explicit environment activation still works, only the management
CLI is newly exposed, lifecycle operations preserve it, both Bash versions pass
the focused cases, and `just smoke` passes. Review the final scoped diff against
the recorded baseline, including preserved unrelated hunks.

The separate planner produces this document only. A fresh independent plan
auditor reviews R0 against source, scope, contracts, and testability and records
findings separately. If needed, the planner revises it and a separate fresh
auditor rechecks R1, R2, then R3 at most. An unresolved R3 goes to the coordinator
and user; no R4 and no implementation begins. Plan acceptance is not permission
to implement: present the audited concrete plan for explicit user approval.

After that approval, use a fresh implementer and then a fresh independent
implementation auditor. For findings, a separate repair planner writes the
concrete repair plan before an implementer edits code. Re-audit each repair at
R1 through R3 at most, stopping to report unresolved R3 findings. Record plan
acceptance, user approval, implementation evidence, and independent implementation
acceptance separately. This workflow authorizes no staging, commit, push,
publication, live asset testing, or installation in the real user HOME.
