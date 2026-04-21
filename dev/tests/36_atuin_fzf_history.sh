#!/usr/bin/env bash
# shellcheck disable=SC2030,SC2031

test_atuin_plugin_initializes_for_bash() {
  log "atuin rc plugin initializes bash integration"

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/bin"

  cat >"$tmp/bin/atuin" <<'EOF'
#!/usr/bin/env bash
if [[ "${1:-}" == "init" && "${2:-}" == "bash" ]]; then
  printf 'export ATUIN_INIT_SHELL=bash\n'
fi
EOF
  chmod +x "$tmp/bin/atuin"

  local test_path="$tmp/bin:/usr/bin:/bin:/usr/sbin:/sbin"
  local got
  got="$(
    PATH="$test_path" REPO_DIR="$REPO_DIR" \
      bash --noprofile --norc -ic '
        export REMOTE_DOTS_DIR="$REPO_DIR/dots"
        export bash_preexec_imported=1
        . "$REPO_DIR/lib/guards.sh"
        . "$REPO_DIR/lib/helpers.sh"
        . "$REPO_DIR/shell/rc.d/23-atuin.sh"
        printf "%s\n" "${ATUIN_INIT_SHELL:-missing}"
      ' 2>/dev/null
  )"

  assert_eq "atuin bash init" "bash" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

test_fzf_history_bind_is_fallback_when_atuin_is_missing() {
  log "fzf history bind is fallback when atuin is missing"

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/bin"

  cat >"$tmp/bin/fzf" <<'EOF'
#!/usr/bin/env bash
exit 0
EOF
  chmod +x "$tmp/bin/fzf"

  local test_path="$tmp/bin:/usr/bin:/bin:/usr/sbin:/sbin"
  local bind_log="$tmp/bind.log"
  local got
  got="$(
    PATH="$test_path" REPO_DIR="$REPO_DIR" BIND_LOG="$bind_log" \
      bash --noprofile --norc -ic '
        bind() {
          if [[ "${1:-}" == "-x" && "${2:-}" == *"__fzf_history"* ]]; then
            printf "%s\n" "$2" >> "$BIND_LOG"
          fi
          return 0
        }
        . "$REPO_DIR/lib/guards.sh"
        . "$REPO_DIR/lib/helpers.sh"
        . "$REPO_DIR/shell/rc.d/20-fzf.sh"
        if [[ -s "$BIND_LOG" ]]; then
          printf bound
        else
          printf missing
        fi
      ' 2>/dev/null
  )"

  assert_eq "fzf history fallback bind" "bound" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

test_fzf_history_bind_is_skipped_when_atuin_exists() {
  log "fzf history bind is skipped when atuin exists"

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/bin"

  cat >"$tmp/bin/fzf" <<'EOF'
#!/usr/bin/env bash
exit 0
EOF
  chmod +x "$tmp/bin/fzf"

  cat >"$tmp/bin/atuin" <<'EOF'
#!/usr/bin/env bash
exit 0
EOF
  chmod +x "$tmp/bin/atuin"

  local test_path="$tmp/bin:/usr/bin:/bin:/usr/sbin:/sbin"
  local bind_log="$tmp/bind.log"
  local got
  got="$(
    PATH="$test_path" REPO_DIR="$REPO_DIR" BIND_LOG="$bind_log" \
      bash --noprofile --norc -ic '
        bind() {
          if [[ "${1:-}" == "-x" && "${2:-}" == *"__fzf_history"* ]]; then
            printf "%s\n" "$2" >> "$BIND_LOG"
          fi
          return 0
        }
        . "$REPO_DIR/lib/guards.sh"
        . "$REPO_DIR/lib/helpers.sh"
        . "$REPO_DIR/shell/rc.d/20-fzf.sh"
        if [[ -s "$BIND_LOG" ]]; then
          printf bound
        else
          printf skipped
        fi
      ' 2>/dev/null
  )"

  assert_eq "fzf history bind with atuin" "skipped" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

register_test test_atuin_plugin_initializes_for_bash
register_test test_fzf_history_bind_is_fallback_when_atuin_is_missing
register_test test_fzf_history_bind_is_skipped_when_atuin_exists
