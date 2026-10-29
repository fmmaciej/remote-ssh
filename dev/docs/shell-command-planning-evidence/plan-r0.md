# Explicit shell command implementation plan

Date: 2026-10-29  
Status: proposed for independent plan audit R0; implementation is not approved.

## Goal and baseline

Add `remote-ssh shell` as the explicit, convenient way to enter a new
interactive Bash with the effective checkout's `shell/rc.sh`. It works when
called from Bash or Zsh, preserves the caller's current directory, and returns
to the parent shell when the new shell exits. Bare `remote-ssh`, `--help`, and
`help` continue to print concise usage without activating the environment.

The baseline is the current worktree, including the accepted installed-CLI R1
implementation and unrelated welcome changes. HEAD alone
(`39226a2d9074acf08279e7c3edde6a51cc2a629c`) does not contain that baseline.
The coordinator's [process record](shell-command-process-record.md) and
[preplanning manifest](shell-command-planning-evidence/worktree-before.json)
record ownership and the 277 pre-existing inputs. Preserve their contents and
all existing plans, audits, evidence and unrelated hunks. This planner writes
only this new plan. No source, test or existing documentation edit, network
request, installation, staging, commit or implementation test run belongs to
this planning phase.

## Public contract

| Invocation | Result |
| --- | --- |
| `remote-ssh shell` | Replace the CLI process with interactive Bash using the effective checkout's rcfile. |
| `remote-ssh shell -h` or `remote-ssh shell --help` | Print short shell usage to stdout, return 0, do not inspect/load the rcfile or start Bash. |
| Any other shell argument sequence | Print a clear argument error and shell usage to stderr, return 1, do not activate the rcfile. |
| No command, `-h`, `--help`, or `help` | Preserve the existing top-level usage behavior and return status. |

Only a sole `-h` or `--help` is accepted. Reject `help`, `--`, `-c`, `-l`,
`--rcfile`, positional arguments, extra arguments after help, and arbitrary
Bash pass-through. There are no new options, config keys or nesting guards.
The shell usage states `Usage: remote-ssh shell`, describes interactive Bash,
and mentions `exit` to return to the calling shell. It does not imply that
calling the command changes the parent's environment.

The launch is equivalent to the existing manual
`bash --rcfile <effective-checkout>/shell/rc.sh -i`. Do not add a TTY requirement:
piped stdin and redirected output remain valid, with Bash's native interactive
behavior and possible job-control warnings. Do not add `--login`, `--norc`,
`--noprofile`, a working-directory change, runtime environment sanitization,
signal traps, or a supervising wrapper. Use `exec` for the final Bash launch.
Existing runtime hooks and their configuration retain their current behavior.

The CLI is already a separate executable process; `exec` replaces that process,
not the invoking user's parent shell. Normal exit statuses, including `exit 0`
and `exit 23`, pass back unchanged. Bash owns interactive signals and job
control; Ctrl-C at its prompt should leave that shell usable. Do not translate
signals or add cleanup handlers to runtime code. A task-owned subprocess killed
by a signal remains observable with the normal subprocess/shell signal status.
Calling `remote-ssh shell` inside an active remote-ssh session starts another
ordinary nested Bash; exiting returns one level. No special de-duplication or
new inheritance policy is introduced.

## Implementation decisions

1. Add `tools/lib/commands/shell.sh`, following the existing sourced-facade
   convention and Bash 3.2-compatible syntax. Its main function receives the
   effective `repo_dir` as its first internal argument, followed by user
   arguments. Parse user arguments before runtime validation.
2. For an actual launch, form the quoted rcfile path from that effective root.
   Require a regular, readable rcfile (`-f` and `-r`); otherwise print a
   `remote-ssh shell:` diagnostic naming it and return 1. A missing file,
   directory at that path, or unreadable file must not silently start a plain
   Bash. Do not source the file as a preflight or parse/validate its hooks.
3. Resolve an external executable Bash through the current PATH with Bash's
   builtin `type -P bash`, using its result as one quoted executable argument.
   Missing Bash yields a clear `remote-ssh shell:` diagnostic and status 127.
   Do not select `$SHELL`, hardcode `/bin/bash`, use another shell, or require an
   installer-managed Bash. PATH selection matches the external Bash selected
   by the existing manual command and lets the same controlled PATH select
   Bash 3.2 or 5.x; `$BASH` would instead pin the dispatcher's interpreter even
   when the user deliberately selects another Bash in PATH. The CLI's existing
   `#!/usr/bin/env bash` bootstrap
   still requires Bash before any subcommand can run; when that interpreter
   itself cannot start, its existing operating-system/env diagnostic applies.
   Test the facade's missing-child-Bash diagnostic by starting the CLI through
   a known absolute Bash with a controlled PATH that lacks Bash.
4. Execute the resolved binary with exactly `--rcfile`, the rcfile path, and
   `-i`. There is no command string, `eval`, `bash -c`, extra process wrapper,
   or argument interpolation. Preserve native `exec` failure diagnostics/status
   if an executable disappears or becomes unusable after the lookup; a new
   filesystem race guarantee is outside this small feature.
5. Register the facade in `tools/lib/commands.lib.sh`; add one dispatcher case
   passing `"$repo_dir" "$@"` and one concise help entry in `bin/remote-ssh`.
   Add the command to `guide commands`. Merely sourcing the facade must have
   no launch or rcfile side effects.

Retain the installed CLI's existing portable symlink bootstrap, link-depth
bound and doctor fallback byte-for-byte apart from the dispatcher/help hunks.
An invocation through an installed link uses its resolved checkout; an
explicit `REMOTE_ENV_DIR` continues to select the effective checkout supplying
libraries and the shell rcfile. Pass the already-selected root rather than
recomputing a root from PWD, the installed destination, or the shell facade's
own location. An invalid override that prevents existing bootstrap/library
loading retains that bootstrap failure; this command does not add doctor's
fallback to shell. Starting a session never changes installed symlinks.

## Documentation and generated guidance

Make the new command the primary local start instruction. From a checkout use
`./bin/remote-ssh shell`; after installation use `remote-ssh shell` with the
existing PATH instructions. Where PATH independence matters, use a fully
qualified command. Retain the manual `bash --rcfile ... -i` form as a fallback
and reference for launching the same environment, and retain the warning not
to source `shell/rc.sh` from Zsh. Explain cwd preservation and `exit` returning
to the parent, explicit activation, and unchanged startup files/default shell.

The short successful install footer replaces its manual launch line with the
shell-safe, full installed CLI path followed by `shell`, using the actual
`INSTALL_BIN_DIR`. Keep the full-path guide command, conditional PATH hint,
literal `$PATH`, concise output and existing collision/lifetime guidance.
No extra manual fallback line is necessary in this short footer.

The interactive guide uses a new dedicated, already shell-quoted
`@SHELL_COMMAND@` placeholder for `<effective-checkout>/bin/remote-ssh shell`.
This checkout command works before installation and with a custom destination
absent from PATH. Keep `@INTERACTIVE_COMMAND@` and its existing safe manual
fallback rendering. Generate both with quoted arguments using the renderer's
current `%q` approach; validate execution in Bash and Zsh for unusual paths.
Only the renderer and `00-interactive.in` change. Do not rewrite the SSH
`RemoteCommand`, VS Code JSON profile or Git sections, their ordering, or their
existing substitutions. Their manual launch form remains a compatible
reference. Do not suggest sourcing Bash rc code into Zsh.

## Exact source ownership

The later fresh implementer owns the following focused hunks, preserving all
baseline changes in these files:

| File | Responsibility |
| --- | --- |
| `tools/lib/commands/shell.sh` (new) | Argument contract, rcfile/Bash validation and exec launch. |
| `tools/lib/commands.lib.sh` | Register the new facade. |
| `bin/remote-ssh` | Help entry and thin route only. |
| `tools/lib/commands/guide/sections.sh` | Add shell to command listing only. |
| `tools/lib/install/post_install.sh` | New safe guide command substitution and short footer start line. |
| `docs/post-install.d/00-interactive.in` | Primary explicit command plus manual fallback/reference. |
| `docs/shell.md`, `docs/shell/start.md`, `docs/install.md` | Focused local-start and return/cwd explanations. Preserve SSH/VS Code examples. |
| `AGENTS.md` | Add public shell command and update explicit activation wording. |
| `dev/tests/test_shell_command.py` (new) | Isolated command, environment, interpreter and PTY tests; module-local harness/helpers. |
| `dev/tests/test_entrypoint.py` | Shell usage/listing and no-argument/help regression assertions. |
| `dev/tests/test_install_cli.py` | Adapt only `footer_commands` extraction to the new start command, retaining its three-value interface and all install/lifecycle assertions. |
| `dev/tests/test_post_install.py` | New footer/guide command semantics and executable start checks; preserve manual fallback, PATH and guide ordering coverage. |
| `dev/tests/test_guide.py` | New primary start command and marker checks; retain semantic manual-fallback argv assertion. |

`dev/tests/test_runme.py` imports `footer_commands` but ignores its start value;
keep it unchanged and run its existing real-install integration as regression
coverage. `test_rc_flow.py`'s Zsh rejection and rc-hook tests remain unchanged.
Reuse existing fixtures without edits to `conftest.py` or `pty_shell.py`.
The existing `PtyShell` helper assumes a fixed Bash parent/prompt and kills only
its immediate child; use a small module-local bounded harness when the new
nested/parent-shell scenarios require process-group cleanup. No runtime hook,
welcome code, install policy, runme implementation, tool asset/manifest,
uninstall/prune logic, README expansion, dependencies or test-wide refactor is
authorized. A need to expand this scope goes to the coordinator for assessment
and a concrete plan adjustment before edits.

The implementer also owns its new implementation record and dedicated evidence
directory; the coordinator assigns their names. Existing process artifacts stay
immutable. An independent implementation auditor owns a separate report/evidence.

## Test design and concrete affected assertions

The inspected baseline has three dependencies that must be handled together:

- `test_install_cli.footer_commands` currently finds a literal `bash --rcfile`
  start line. Extract the new full-path `... shell` line unambiguously while
  retaining the helper interface used by post-install and runme tests.
- `test_post_install_prints_short_guide_hint` expects the manual footer;
  `test_footer_and_guide_commands_execute_without_path` currently appends `-c`
  to both printed Bash launches. The new command deliberately rejects `-c`.
  Execute the printed shell command unchanged and supply commands via stdin
  or PTY instead. Keep separate manual fallback execution coverage.
- `test_remote_ssh_guide_supports_post_install_section` already captures exact
  NUL-separated manual argv rather than requiring one quoting style. Keep that
  check; add a semantic exact-argv check for the primary command and reject
  unresolved new and old markers. Do not restore lexical quote assumptions or
  compare output to a duplicate implementation of `%q`.

All new tests use temporary copied runtime trees and temporary HOME/XDG config,
state and cache locations. Sanitize inherited `REMOTE_*`, exported Bash
functions, `BASH_ENV`, `ENV`, `SHELLOPTS`, `BASHOPTS`, `CDPATH`, `ZDOTDIR` and
installation/library overrides before supplying deliberate test values. Disable
update checks, welcome, Atuin auto-import and optional external integrations
with their existing toggles; place fail-fast observable network stubs in PATH.
No real HOME installation/configuration, network access or live asset tests.
Do not edit runtime hooks to make isolation work.

Use `runtime_bash` and bind PATH's env-Bash lookup to the selected interpreter.
Record actual version outputs: demonstrate real Bash 3.2 and real Bash 5.x,
and the available Zsh caller (`-f`, isolated HOME/ZDOTDIR). Distinct paths to
one Bash version do not satisfy the version matrix. If an interpreter or PTY
capability is unavailable, report the limitation and obtain valid verification
through the coordinator; do not turn a required case into an unexplained pass.

Required focused cases:

1. **Dispatch and exact argv.** In a disposable complete CLI tree, invoke the
   public dispatcher with a known absolute interpreter and a capture executable
   in PATH's `bash` position. Assert exactly three NUL-separated child arguments
   (`--rcfile`, the effective rcfile, `-i`), unchanged cwd, and child status
   propagation. This isolates routing; real-Bash cases below prove activation.
2. **Help boundary and invalid input.** Bare CLI, top-level help variants, and
   both shell help forms succeed without an rc marker or launch marker. Test
   shell help with absent rcfile/child Bash to prove parsing comes first.
   Negative arguments include all forms in the public contract, including
   extra arguments after help. Assert status 1, diagnostic/usage, and no launch.
3. **Real activation through links.** Use the accepted real-install fixture to
   publish the installed link, then execute it directly from an unrelated cwd
   in a checkout/destination containing spaces, quotes, dollar signs and shell
   metacharacters. Assert interactive `$-`, Bash version, effective
   `REMOTE_ENV_DIR`, checkout bin in PATH, `rhelp` alias and `log` function.
   Check cwd before any child `cd`; test both bare-command PATH availability
   and full-path launch when the install bin is absent from PATH. Preserve the
   link target and inode. Existing bootstrap chain/depth tests remain intact.
4. **Effective override.** Call one checkout's installed link with a valid
   `REMOTE_ENV_DIR` for another copied checkout, using a distinct rc marker.
   The second checkout's rcfile/environment loads, cwd stays unchanged, and the
   installed link is untouched. Unset override derives the original checkout.
5. **No TTY restriction and statuses.** Launch real Bash through the CLI with
   piped stdin containing marker/cwd checks and `exit 23`, with a timeout.
   Assert status 23 and activation; allow native Bash terminal warnings. Also
   check normal `exit 0`. Compare the substantive activation/cwd/status result
   with the manual launch in the same isolated environment. No `-c` pass-through.
6. **PTY entry and parent return.** Start an ordinary Bash parent and, when
   available, Zsh parent in a controlling PTY; capture initial cwd/environment,
   then run the installed full-path command. Establish readiness using an
   executed unique marker rather than input echo or decorative prompt text.
   Verify real interactive Bash, expected rc environment/alias/function and cwd.
   Change cwd/export a child-only marker, exit 23, and assert the parent sees
   status 23, its original cwd/environment and no new alias/function/checkout
   helper exposure. Test a nested shell and one-level return; Ctrl-C at the
   child prompt must leave it able to run another marker command and exit.
7. **Exec and signals.** In a bounded isolated real launch, have the child print
   its PID and wait for input; assert that PID equals the launched CLI process
   PID. Send a deterministic signal such as SIGKILL to that task-owned process,
   reap it, and assert the native subprocess signal result. This verifies no
   supervising wrapper; it does not prescribe new interactive signal policy.
8. **Failures before activation.** Missing rcfile, directory rcfile, unreadable
   regular rcfile and missing PATH Bash produce the defined errors and no rc
   marker. Exercise permissions under an ordinary user; do not fake an
   unreadable-file pass when privileged access defeats chmod. Use a controllable
   facade-level test only as additional evidence, not a substitute for the
   ordinary-user unreadability check.
9. **Copyable guidance and no persistent changes.** Parse both primary printed
   commands as shell syntax with argument capture and assert exactly command
   path plus `shell`; run the unmodified footer and guide commands from fresh
   Bash/Zsh with controlled stdin/PTY. Preserve exact-argv manual fallback
   validation and real fallback activation. Assert template ordering, unresolved
   marker absence, conditional/literal PATH hints, short footer, no network
   calls, and unchanged temporary startup files and expected-tools/installed
   state. A normal session may write only its existing temporary history/state;
   do not claim the child runtime has no normal state effects.

Every subprocess gets a finite timeout. PTY/select loops use monotonic deadlines
and retain captured output on failure. Launch supervisors in a fresh session;
in finally/timeout paths terminate only the task-owned process group, escalate
to KILL after a bounded grace period, reap children and close PTY descriptors.
Do not leave nested shells alive or rely solely on killing the parent PID.
Keep these mechanics local to the tests/evidence rather than expanding runtime.

## Execution order and verification gate

After explicit user approval of the audited concrete plan:

1. Fresh implementer reads the baseline/process record, verifies fingerprints,
   inventories relevant dirty hunks, records interpreter versions and prepares
   isolated tests. It preserves accepted installed-CLI and welcome behavior.
2. Implement the facade, registration and minimal route/help changes; add the
   command tests. Then make the scoped docs/renderer/footer changes and adapt
   all three affected test areas together. No speculative refactor.
3. Run final focused tests for `test_shell_command.py`, `test_entrypoint.py`,
   `test_install_cli.py`, `test_post_install.py`, `test_guide.py`,
   `test_runme.py`, and `test_rc_flow.py`, including the interpreter/PTY matrix.
   Run relevant style/syntax checks and `git diff --check`. Record exact commands,
   versions, exit codes, counts and logs; do not broaden unrelated format hunks.
4. Freeze the candidate manifest and run required, full, unfiltered `just smoke`
   on that candidate, including all static checks and pytest. No selectors,
   added skip/xfail rules, `PYTEST_ADDOPTS` filtering or live asset check.
   Retain source/protected-file fingerprints before and after. A focused pass
   or infrastructure explanation does not replace this gate.
5. Fresh independent implementation auditor checks contracts, scope, complete
   focused/full evidence and preserved baseline. Additional runs address a
   concrete unresolved concern; they do not blindly repeat successful checks.

Previous installed-CLI verification passed full smoke in about 341 seconds.
Its sandbox attempts encountered tmux/PTY restrictions, and one supervisor run
using system Python 3.15 stalled; the exact cause was not established. The
successful retry used the project's uv Python 3.13 runtime outside the sandbox,
fresh session, closed stdin and bounded process-group cleanup. Plan a suitably
bounded full-check supervisor using that established project runtime. If the
sandbox blocks terminal facilities, request the normal execution escalation
through the coordinator; do not modify unrelated tmux/welcome/Atuin sources or
quietly skip tests. Retain each failed start, timeout, partial log and result
separately, verify cleanup and fingerprints, diagnose the specific failure,
then rerun only as justified. No failure may be overwritten by later evidence.

## Acceptance and independent workflow

Accept implementation only when explicit shell entry works from Bash and Zsh,
direct/installed/full-path execution selects the effective checkout, cwd and
parent state are preserved, exit/signal behavior follows the exec contract,
help/no-argument paths never activate rcfile, errors are clear, printed commands
execute safely, all required isolated cases and unfiltered smoke pass, and all
out-of-scope baseline inputs remain unchanged.

The separate planner submits this document only. A fresh independent plan
auditor reviews R0 and records its verdict separately. Revisions, if needed,
receive fresh independent R1 through R3 audits at most. Unresolved R3 findings
go to the coordinator/user; there is no R4 or automatic implementation. An
accepted plan is presented to the user for explicit implementation approval.
Only then assign a fresh implementer, followed by a fresh independent
implementation auditor. Any implementation findings require a separate concrete
repair plan before edits and independent re-audit at R1 through R3 at most.
Record acceptance, user approval and implementation acceptance separately.
This process authorizes no staging, commit, push, publication, live asset test
or installation/configuration in the real HOME.
