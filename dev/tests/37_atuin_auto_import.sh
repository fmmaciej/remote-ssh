#!/usr/bin/env bash
# shellcheck disable=SC2030,SC2031

test_atuin_auto_import_runs_once_when_marker_is_missing() {
  log "atuin auto import runs once when marker is missing"

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/bin" "$tmp/home" "$tmp/state"

  cat >"$tmp/bin/atuin" <<'EOF'
#!/usr/bin/env bash
if [[ "${1:-}" == "import" && "${2:-}" == "auto" ]]; then
  printf 'import auto\n' >> "$ATUIN_TEST_LOG"
  exit 0
fi
if [[ "${1:-}" == "init" && "${2:-}" == "bash" ]]; then
  printf 'export REMOTE_SSH_TEST_ATUIN_BASH_INIT=1\n'
  exit 0
fi
exit 0
EOF
  chmod +x "$tmp/bin/atuin"

  local output
  output="$(
    PATH="$tmp/bin:/usr/bin:/bin:/usr/sbin:/sbin" \
    HOME="$tmp/home" \
    XDG_STATE_HOME="$tmp/state" \
    ATUIN_TEST_LOG="$tmp/import.log" \
    REPO_DIR="$REPO_DIR" \
      bash --noprofile --norc -ic '
        export REMOTE_DOTS_DIR="$REPO_DIR/dots"
        export bash_preexec_imported=1
        . "$REPO_DIR/lib/guards.sh"
        . "$REPO_DIR/lib/helpers.sh"
        . "$REPO_DIR/shell/rc.d/23-atuin.sh"
        printf "log=%s\n" "$(cat "$ATUIN_TEST_LOG")"
        printf "marker=%s\n" "$XDG_STATE_HOME/remote-ssh/atuin-import-auto.done"
        printf "marked=%s\n" "$([[ -f "$XDG_STATE_HOME/remote-ssh/atuin-import-auto.done" ]] && printf 1 || printf 0)"
      ' 2>/dev/null
  )"

  grep -q '^log=import auto$' <<<"$output"
  grep -q '^marked=1$' <<<"$output"

  trap - RETURN
  rm -rf "$tmp"
}

test_atuin_auto_import_is_skipped_when_marker_exists() {
  log "atuin auto import is skipped when marker exists"

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/bin" "$tmp/home" "$tmp/state/remote-ssh"
  : > "$tmp/state/remote-ssh/atuin-import-auto.done"

  cat >"$tmp/bin/atuin" <<'EOF'
#!/usr/bin/env bash
if [[ "${1:-}" == "import" && "${2:-}" == "auto" ]]; then
  printf 'import auto\n' >> "$ATUIN_TEST_LOG"
  exit 0
fi
if [[ "${1:-}" == "init" && "${2:-}" == "bash" ]]; then
  printf 'export REMOTE_SSH_TEST_ATUIN_BASH_INIT=1\n'
  exit 0
fi
exit 0
EOF
  chmod +x "$tmp/bin/atuin"

  local output
  output="$(
    PATH="$tmp/bin:/usr/bin:/bin:/usr/sbin:/sbin" \
    HOME="$tmp/home" \
    XDG_STATE_HOME="$tmp/state" \
    ATUIN_TEST_LOG="$tmp/import.log" \
    REPO_DIR="$REPO_DIR" \
      bash --noprofile --norc -ic '
        export REMOTE_DOTS_DIR="$REPO_DIR/dots"
        export bash_preexec_imported=1
        . "$REPO_DIR/lib/guards.sh"
        . "$REPO_DIR/lib/helpers.sh"
        . "$REPO_DIR/shell/rc.d/23-atuin.sh"
        printf "logged=%s\n" "$([[ -f "$ATUIN_TEST_LOG" ]] && printf 1 || printf 0)"
        printf "marked=%s\n" "$([[ -f "$XDG_STATE_HOME/remote-ssh/atuin-import-auto.done" ]] && printf 1 || printf 0)"
      ' 2>/dev/null
  )"

  grep -q '^logged=0$' <<<"$output"
  grep -q '^marked=1$' <<<"$output"

  trap - RETURN
  rm -rf "$tmp"
}

register_test test_atuin_auto_import_runs_once_when_marker_is_missing
register_test test_atuin_auto_import_is_skipped_when_marker_exists
