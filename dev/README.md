# Developer tooling

This directory contains **optional developer tooling** used to maintain this repository.
Nothing here is required to run the scripts on remote servers or production machines.

The tools below are intended for **local development only**.

---

## Tools used

### uv

Yeah, it's a cool tool.

### just

Task runner used to define and run common development commands
(e.g. linting and formatting).

### ruff

Python linter and formatter used for scripts in `bin/`.

### pre-commit

Git hook manager used to run checks automatically before commits.

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

### Tools

```bash
uv tool install ruff
uv tool install mypy
uv tool install pre-commit
```

## Usage

Top level directory:

```bash
just lint
just fmt
just type
just test
just smoke
just test-assets-live
```

Developer divectory `dev/`:

```bash
just py-lint
just py-fmt
just py-type
just sh-lint
just sh-fmt
just test
just smoke
just test-assets-live
```

`just test-assets-live` is optional and uses the GitHub Releases API to
check that generated asset names exist for the pinned tool versions. It does
not download the release archives.

If you hit GitHub API rate limits, copy `dev/.env.example` to `dev/.env` and
set `GITHUB_TOKEN` or `GH_TOKEN`. `dev/.env` is local-only and ignored by git.

Smoke tests live in `dev/tests/`. Files are prefixed with numbers to keep the
execution order readable.

Optional: enable git hooks locally:

```bash
pre-commit install -c dev/.pre-commit-config.yaml
```

---

## Notes

- No Python virtual environment is required.
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
