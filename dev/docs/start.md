# Developer Start

Back: [Developer tooling](../README.md)

Developer tooling is local-only. Remote runtime code should not depend on
anything installed through `dev/`.

## Tools

- `uv`: manages the Python developer environment from `dev/pyproject.toml`.
- `just`: runs common developer commands.
- `ruff`, `mypy`, `pytest`, and `pre-commit`: installed by `uv`.

Install `uv` and `just` with your local package manager:

```bash
brew install uv just
pacman -S uv just
apt install uv just
```

Then sync the developer environment:

```bash
cd dev
uv sync
```

## Git Hooks

After syncing, install optional pre-commit hooks:

```bash
just pre-commit-install
```

Run them manually with:

```bash
just pre-commit
```
