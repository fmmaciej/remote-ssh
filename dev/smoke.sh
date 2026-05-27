#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"

export SCRIPT_DIR REPO_DIR

export DEV_LOG_PREFIX=smoke

# shellcheck disable=SC1091
. "$SCRIPT_DIR/lib.sh"

dev_log "bash syntax"
find "$REPO_DIR" \
  -path "$REPO_DIR/.git" -prune -o \
  -path "$REPO_DIR/dev/.venv" -prune -o \
  -name '*.sh' -print0 \
  | xargs -0 bash -n
find "$REPO_DIR/bin" -maxdepth 1 -type f -print0 \
  | xargs -0 bash -n

dev_log "shellcheck"
dev_require_cmd shellcheck
find "$REPO_DIR" \
  -path "$REPO_DIR/.git" -prune -o \
  -path "$REPO_DIR/dev/.venv" -prune -o \
  -name '*.sh' -print0 \
  | xargs -0 shellcheck
find "$REPO_DIR/bin" -maxdepth 1 -type f -print0 \
  | xargs -0 shellcheck

dev_log "python checks"
dev_require_cmd uv
(
  cd "$SCRIPT_DIR" || exit
  PYTHONDONTWRITEBYTECODE=1 uv run ruff check --no-fix ../scripts check_assets_live.py bench_shell_startup.py bench
  PYTHONDONTWRITEBYTECODE=1 uv run mypy --config-file pyproject.toml ../scripts check_assets_live.py bench_shell_startup.py bench
)

dev_log "ok"
