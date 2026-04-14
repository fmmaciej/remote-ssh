#!/usr/bin/env bash

test_static_checks() {
  log "bash syntax"
  find "$REPO_DIR" \
    -path "$REPO_DIR/.git" -prune -o \
    -name '*.sh' -print0 \
    | xargs -0 bash -n

  log "shellcheck"
  require_cmd shellcheck
  find "$REPO_DIR" \
    -path "$REPO_DIR/.git" -prune -o \
    -name '*.sh' -print0 \
    | xargs -0 shellcheck

  log "python checks"
  require_cmd ruff
  require_cmd mypy
  PYTHONDONTWRITEBYTECODE=1 ruff check --no-fix "$REPO_DIR/scripts"
  PYTHONDONTWRITEBYTECODE=1 mypy --config-file "$REPO_DIR/dev/pyproject.toml" "$REPO_DIR/scripts"
}

register_test test_static_checks
