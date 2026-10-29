# Explicit shell command — independent plan audit

Date: 2026-10-29  
Round: **R0**  
Verdict: **ACCEPTED**  
Blocking findings: **none**

The plan is concrete, implementable and consistent with the requested explicit
`remote-ssh shell` interface. Acceptance applies to the plan only. Implementation
still requires explicit user approval, a fresh implementer and a fresh
independent implementation auditor.

## Audited inputs and independence

- Plan: [`shell-command-implementation-plan.md`](shell-command-implementation-plan.md).
  SHA-256: `cf52fce5f2e665c04316d08c9f7f112a40a30733fb62de43f30101f1da1e1124`.
- Current `AGENTS.md`, the coordinator's process record and the preplanning
  manifest. Manifest SHA-256:
  `94805a39c51dc0ef73a98ab60494547447935b6ba96cf16f76421321d79112f0`.
- Current dispatcher, command loader, shell rc/environment, guide helpers,
  post-install renderer/footer and interactive template; affected documentation
  and actual test helpers/assertions; developer smoke recipes and retained
  installed-CLI R1 audit/launcher evidence.

I independently recomputed every entry of
[`worktree-before.json`](shell-command-planning-evidence/worktree-before.json):
**277 entries, zero mismatches**. The accepted installed-CLI work and unrelated
welcome changes are the baseline; comparison against HEAD alone would be
incorrect. Existing plans, reports, source/test changes and evidence were
preserved. I authored only this audit report, without delegation.

## Criteria checked

| Criterion | Assessment |
| --- | --- |
| Explicit activation boundary | Plan lines 25–57 preserve bare CLI/help behavior and define one new interactive Bash session. Argument rejection is explicit, with only sole shell help forms accepted. No pass-through, new configuration, nesting guard or startup/default-shell mutation is introduced. |
| Runtime architecture | Lines 59–101 keep parsing/validation/exec in a new sourced facade, register it in `commands.lib.sh`, and limit the public entrypoint to routing/help. Sourcing the facade must not activate the rcfile. Existing symlink bootstrap, depth bound and doctor behavior remain intact. |
| Effective root and paths | The route passes the already selected `repo_dir`; the shell uses that root rather than PWD or the installed bin directory. Installed links and `REMOTE_ENV_DIR` overrides have required coverage. All executable/rcfile arguments remain separate quoted arguments. |
| Bash/preflight/TTY semantics | Regular/readable rcfile validation, PATH executable lookup through builtin `type -P bash`, defined missing-Bash status 127, argument parsing before preflight and native exec failure behavior are specified. The plan distinguishes the existing env-shebang prerequisite from the child-Bash diagnostic. No TTY restriction is added. |
| Cwd, exit and signals | Exec replaces the CLI process; the caller remains the parent. Required real-shell/PTY cases observe cwd, interactive mode, exit 0/23, unchanged parent state, nested return and Ctrl-C usability. PID/signal evidence checks the absence of a supervising runtime wrapper. |
| Installation guidance | The successful footer uses the actual full installed CLI path plus `shell`, retaining full-path guide/PATH hints and short output. The guide uses a separate quoted checkout-command marker while retaining the manual fallback. SSH, VS Code and Git template formats stay outside the rewrite. |
| Actual test dependencies | `test_install_cli.footer_commands` currently extracts `bash --rcfile` and retains a three-value interface. `test_post_install` currently appends `-c` to printed launches. `test_guide` captures exact NUL-separated manual arguments. Lines 167–183 explicitly cover all three dependencies without weakening the semantic fallback assertion. `test_runme` ignores the start value, so retaining its file unchanged is feasible. |
| Isolation and meaningful behavior | Lines 185–264 require copied runtime trees, temporary HOME/XDG state/cache, inherited-environment cleanup, observable offline transport boundaries, real Bash activation, actual helper markers, both Bash versions and available Zsh. Capture executables are limited to routing assertions; they do not substitute for the real activation/PTY cases. |
| Verification and evidence | Lines 266–302 require focused checks followed by final full unfiltered `just smoke`, frozen candidate/protected hashes, raw logs and separately retained unsuccessful attempts. The project uv Python supervisor, fresh session, controlled stdin, finite deadlines and cleanup requirements reflect the retained R1 execution evidence. No earlier smoke pass is presented as verification of the proposed feature. |
| Authorization and scope | Lines 130–165 bound source/test/documentation ownership and protect existing work. Lines 312–322 separate plan acceptance, user approval and implementation acceptance, with independent R0/R1–R3 review and no automatic implementation, commit, push or real-HOME installation. |

The guide's full-path command is feasible without changing its root helper.
`tools/lib/commands/guide/common.sh:13` already computes the root using
`cd "${REMOTE_ENV_DIR:-$REPO_DIR}" && pwd`; `sections.sh:194` passes that result
to the renderer inside command substitution. Consequently a valid relative
`REMOTE_ENV_DIR` produces an absolute renderer argument while preserving the
caller's cwd. This does not require a new bootstrap or override policy.

## Nonblocking observations

1. The future PTY harness must honor the stated no-surviving-shell requirement
   even when interactive job control places descendants in separate process
   groups. A single parent `killpg` is not, by itself, evidence that every nested
   shell has been reaped. This is an implementation/audit detail already bounded
   by lines 154–157 and 260–264; no runtime cleanup feature is called for.
2. Keep the before-install guide case visibly distinct in the eventual evidence:
   run its printed checkout command while no management link exists, including
   an unusual path. The plan already requires before-install guidance and real
   execution of printed commands (lines 119–124 and 250–254); an installed-link
   case alone would not demonstrate that requirement.
3. The existing `runtime_bash` fixture enumerates available paths rather than
   guaranteeing distinct versions. The plan correctly requires recorded real
   Bash 3.2 and 5.x versions and escalation of unavailable required capabilities;
   the implementation audit must assess those records, not parameter count.

These observations do not require a plan revision and are not acceptance
waivers. They identify evidence the later independent implementation audit
must inspect.

## Limits and next gate

This was a read-only source/plan/evidence review plus fingerprint verification.
I did not implement the command, modify source/tests/existing documentation,
execute implementation tests or full smoke, access the network, run live asset
checks, install into the real HOME, stage, commit or push. No runtime behavior
or future test result is certified by this plan verdict.

There are no blocking findings and no R1 plan repair is needed. Present this
exact accepted plan to the user for explicit implementation approval before
assigning a fresh implementer.
