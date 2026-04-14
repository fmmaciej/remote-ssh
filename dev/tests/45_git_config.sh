#!/usr/bin/env bash
# shellcheck disable=SC2030,SC2031

test_remote_git_config_add() {
  log "remote git config is session-scoped"

  require_cmd git

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  local got
  got="$(
    export HOME="$tmp/home"
    mkdir -p "$HOME"
    # shellcheck source=/dev/null
    . "$REPO_DIR/lib/guards.sh"
    # shellcheck source=/dev/null
    . "$REPO_DIR/lib/helpers.sh"

    remote_git_config_add user.name "Remote SSH"
    remote_git_config_add user.email "remote-ssh@example.invalid"
    remote_git_config_add pull.ff "only"

    printf '%s\n' "$(git config user.name)"
    printf '%s\n' "$(git config user.email)"
    printf '%s\n' "$(git config pull.ff)"

    if [[ -e "$HOME/.gitconfig" ]]; then
      printf 'unexpected-global-config\n'
    fi
  )"

  assert_eq "session git config" $'Remote SSH\nremote-ssh@example.invalid\nonly' "$got"

  trap - RETURN
  rm -rf "$tmp"
}

test_remote_git_config_can_override_keys() {
  log "remote git config can be overridden later"

  require_cmd git

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  local got
  got="$(
    export HOME="$tmp/home"
    mkdir -p "$HOME"
    # shellcheck source=/dev/null
    . "$REPO_DIR/lib/guards.sh"
    # shellcheck source=/dev/null
    . "$REPO_DIR/lib/helpers.sh"

    remote_git_config_add core.editor "nvim"
    remote_git_config_add core.editor "vim"

    git config core.editor
  )"

  assert_eq "session git config override" "vim" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

test_git_rc_defaults_and_host_override() {
  log "git rc defaults can be refined by host.d"

  require_cmd git

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/remote/lib" "$tmp/remote/shell/rc.d/host.d" "$tmp/bin" "$tmp/home"

  cp "$REPO_DIR/lib/guards.sh" "$tmp/remote/lib/guards.sh"
  cp "$REPO_DIR/lib/helpers.sh" "$tmp/remote/lib/helpers.sh"
  cp "$REPO_DIR/shell/env.sh" "$tmp/remote/shell/env.sh"
  cp "$REPO_DIR/shell/aliases.sh" "$tmp/remote/shell/aliases.sh"
  cp "$REPO_DIR/shell/rc.sh" "$tmp/remote/shell/rc.sh"
  cp "$REPO_DIR/shell/rc.d/10-editor-pager.sh" "$tmp/remote/shell/rc.d/10-editor-pager.sh"
  cp "$REPO_DIR/shell/rc.d/12-git.sh" "$tmp/remote/shell/rc.d/12-git.sh"

  cat >"$tmp/remote/shell/rc.d/host.d/gitbox.sh" <<'EOF'
# shellcheck shell=bash
ensure_this_file_sourced
remote_git_config_add core.editor "vim"
remote_git_config_add user.name "Host User"
EOF

  cat >"$tmp/bin/hostname" <<'EOF'
#!/usr/bin/env bash
if [[ "${1:-}" == "-s" ]]; then
  printf 'gitbox\n'
else
  printf 'gitbox.example\n'
fi
EOF
  chmod +x "$tmp/bin/hostname"

  local got
  got="$(
    export HOME="$tmp/home"
    export PATH="$tmp/bin:$PATH"
    # shellcheck source=/dev/null
    . "$tmp/remote/shell/rc.sh"

    printf '%s\n' "$(git config pull.rebase)"
    printf '%s\n' "$(git config rebase.autoStash)"
    printf '%s\n' "$(git config fetch.prune)"
    printf '%s\n' "$(git config push.autoSetupRemote)"
    printf '%s\n' "$(git config init.defaultBranch)"
    printf '%s\n' "$(git config core.editor)"
    printf '%s\n' "$(git config user.name)"
  )"

  assert_eq "git rc defaults and host override" $'true\ntrue\ntrue\ntrue\nmain\nvim\nHost User' "$got"

  trap - RETURN
  rm -rf "$tmp"
}

register_test test_remote_git_config_add
register_test test_remote_git_config_can_override_keys
register_test test_git_rc_defaults_and_host_override
