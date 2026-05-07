#!/usr/bin/env bash
# shellcheck disable=SC2030,SC2031

test_rc_loads_os_and_host_overrides() {
  log "rc.sh loads os.d and host.d"

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/remote/lib" "$tmp/remote/shell/rc.d/os.d" "$tmp/remote/shell/rc.d/host.d" "$tmp/bin"

  cp "$REPO_DIR/lib/guards.sh" "$tmp/remote/lib/guards.sh"
  cp "$REPO_DIR/lib/helpers.sh" "$tmp/remote/lib/helpers.sh"
  cp "$REPO_DIR/shell/env.sh" "$tmp/remote/shell/env.sh"
  cp "$REPO_DIR/shell/aliases.sh" "$tmp/remote/shell/aliases.sh"
  cp "$REPO_DIR/shell/rc.sh" "$tmp/remote/shell/rc.sh"

  cat >"$tmp/remote/shell/rc.d/10-base.sh" <<'EOF'
# shellcheck shell=bash
ensure_this_file_sourced
RC_FLOW="${RC_FLOW:-}:base"
export RC_FLOW
EOF

  cat >"$tmp/remote/shell/rc.d/os.d/linux.sh" <<'EOF'
# shellcheck shell=bash
ensure_this_file_sourced
RC_FLOW="${RC_FLOW:-}:linux"
export RC_FLOW
EOF

  cat >"$tmp/remote/shell/rc.d/host.d/testbox.sh" <<'EOF'
# shellcheck shell=bash
ensure_this_file_sourced
RC_FLOW="${RC_FLOW:-}:host"
export RC_FLOW
EOF

  cat >"$tmp/bin/uname" <<'EOF'
#!/usr/bin/env bash
printf 'Linux\n'
EOF
  chmod +x "$tmp/bin/uname"

  cat >"$tmp/bin/hostname" <<'EOF'
#!/usr/bin/env bash
if [[ "${1:-}" == "-s" ]]; then
  printf 'testbox\n'
else
  printf 'testbox.example\n'
fi
EOF
  chmod +x "$tmp/bin/hostname"

  local got
  got="$(
    PATH="$tmp/bin:$PATH"
    # shellcheck source=/dev/null
    . "$tmp/remote/shell/rc.sh"
    printf '%s\n' "$RC_FLOW"
  )"

  assert_eq "rc load order" ":base:linux:host" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

register_test test_rc_loads_os_and_host_overrides

test_update_check_rc_skips_noninteractive_shells() {
  log "update check rc hook skips non-interactive shells"

  local tmp got
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/remote/lib" "$tmp/remote/bin" "$tmp/remote/shell/rc.d"

  cp "$REPO_DIR/lib/guards.sh" "$tmp/remote/lib/guards.sh"
  cp "$REPO_DIR/lib/helpers.sh" "$tmp/remote/lib/helpers.sh"
  cp "$REPO_DIR/shell/env.sh" "$tmp/remote/shell/env.sh"
  cp "$REPO_DIR/shell/aliases.sh" "$tmp/remote/shell/aliases.sh"
  cp "$REPO_DIR/shell/rc.sh" "$tmp/remote/shell/rc.sh"
  cp "$REPO_DIR/shell/rc.d/04-update-check.sh" "$tmp/remote/shell/rc.d/04-update-check.sh"

  cat >"$tmp/remote/bin/remote-ssh" <<EOF
#!/usr/bin/env bash
touch "$tmp/called"
exit 1
EOF
  chmod +x "$tmp/remote/bin/remote-ssh"

  got="$(
    export REMOTE_SSH_UPDATE_CHECK_STATE_DIR="$tmp/state"
    # shellcheck source=/dev/null
    . "$tmp/remote/shell/rc.sh"
    if [[ -e "$tmp/called" ]]; then
      printf 'called\n'
    else
      printf 'skipped\n'
    fi
  )"

  assert_eq "non-interactive update check hook" "skipped" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

register_test test_update_check_rc_skips_noninteractive_shells
