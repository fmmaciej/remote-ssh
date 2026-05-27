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
- `zsh-reference`: synthetic Zsh startup reference loaded from
  `dev/config/shell_startup_references.json`.
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

The table also shows `slower`, the percentage slower or faster than the current
measured `bash-baseline`.

## Reference Values

Reference scenarios are loaded from:

```text
dev/config/shell_startup_references.json
dev/config/shell_startup_references.local.json
```

The first file is versioned. The `.local.json` file is ignored by Git and can
override or add local references. These values are synthetic reference points;
the benchmark does not execute `zsh` for them. They are still compared against
the current measured `bash-baseline`.

Example local override:

```json
{
  "references": [
    {
      "name": "zsh-reference",
      "description": "My zsh -i startup from local dotfiles",
      "ready_ms": 196.0,
      "total_ms": 196.5
    },
    {
      "name": "zsh-dotfiles",
      "description": "Another local Zsh reference",
      "ready_ms": 220.0,
      "total_ms": 221.0
    }
  ]
}
```
