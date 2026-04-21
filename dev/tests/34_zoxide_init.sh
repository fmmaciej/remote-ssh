#!/usr/bin/env bash
# shellcheck disable=SC2030,SC2031

test_zoxide_initializes_for_bash() {
  log "zoxide initializes for bash"

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/bin"

  cat >"$tmp/bin/zoxide" <<'EOF'
#!/usr/bin/env bash
if [[ "${1:-}" == "init" && "${2:-}" == "bash" ]]; then
  printf 'export REMOTE_SSH_TEST_ZOXIDE_SHELL=bash\n'
  exit 0
fi
if [[ "${1:-}" == "init" && "${2:-}" == "zsh" ]]; then
  printf 'export REMOTE_SSH_TEST_ZOXIDE_SHELL=zsh\n'
  exit 0
fi
exit 1
EOF
  chmod +x "$tmp/bin/zoxide"

  local got
  got="$(
    PATH="$tmp/bin:/usr/bin:/bin:/usr/sbin:/sbin" REPO_DIR="$REPO_DIR" \
      bash --noprofile --norc -ic '
        export REMOTE_DOTS_DIR="$REPO_DIR/dots"
        . "$REPO_DIR/lib/guards.sh"
        . "$REPO_DIR/lib/helpers.sh"
        . "$REPO_DIR/shell/rc.d/21-zoxide.sh"
        printf "shell=%s\n" "${REMOTE_SSH_TEST_ZOXIDE_SHELL:-missing}"
        printf "z=%s\n" "$(type -t z || true)"
        printf "zi=%s\n" "$(type -t zi || true)"
      ' 2>/dev/null
  )"

  grep -q '^shell=bash$' <<<"$got"
  grep -q '^z=function$' <<<"$got"
  grep -q '^zi=function$' <<<"$got"

  trap - RETURN
  rm -rf "$tmp"
}

test_zoxide_initializes_for_zsh() {
  if ! command -v zsh >/dev/null 2>&1; then
    log "SKIP: zsh not available"
    return 0
  fi

  log "zoxide initializes for zsh"

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/bin"

  cat >"$tmp/bin/zoxide" <<'EOF'
#!/usr/bin/env bash
if [[ "${1:-}" == "init" && "${2:-}" == "bash" ]]; then
  printf 'export REMOTE_SSH_TEST_ZOXIDE_SHELL=bash\n'
  exit 0
fi
if [[ "${1:-}" == "init" && "${2:-}" == "zsh" ]]; then
  printf 'export REMOTE_SSH_TEST_ZOXIDE_SHELL=zsh\n'
  exit 0
fi
exit 1
EOF
  chmod +x "$tmp/bin/zoxide"

  local got
  got="$(
    PATH="$tmp/bin:$PATH" REPO_DIR="$REPO_DIR" \
      zsh -i -c '
        export PATH="'"$tmp"'/bin:$PATH"
        export REMOTE_DOTS_DIR="$REPO_DIR/dots"
        source "$REPO_DIR/lib/guards.sh"
        source "$REPO_DIR/lib/helpers.sh"
        source "$REPO_DIR/shell/rc.d/21-zoxide.sh"
        print -r -- "shell=${REMOTE_SSH_TEST_ZOXIDE_SHELL:-missing}"
        if whence -w z >/dev/null 2>&1; then
          print -r -- "z=function"
        else
          print -r -- "z=missing"
        fi
        if whence -w zi >/dev/null 2>&1; then
          print -r -- "zi=function"
        else
          print -r -- "zi=missing"
        fi
      ' 2>/dev/null
  )"

  grep -q '^shell=zsh$' <<<"$got"
  grep -q '^z=function$' <<<"$got"
  grep -q '^zi=function$' <<<"$got"

  trap - RETURN
  rm -rf "$tmp"
}

register_test test_zoxide_initializes_for_bash
register_test test_zoxide_initializes_for_zsh
