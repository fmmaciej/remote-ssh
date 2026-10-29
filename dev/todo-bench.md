# Shell Startup Benchmark TODO

Status: config loader and bundled welcome optimizations implemented and
independently reviewed.
Other shell startup simplification remains deferred.

The completed config-loader follow-up is documented in the
[implementation record](docs/config-loader-implementation-record.md), following
the [accepted plan](docs/config-loader-implementation-plan.md) and an independent
[implementation audit](docs/config-loader-implementation-audit.md). A fresh
[behavior re-audit](docs/config-loader-independent-reaudit.md) and
[paired performance verification](docs/config-loader-reaudit-performance.md)
confirm the size of the measured saving; the fresh audit accepted repair R1.

The welcome optimization follows its [accepted plan](docs/welcome-implementation-plan.md).
Its [implementation record](docs/welcome-implementation-record.md) retains the
full panel, compatibility checks, and two paired performance batches on Bash 3.2
and 5.3. The independent [implementation audit](docs/welcome-implementation-audit.md)
accepted R1 after repairing worker preflight and measurement snapshot preparation.

The earlier
[audit fixes](docs/audit-fix-plan.md) remain a separate correctness workstream.

## Audit observations from 2026-10-16

These measurements precede the correctness fixes and remain a baseline for the
later optimization work.

Local PTY measurements used five measured samples and one warmup per scenario:

```bash
just bench-shell --suite login --iterations 5 --warmup 1
```

| Scenario | Ready median |
| --- | ---: |
| bash-baseline | 10.0 ms |
| remote-ssh-min | 234.1 ms |
| remote-ssh-default | 402.9 ms |
| remote-ssh-default-warm-home | 361.7 ms |

These measurements used the local machine and available integrations, including
Starship, Zoxide, and fzf, without Atuin. Compare changes on the same machine
with the same tools and state. The benchmark's `zsh-reference` is a synthetic
reference and is not a measured competing shell.

A separate isolated measurement of loading `shell/config.lib.sh` and calling
`remote_ssh_config_load` under `/bin/bash` gave medians of 61.1 ms without a
config file and 486.9 ms with all nine allowed keys, over five runs each. This
is a loader measurement, separate from the PTY scenarios above. The current
loader scans the config file again for every key and creates many subprocesses.

## Simplification work

1. Completed: parse config once per load and remove repeated parser/marker
   subprocesses. Allowed keys, literal values, environment precedence, reload
   behavior, and child-process provenance are preserved. See the
   [implementation and measurements](docs/config-loader-implementation-record.md).
2. Completed: render the three standard welcome modules in one fresh Bash
   worker that loads the library once. The full status panel, separate renderer
   captures, external user modules, standalone wrappers, and conservative
   external fallback are preserved. See the
   [implementation and measurements](docs/welcome-implementation-record.md).
3. Review the startup load graph and repeated source guards. Consolidate tiny
   private modules where it improves readability, and avoid external `basename`
   calls just to construct guard messages. Keep public command facades.
4. Review optional initialization for Atuin, bash-preexec, Starship, and Zoxide.
   Load only the integrations needed by the selected shell behavior. Preserve
   history and prompt correctness before trying lazy initialization.
5. Revisit the default tool selection. Promote `mini` and `quick` as lightweight
   starting points and keep the full set available. Review `nu`, `nvim`, `yazi`,
   `zellij`, and `bssh` as optional additions. Any default-list change must keep
   `DEFAULT_TOOLS`, `RUNME_TOOLS`, documentation, and tests synchronized.
6. Check callers before removing unused `load_once` and `init_lib`, the older
   `scripts/ssh_hosts.py`, and duplicated SSH parsing. Keep the Python dependency
   of `ssh-find` and `ssh-pick` explicit.
7. Remove unreachable Zsh branches only after choosing the supported integration
   boundary and adjusting tests. The public shell entrypoint remains Bash-only.
8. Keep developer simplification separate: replace heuristic GitHub JSON parsing
   with a real parser in developer tooling without adding runtime dependencies.

Do not turn this list into a broad refactor during the correctness fixes.
History fallback is part of the current repair plan, even though it touches
shell initialization.

## Earlier profiling notes

The following measurements came from an earlier local diagnostic. They are
historical context, not the current baseline or a guaranteed performance target.

This earlier diagnostic tracked startup-time wins after the welcome/status
benchmark work.

Earlier local shape:

```text
bash-baseline                 ~12 ms
remote-ssh-min               ~315 ms
remote-ssh-default           ~527 ms
remote-ssh-default-warm-home ~459 ms
```

The remaining cost is not one single hook:

- baseline `rc.sh` without welcome is roughly `300 ms`;
- welcome adds roughly `150-220 ms`;
- warm-home removes some once-per-HOME cost, but repeated-login startup is
  still around `450 ms`.

### Earlier Optimization Candidates

1. Replace `git config` calls in `07-git-session-identity.sh`.

   Revisit the proposed parser before implementation: prefer one Git query or
   deferred lookup. A handwritten parser must not silently lose supported Git
   quoting or configuration semantics.

   The hook currently calls `git config --file dots/git/user.local --get`
   twice. Local profiling showed:

   ```text
   two git config calls   ~108 ms
   one git get-regexp      ~91 ms
   simple file parser      ~12 ms
   ```

   A small shell/awk parser for the simple `dots/git/user.local` shape should
   preserve behavior and save roughly `70-90 ms` on login.

2. Render bundled welcome modules in-process.

   User custom modules should stay isolated subprocesses, but bundled modules
   are trusted repo code. Today each bundled module is executed as a separate
   process and sources `welcome.lib.sh` again.

   Local profiling:

   ```text
   current default rc        ~606 ms
   no welcome                ~325 ms
   direct bundled welcome    ~511 ms
   ```

   Rendering bundled welcome directly from the runner could save roughly
   `70-100 ms` while keeping user modules isolated.

3. Add a diagnostic benchmark suite for fast-login tradeoffs.

   Useful variants:

   - default;
   - warm-home;
   - Git session identity disabled;
   - optional integrations disabled.

   This should be diagnostic only, not a runtime behavior change.

4. Consider cache for tools/scripts welcome status later.

   `status.lib.sh` reduced the cost of loading command status, but tools/scripts
   status still costs roughly `50-80 ms`. A cache could help, but it adds state
   semantics and refresh policy, so it should come after the lower-risk wins.

### Earlier Lower Priority Areas

- Atuin, bash-preexec, Starship, and Zoxide are visible but functional
  tradeoffs. Disabling them by default would change the shell experience.
- `env.sh` and aliases cost roughly `80-90 ms`. Further optimization would
  require flattening loader paths and reducing source calls, which may hurt
  maintainability for a smaller gain.

### Earlier Target

Getting `remote-ssh-default` from roughly `500 ms` to `330-380 ms` looks
realistic without a major architecture change. Getting below `250 ms` probably
requires sharper tradeoffs: lazy optional integrations, fewer default features,
or cached welcome status.
