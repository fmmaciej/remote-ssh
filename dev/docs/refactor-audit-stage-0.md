# Refactor Audit Stage 0: Map And Criteria

Date: 2026-06-01

This report is a factual map for later refactor review stages. It does not
recommend or apply code changes. The audited inventory covers `bin/`, `lib/`,
`scripts/`, `shell/`, and `tools/`.

## Module Map

The audited scope is about 8,950 lines. The largest implementation clusters are
the shell runtime, the public `remote-ssh` command modules, install tooling, and
standalone helper scripts. `tools/vendors/bash-preexec.sh` is 564 lines of
vendored code and should be reviewed only through its integration boundary.

Public entrypoints and their layers:

| Entrypoint | Layer | Main implementation path |
| --- | --- | --- |
| `bin/remote-ssh` | user-facing CLI | sources `tools/lib/env.sh` and `tools/lib/commands.lib.sh`, then dispatches subcommands |
| `tools/install-tool.sh` | lower-level pinned tool installer CLI | sources `tools/lib/env.sh` and `tools/lib/install-tool.lib.sh` |
| `tools/generate-def.sh` | developer-only tool definition generator | sources `tools/lib/env.sh`, optional `dev/.env`, and `tools/lib/generate-def.lib.sh` |
| `bin/ci-run` | user-facing helper wrapper | execs `scripts/ci_run.sh` |
| `bin/helm-chart-diff` | user-facing helper wrapper | execs `scripts/helm_chart_diff.sh` |
| `shell/rc.sh` | interactive shell bootstrap | sources `shell/env.sh`, `shell/aliases.sh`, `shell/rc.d/*.sh`, OS hooks, and host hooks |
| `shell/rc.d/25-log.sh` | interactive shell helper surface | defines `log` and `logrun` |
| `shell/rc.d/26-bssh.sh` | interactive shell helper surface | defines `bssh` and `bssh-ip` |
| `shell/rc.d/30-ssh-pick.sh` | interactive shell helper surface | defines `ssh-pick`, backed by `scripts/ssh_hosts.py` |

Primary module groups:

- `lib/`: shared shell helpers loaded by both shell runtime and tool CLIs.
- `shell/`: login shell environment, config loading, update checks, welcome
  rendering, aliases, and interactive helpers.
- `tools/lib/commands/`: public `remote-ssh` subcommands and private command
  modules for `git`, `ssh`, `guide`, and `update`.
- `tools/lib/install/` and `tools/lib/install-tool/`: expected-tool selection,
  platform-aware asset selection, download, extraction, and symlink switching.
- `tools/lib/common/`: shared platform, GitHub, requirements, and archive
  helpers for tool code.
- `tools/lib/generate-def/`: developer-only release manifest generation.
- `tools/defs/`: exact pinned release asset manifests; treat these as data for
  later audit stages unless asset contract behavior is under review.
- `scripts/`: standalone helper implementations. They do not source the
  runtime library today.

Largest non-vendored files and function clusters to revisit in later stages:

| File | Lines | Function count | Later stage |
| --- | ---: | ---: | --- |
| `scripts/helm_chart_diff.sh` | 513 | 16 | Stage 4 |
| `tools/lib/commands/uninstall.sh` | 353 | 14 | Stage 2 or 3 |
| `scripts/ci_run.sh` | 333 | 10 | Stage 4 |
| `tools/lib/commands/guide/sections.sh` | 242 | 12 | Stage 2 |
| `tools/lib/commands/update/check.sh` | 238 | 8 | Stage 2 |
| `tools/lib/commands/ssh/status.sh` | 231 | 11 | Stage 2 |
| `shell/welcome/runner.sh` | 201 | 14 | Stage 1 |
| `tools/lib/install-tool/install.sh` | 182 | 8 | Stage 3 |
| `tools/lib/commands/doctor.sh` | 174 | 7 | Stage 2 or 3 |
| `tools/lib/common/github.sh` | 165 | 11 | Stage 4, with generator context |

Relevant existing test surfaces for later stages include `dev/tests/test_rc_flow.py`,
`dev/tests/test_shell_helpers.py`, `dev/tests/test_welcome.py`,
`dev/tests/test_entrypoint.py`, `dev/tests/test_check.py`,
`dev/tests/test_doctor.py`, `dev/tests/test_update.py`,
`dev/tests/test_install_tool_core.py`, `dev/tests/test_install_binary.py`,
`dev/tests/test_prune.py`, `dev/tests/test_uninstall.py`,
`dev/tests/test_ci_run.py`, `dev/tests/test_helm_chart_diff.py`, and
`dev/tests/test_generate_def.py`.

## Source Graph

Shell runtime load graph:

- `shell/rc.sh`
  - sources `shell/env.sh` if present.
  - sources `shell/aliases.sh` if present.
  - uses `remote_source_dir` to source `shell/rc.d/*.sh`.
  - sources `shell/rc.d/os.d/$(remote_os_id).sh` if present.
  - sources `shell/rc.d/host.d/${REMOTE_HOSTNAME}.sh` if present.
- `shell/env.sh`
  - establishes `REMOTE_ENV_DIR`, `REMOTE_BIN_DIR`, `REMOTE_DOTS_DIR`,
    `REMOTE_LIB_DIR`, and `REMOTE_SHELL_DIR`.
  - sources `lib/guards.sh` and `lib/helpers.sh`.
  - sources `shell/config.lib.sh` and calls `remote_ssh_config_load` when the
    config library exists.
  - prepends `$HOME/.local/bin` and repo `bin/` to `PATH`.
- `shell/config.lib.sh`
  - sources `shell/config/entries.sh`, `path.sh`, `parse.sh`, `markers.sh`,
    and `load.sh`.
- `shell/update-check.lib.sh`
  - sources `shell/update-check/toggle.sh`, `state.sh`, and `time.sh`.
- `shell/welcome.lib.sh`
  - sources `shell/update-check.lib.sh`.
  - sources welcome modules: `base.sh`, `toggles.sh`, `issues.sh`,
    `banner.sh`, `host.sh`, `update.sh`, `commands.sh`, `hw.sh`, `sw.sh`, and
    `runner.sh`.
- `shell/welcome.d/*.sh`
  - source `shell/welcome.lib.sh` and run selected welcome sections.
- `shell/rc.d/04-update-check.sh`
  - sources `shell/update-check.lib.sh` for interactive update checks.
- `shell/rc.d/05-bash-preexec.sh`
  - conditionally sources `tools/vendors/bash-preexec.sh` for interactive Bash
    only; the vendored file should not be audited internally.
- `shell/rc.d/08-welcome.sh`
  - sources `shell/welcome.lib.sh`.

CLI/tools load graph:

- `bin/remote-ssh`
  - sources `tools/lib/env.sh`.
  - sources `tools/lib/commands.lib.sh`.
  - dispatches to command facade functions.
- `tools/lib/env.sh`
  - establishes repo and tools directory variables.
  - sources `lib/guards.sh`, `lib/log.sh`, and `lib/helpers.sh`.
  - defines default `INSTALL_PREFIX` and `INSTALL_BIN_DIR` if unset.
- `tools/lib/commands.lib.sh`
  - eagerly sources command facades: `install.sh`, `uninstall.sh`, `tool.sh`,
    `tool_status.sh`, `check.sh`, `ssh.sh`, `update.sh`, `git.sh`,
    `setup.sh`, `doctor.sh`, `prune.sh`, `scripts.sh`, `guide.sh`, and
    `help.sh`.
  - lazily loads `tools/lib/install.lib.sh` and `tools/lib/install-tool.lib.sh`
    through `remote_ssh_cmd_require_install_libs`.
- `tools/lib/install.lib.sh`
  - sources common platform/requirements helpers.
  - sources install defaults, requirements, tool defs/assets, install logic,
    install dirs, and post-install rendering.
- `tools/lib/install-tool.lib.sh`
  - sources common platform/requirements/extract helpers.
  - sources install-tool defs, assets, download, install, and main modules.
- `tools/lib/generate-def.lib.sh`
  - sources common platform and GitHub helpers.
  - sources generator detect, names, assets, checksums, and render modules.
- `tools/lib/status.lib.sh`
  - sources `tools/lib/env.sh`.
  - sources a reduced status surface for login-time welcome checks:
    platform, defs/assets, expected tools, tool inventory, tool sets,
    `tool_status.sh`, and `scripts.sh`.
- `tools/lib/commands/git.sh`
  - sources `git/common.sh`, `git/setup.sh`, and `git/status.sh`.
- `tools/lib/commands/git/status.sh`
  - sources SSH agent status helpers plus Git status model, diagnosis, hints,
    and render modules.
- `tools/lib/commands/ssh.sh`
  - sources SSH common helpers, agent status helpers, setup, and status.
- `tools/lib/commands/update.sh`
  - sources `tools/lib/commands/update/check.sh`.
- `tools/lib/commands/update/check.sh`
  - sources `shell/update-check.lib.sh` to share cache/timing behavior.
- `tools/lib/commands/guide.sh`
  - sources guide common, shell snapshot, tool report, and section modules.
- `tools/lib/commands/guide/sections.sh`
  - sources `shell/config.lib.sh` to report runtime config values.
- `tools/install-tool.sh`
  - sources `tools/lib/env.sh` and `tools/lib/install-tool.lib.sh`.
- `tools/generate-def.sh`
  - sources `tools/lib/env.sh`.
  - optionally sources `dev/.env`.
  - sources `tools/lib/generate-def.lib.sh`.

Helper scripts load graph:

- `bin/ci-run` execs `scripts/ci_run.sh`.
- `bin/helm-chart-diff` execs `scripts/helm_chart_diff.sh`.
- `scripts/ci_run.sh` is self-contained Bash.
- `scripts/helm_chart_diff.sh` is self-contained Bash.
- `scripts/ssh_hosts.py` is self-contained Python and is called by
  `ssh-pick` at function call time.

Dependency map by timing:

- Load-time file dependencies are primarily the source graph above.
- Shell runtime load-time external commands include basic shell builtins and
  small system tools used during initialization, notably `uname`, `hostname`,
  `date`, `mkdir`, and optional `command -v` checks. Interactive feature hooks
  may also call installed tools at load time when present, such as `atuin`,
  `zoxide`, and `starship`.
- CLI load-time external commands are mostly path setup and sourcing. Command
  execution is normally deferred to subcommand functions.
- Call-time core install/check dependencies include `curl`, `grep`, `sed`,
  `find`, `tar`, `uname`, `mktemp`, optional `unzip`, and optional
  `sha256sum` or `shasum`.
- Call-time update and Git/SSH dependencies include `git`, `ssh`, `ssh-add`,
  and `grep`.
- Call-time shell helper dependencies include `fzf`, `navi`, `tspin`, `bssh`,
  `ssh`, `awk`, and `python3` for `scripts/ssh_hosts.py`.
- Call-time developer/helper dependencies include `gh` for `ci-run`, `helm`,
  `diff`, `sort`, `cp`, and optional `curl` for `helm-chart-diff`, and GitHub
  API access via `curl` for `tools/generate-def.sh`.

## Runtime vs Developer Boundary

Minimal runtime:

- `shell/rc.sh`, `shell/env.sh`, `shell/config*`, `shell/aliases.sh`,
  `shell/rc.d/*.sh`, `shell/update-check*`, `shell/welcome*`, and root `lib/`.
- `bin/remote-ssh` and the `tools/lib/commands/` command surface used by
  installed hosts.
- `tools/lib/install/`, `tools/lib/install-tool/`, `tools/lib/common/`, and
  `tools/defs/` for local installs, updates, checks, doctor, and prune flows.

Optional runtime helpers:

- `shell/rc.d/20-fzf.sh`, `21-zoxide.sh`, `21-yazi.sh`, `22-starship.sh`,
  `23-atuin.sh`, `24-navi.sh`, `25-log.sh`, `26-bssh.sh`, and `30-ssh-pick.sh`.
- `ssh-pick` currently depends on `python3` through `scripts/ssh_hosts.py`.
- `tools/vendors/bash-preexec.sh` is optional integration support for Atuin in
  interactive Bash and should remain isolated as vendored code.

User-facing CLI:

- `bin/remote-ssh` is the main command.
- `tools/install-tool.sh` is a lower-level installer entrypoint.
- `bin/ci-run` and `bin/helm-chart-diff` are helper commands exposed through
  repo `bin/`.

Developer-only generator/check path:

- `tools/generate-def.sh` and `tools/lib/generate-def/` are developer-only.
- `tools/lib/common/github.sh` is shared with generator-style GitHub release
  operations and should be treated carefully when auditing runtime boundaries.
- `dev/` tooling and tests are not runtime dependencies. Later stages may use
  existing tests as coverage, but should not move developer-only dependencies
  into remote shell startup or install paths.

## Initial Risk List

| Risk | Level | Later stage | Notes |
| --- | --- | --- | --- |
| Interactive startup may mix cheap guards with optional tool initialization. | high | Stage 1 | `rc.d` hooks include optional Atuin, zoxide, Starship, update-check, welcome, fzf, and shell helper setup. Separate load-time work from call-time work before refactoring. |
| Source aggregators eagerly load broad command surfaces. | medium | Stage 2 | `tools/lib/commands.lib.sh` loads many command facades for every `remote-ssh` invocation, while install libs are lazy. Audit whether this boundary remains intentional. |
| Install/check/doctor/prune/uninstall share concepts but not one obvious ownership boundary. | high | Stage 3 | Tool state, expected tools, symlink classification, and release directories appear across several command and install modules. |
| Developer-only GitHub release helpers sit in shared `tools/lib/common/`. | medium | Stage 4 | `tools/lib/common/github.sh` is sourceable through common aggregators; keep generator/API usage from becoming runtime-required. |
| Large shell and Bash helper scripts concentrate parsing, IO, and domain logic. | medium | Stage 4 | `scripts/helm_chart_diff.sh`, `scripts/ci_run.sh`, and several command modules are candidates for later review of test seams and extraction boundaries. |
| Welcome/status code has a reduced status library beside full command libraries. | medium | Stage 1 | `tools/lib/status.lib.sh` exists to keep login-time checks lighter. Preserve this boundary unless Stage 1 proves a better shape. |
| Vendored Bash preexec is integrated into startup. | low | Stage 1 | Only `shell/rc.d/05-bash-preexec.sh` should be reviewed; do not refactor `tools/vendors/bash-preexec.sh` directly. |
| Exact tool definitions are data-like but executable shell. | medium | Stage 3 | Asset manifests are source files loaded by installer/status code. Later review should preserve exact-manifest policy. |

## Refactor Criteria

Use these criteria when evaluating follow-up stages:

- Runtime startup work must stay cheap, guarded, and easy to disable.
- Runtime code must not gain dependencies beyond the documented minimal set
  unless the dependency is explicitly optional and guarded.
- Developer-only API discovery and GitHub release generation must stay outside
  normal remote install and shell startup paths.
- Public command behavior should remain stable before internal module movement:
  same arguments, exit codes, output shape, and mutation boundaries.
- Informational flows, especially update checks, must not mutate the checkout.
- Install refactors must preserve staged installs, pinned versions, checksum
  verification, symlink rollback, and conservative prune semantics.
- Large modules should be split only when the split clarifies ownership,
  reduces duplicated behavior, or creates a meaningful test seam.
- Shared helpers should have clear ownership. Avoid adding generic helpers
  unless at least two existing call sites need the same behavior.
- Refactors that touch shared install or command behavior need focused pytest
  subprocess coverage before implementation.
- Documentation changes should follow behavior changes; this Stage 0 report is
  a planning artifact, not user-facing documentation.
