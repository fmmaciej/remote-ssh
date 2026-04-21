#!/usr/bin/env bash
# shellcheck disable=SC2030,SC2031

test_atuin_init_sets_zsh_config_and_runs_init() {
  if ! command -v zsh >/dev/null 2>&1; then
    log "SKIP: zsh not available"
    return 0
  fi

  log "atuin init sets zsh config and runs init"

  local repo_root="$REPO_DIR"
  local stub_dir
  stub_dir="$(mktemp -d)"
  trap 'rm -rf "$stub_dir"' RETURN

  cat >"$stub_dir/atuin" <<'EOF'
#!/usr/bin/env bash
if [[ "${1:-}" == "init" && "${2:-}" == "zsh" ]]; then
  cat <<'SCRIPT'
export REMOTE_SSH_TEST_ATUIN_ZSH_INIT=1
SCRIPT
  exit 0
fi
exit 1
EOF
  chmod +x "$stub_dir/atuin"

  local output
  output="$(
    PATH="$stub_dir:$PATH" zsh -i -c '
      export PATH="'"$stub_dir"':$PATH"
      export REMOTE_SSH_REPO_DIR="'"$repo_root"'"
      export REMOTE_DOTS_DIR="$REMOTE_SSH_REPO_DIR/dots"
      source "$REMOTE_SSH_REPO_DIR/shell/rc.d/23-atuin.sh"
      print -r -- "init=${REMOTE_SSH_TEST_ATUIN_ZSH_INIT:-0}"
      print -r -- "config=${ATUIN_CONFIG_DIR:-}"
    ' 2>/dev/null
  )"

  grep -q '^init=1$' <<<"$output"
  grep -q '^config='"$repo_root"'/dots/atuin$' <<<"$output"

  trap - RETURN
  rm -rf "$stub_dir"
}

register_test test_atuin_init_sets_zsh_config_and_runs_init
