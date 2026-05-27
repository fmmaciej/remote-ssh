# Checks And Tests

Back: [Developer tooling](../README.md)

`just smoke` is the default verification for normal changes:

```bash
just smoke
```

It runs static Bash checks, `shellcheck`, `ruff`, `mypy`, and the pytest suite
under `dev/tests/`.

## Focused Checks

```bash
just lint
just fmt
just type
just test
```

From `dev/`, the same checks can be split further:

```bash
just py-lint
just py-fmt
just py-type
just py-test
just sh-lint
just sh-fmt
```

## Test Guidance

Prefer pytest tests under `dev/tests/` for new behavior that can exercise public
commands as subprocesses. Tests may launch Bash subprocesses when they need to
source shell functions, rc files, aliases, or tool definitions.

Keep developer-only helpers in `dev/`; do not make remote runtime shell code
depend on `dev/` files.
