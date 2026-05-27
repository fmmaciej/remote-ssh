# Shell Startup Benchmark

Back: [Developer tooling](../README.md)

`just bench-shell` runs a local, developer-only benchmark for shell startup
cost:

```bash
just bench-shell
```

The benchmark uses a pseudo-TTY and isolated `HOME`, `XDG_CONFIG_HOME`, and
`XDG_STATE_HOME` directories. It is local-first and does not require SSH access.
Treat results as relative diagnostics on the same machine, not as a pass/fail
threshold.

## Scenarios

- `bash-baseline`: clean `bash --noprofile --norc`.
- `remote-ssh-min`: remote-ssh `rc.sh` with welcome and update check disabled.
- `remote-ssh-welcome`: welcome enabled, update check disabled, user modules
  disabled.
- `remote-ssh-default`: default welcome with an isolated fresh update cache.

Each sample reports:

- `ready_ms`: time until the first command after shell startup prints a marker.
- `total_ms`: time until the shell process exits.

## Examples

```bash
just bench-shell --iterations 50
just bench-shell --scenario remote-ssh-default
just bench-shell --scenario remote-ssh-default --format json
```

When a single non-baseline scenario is selected, `bash-baseline` is added
automatically so `ratio` and `delta` remain meaningful. Use `--format json` to
inspect captured output from failed samples.
