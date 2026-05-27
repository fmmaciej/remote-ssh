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
- `remote-ssh-default-preseed`: default welcome with a fresh `HOME` per sample,
  plus preseeded once-per-HOME state such as the Atuin auto-import marker.
- `remote-ssh-default-warm-home`: default welcome with one isolated `HOME`
  shared by the primer, warmups, and measured samples.

`remote-ssh-default` is a cold/fresh-home diagnostic. It is useful for first
login cost, but it can overstate repeated-login cost because every sample looks
like a new account to once-per-HOME hooks. Use `remote-ssh-default-preseed` to
remove known one-time state setup from otherwise fresh samples, and
`remote-ssh-default-warm-home` to model repeated logins on the same account.

Each sample reports:

- `ready_ms`: time until the first command after shell startup prints a marker.
- `total_ms`: time until the shell process exits.

## Examples

```bash
just bench-shell --iterations 50
just bench-shell --suite login
just bench-shell --scenario remote-ssh-default
just bench-shell --scenario remote-ssh-default --format json
```

When a single non-baseline scenario is selected, `bash-baseline` is added
automatically so `ratio` and `delta` remain meaningful. Use `--format json` to
inspect captured output from failed samples.

The table also shows `slower`, the percentage slower or faster than the current
measured `bash-baseline`.

## Suites

Suites are named groups of measured scenarios. They are useful when the full
default report is too broad, but a single `--scenario` is too narrow.

```bash
just bench-shell --iterations 10 --warmup 2 --suite login
```

- `login`: `remote-ssh-min`, `remote-ssh-default`,
  `remote-ssh-default-warm-home`.

References are still added automatically for measured suites, so `login` shows
`bash-baseline` and `zsh-reference` before the suite scenarios.

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
