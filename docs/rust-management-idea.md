# Idea: migrate the management layer to Rust

Status: idea for consideration; not an approved implementation plan.

Recorded: 2026-10-30.

## Scope and motivation

Consider replacing the Bash management layer of remote-ssh with a Rust CLI,
while retaining Bash as the interactive shell and keeping its session setup
scripts. The goal would be clearer data models, explicit installation states,
and consistent error handling as application management grows.

The current project already implements the essential architecture: it installs
pinned application releases, supplies dotfiles and shell integrations, and starts
Bash with its own rcfile. This idea changes the implementation of management,
rather than introducing a new product model.

## Proposed boundary

| Component | Possible treatment |
| --- | --- |
| Public CLI and management commands | Migrate to Rust |
| Platform and asset selection, installation, tool inventory | Migrate to Rust |
| Update, uninstall, checks, diagnostics, pruning | Migrate to Rust |
| Application definitions | Move toward a declarative data format |
| Bundled dotfiles in `dots/` | Keep as project resources |
| `shell/rc.sh`, aliases, functions, history and prompt integrations | Keep in Bash |
| `runme.sh` | Retain a small bootstrap that obtains the appropriate release and starts installation |
| Developer-only definition generator | May remain in Bash initially |
| Optional Python SSH helpers | Evaluate separately; not required for the first migration |

Session startup would retain the existing flow:

```text
remote-ssh CLI in Rust
  -> resolves the environment and project resources
  -> execs bash --rcfile <resources>/shell/rc.sh -i
  -> Bash loads configuration, aliases, functions and application integrations
```

Shell code is a deliberate part of this design. Aliases, functions, and prompt
or history hooks must be installed inside the interactive Bash process. Keeping
them in Bash does not make the management-layer migration incomplete.

## Application configuration and definition generation

Applications need a supported way to receive their configuration, such as a
configuration path, environment variable, or command-line option. They do not
need specific knowledge of remote-ssh. Application-specific activation code can
remain in the session scripts.

The existing `tools/generate-def.sh` and `tools/defs/` already provide much of
the proposed upstream-to-repository translation workflow. A future definition
would describe the pinned version, exact platform assets, checksums, executable
or bundle layout, and any necessary configuration integration.

The generator could initially keep its current implementation and emit the new
data format. Generation and review would remain a maintainer workflow; runtime
installation would consume exact definitions. Supporting additional upstream
sources would be a separate feature.

## Difficulty and main work

Assessment: medium difficulty for the management layer. The earlier concern
about rewriting the entire interactive environment does not apply when the
shell layer remains in Bash.

The main work is preserving behavior and distribution contracts:

- Preserve staged installations, validation of managed paths, symlink switching,
  failure recovery, and conservative uninstall/prune behavior.
- Design how the compiled CLI is distributed and updated together with matching
  shell scripts, dotfiles, and application definitions. The current update flow
  refreshes a Git checkout and then executes the updated scripts; a compiled
  CLI needs an explicit equivalent.
- Replace executable `.sh` definitions with a well-defined data contract,
  preserving exact assets, platform preferences, checksums, aliases, and bundles.
- Preserve configuration precedence and avoid divergent interpretations between
  the CLI and session scripts.
- Reuse public-command subprocess tests where possible, adapting their launch
  mechanism. Tests that source internal Bash management functions will need
  replacement or restructuring. Shell integration tests remain relevant.

This is likely several weeks of work to preserve existing behavior, rather than
a weekend rewrite. This is only a rough assessment, not a delivery estimate.
Any shell startup performance benefit would need measurement.

## Possible first step and decision criterion

Start with a shared application/state model and implementations of `tool list`
and `check`. Compare behavior against the existing CLI before migrating the
installer, update flow, and destructive operations.

The migration becomes more attractive if remote-ssh continues to grow as an
application manager. For a stable feature set, the maintenance benefit may not
justify the rewrite and additional binary release infrastructure. Keeping Bash
for session integration is compatible with either decision.
