# Shell Startup Benchmark TODO

This note tracks likely startup-time wins after the welcome/status benchmark
work.

Current local shape:

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

## Highest-Value Optimizations

1. Replace `git config` calls in `07-git-session-identity.sh`.

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

## Lower-Priority Areas

- Atuin, bash-preexec, Starship, and Zoxide are visible but functional
  tradeoffs. Disabling them by default would change the shell experience.
- `env.sh` and aliases cost roughly `80-90 ms`. Further optimization would
  require flattening loader paths and reducing source calls, which may hurt
  maintainability for a smaller gain.

## Practical Target

Getting `remote-ssh-default` from roughly `500 ms` to `330-380 ms` looks
realistic without a major architecture change. Getting below `250 ms` probably
requires sharper tradeoffs: lazy optional integrations, fewer default features,
or cached welcome status.
