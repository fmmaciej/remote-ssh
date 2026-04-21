#!/usr/bin/env bash
# shellcheck disable=SC2030,SC2031

test_atuin_init_sets_bash_config_and_runs_init() {
  log "atuin init sets bash config and runs init"

  local repo_root="$REPO_DIR"
  local stub_dir
  stub_dir="$(mktemp -d)"
  trap 'rm -rf "$stub_dir"' RETURN

  cat >"$stub_dir/atuin" <<'EOF'
#!/usr/bin/env bash
if [[ "${1:-}" == "init" && "${2:-}" == "bash" ]]; then
  cat <<'SCRIPT'
export REMOTE_SSH_TEST_ATUIN_BASH_INIT=1
SCRIPT
  exit 0
fi
exit 1
EOF
  chmod +x "$stub_dir/atuin"

  local output
  output="$(
    PATH="$stub_dir:$PATH" bash -i -c '
      export REMOTE_SSH_REPO_DIR="'"$repo_root"'"
      export REMOTE_DOTS_DIR="$REMOTE_SSH_REPO_DIR/dots"
      export bash_preexec_imported=1
      source "$REMOTE_SSH_REPO_DIR/shell/rc.d/23-atuin.sh"
      printf "init=%s\n" "${REMOTE_SSH_TEST_ATUIN_BASH_INIT:-0}"
      printf "config=%s\n" "${ATUIN_CONFIG_DIR:-}"
    ' 2>/dev/null
  )"

  grep -q '^init=1$' <<<"$output"
  grep -q '^config='"$repo_root"'/dots/atuin$' <<<"$output"

  trap - RETURN
  rm -rf "$stub_dir"
}

register_test test_atuin_init_sets_bash_config_and_runs_init
