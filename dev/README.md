# Developer Tooling

`dev/` contains optional local tooling used to maintain this repository. Nothing
here is required on remote hosts, and developer dependencies must stay isolated
from runtime shell code.

Python developer tooling targets Python 3.13.

## Quick Start

```bash
cd dev
uv sync
just smoke
```

From the repository root, the top-level `justfile` delegates common developer
commands to `dev/justfile`:

```bash
just smoke
just lint
just fmt
```

## Sections

- [Start](docs/start.md): required local tools, `uv sync`, and pre-commit hooks.
- [Commands](docs/commands.md): root and `dev/` `just` recipes.
- [Checks](docs/checks.md): smoke, lint, type checks, pytest, and test guidance.
- [Live Assets](docs/live-assets.md): optional GitHub Releases validation.
- [Shell Startup Benchmark](docs/bench-shell.md): local PTY benchmark for
  remote-ssh shell startup cost.

## Notes

- No global Python developer tools are required beyond `uv`.
- Python scripts in this repository should use the standard library unless a
  dependency is explicitly isolated in developer tooling.
- Runtime install paths are documented in
  [Install Flow](../docs/install.md#installed-paths).
