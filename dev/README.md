# Developer tooling

This directory contains **optional developer tooling** used to maintain this repository.
Nothing here is required to run the scripts on remote servers or production machines.

The tools below are intended for **local development only**.
Python developer tooling targets Python 3.13.

---

## Tools used

### uv

Yeah, it's a cool tool.

### just

Task runner used to define and run common development commands
(e.g. linting and formatting).

### ruff, mypy, pytest, pre-commit

Python developer tools managed by `uv` from `dev/pyproject.toml`.

---

## Installation

### macOS

Using Homebrew:

```bash
brew install uv just
```

### Linux

Arch Linux

```bash
pacman -S uv just
```

Debian / Ubuntu

```bash
apt install uv just
```

### Python developer environment

```bash
cd dev
uv sync
```

### Git hooks

After syncing the developer environment, install the local pre-commit hooks:

```bash
just pre-commit-install
```

## Usage

Top level directory:

```bash
just lint
just fmt
just type
just test
just smoke
just pre-commit-install
just pre-commit
just test-assets-live
```

Developer directory `dev/`:

```bash
just py-lint
just py-fmt
just py-type
just py-test
just sh-lint
just sh-fmt
just test
just smoke
just pre-commit-install
just pre-commit
just test-assets-live
```

`just test-assets-live` is optional and uses the GitHub Releases API to
check that generated asset names exist for the pinned tool versions. It does
not download the release archives.

If you hit GitHub API rate limits, copy `dev/.env.example` to `dev/.env` and
set `GITHUB_TOKEN` or `GH_TOKEN`. `dev/.env` is local-only and ignored by git.
The live checker is implemented in `dev/check_assets_live.py` and is normally
run through `just test-assets-live`.

Smoke checks are split by responsibility:

- `dev/lib.sh` contains small helpers for developer scripts.
- `dev/smoke.sh` runs static checks: Bash syntax, `shellcheck`, `ruff`, and
  `mypy`.
- `dev/tests/` contains pytest subprocess and integration tests.

Prefer pytest for new CLI/integration tests. Tests may still launch Bash
subprocesses when they need to source shell functions, rc files, aliases, or
tool definitions.

The pre-commit hooks are optional but recommended for regular development.

---

## Notes

- No global Python developer tools are required beyond `uv`.
- Python scripts in this repository are expected to run using the standard library only.
- This tooling is intentionally isolated in `dev/` to avoid impacting runtime environments.

## Repository structure

```bash
$HOME/
  .local/
    bin/      # symlinks do fd/rg/fzf/yazi/nvim/starship itd.
    dev/
    opt/      # binaries: fd-10.3.0, rg-15.1.0...
    share/
      remote-ssh/
        bin/
        dots/
        libs/
        shell/
        tools/
        POST_INSTALL.txt
        README.md
```
