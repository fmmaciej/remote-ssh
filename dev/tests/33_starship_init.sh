#!/usr/bin/env bash
# shellcheck disable=SC2030,SC2031

test_starship_initializes_for_bash() {
  log "starship initializes for bash"

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/bin"

  cat >"$tmp/bin/starship" <<'EOF'
#!/usr/bin/env bash
if [[ "${1:-}" == "init" && "${2:-}" == "bash" ]]; then
  printf 'export REMOTE_SSH_TEST_STARSHIP_SHELL=bash\n'
  exit 0
fi
if [[ "${1:-}" == "init" && "${2:-}" == "zsh" ]]; then
  printf 'export REMOTE_SSH_TEST_STARSHIP_SHELL=zsh\n'
  exit 0
fi
exit 1
EOF
  chmod +x "$tmp/bin/starship"

  local got
  got="$(
    PATH="$tmp/bin:/usr/bin:/bin:/usr/sbin:/sbin" REPO_DIR="$REPO_DIR" \
      bash --noprofile --norc -ic '
        export REMOTE_DOTS_DIR="$REPO_DIR/dots"
        . "$REPO_DIR/lib/guards.sh"
        . "$REPO_DIR/lib/helpers.sh"
        . "$REPO_DIR/shell/rc.d/22-starship.sh"
        printf "shell=%s\n" "${REMOTE_SSH_TEST_STARSHIP_SHELL:-missing}"
        printf "config=%s\n" "${STARSHIP_CONFIG:-missing}"
      ' 2>/dev/null
  )"

  grep -q '^shell=bash$' <<<"$got"
  grep -q '^config='"$REPO_DIR"'/dots/starship.toml$' <<<"$got"

  trap - RETURN
  rm -rf "$tmp"
}

test_starship_initializes_for_zsh() {
  if ! command -v zsh >/dev/null 2>&1; then
    log "SKIP: zsh not available"
    return 0
  fi

  log "starship initializes for zsh"

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/bin"

  cat >"$tmp/bin/starship" <<'EOF'
#!/usr/bin/env bash
if [[ "${1:-}" == "init" && "${2:-}" == "bash" ]]; then
  printf 'export REMOTE_SSH_TEST_STARSHIP_SHELL=bash\n'
  exit 0
fi
if [[ "${1:-}" == "init" && "${2:-}" == "zsh" ]]; then
  printf 'export REMOTE_SSH_TEST_STARSHIP_SHELL=zsh\n'
  exit 0
fi
exit 1
EOF
  chmod +x "$tmp/bin/starship"

  local got
  got="$(
    PATH="$tmp/bin:$PATH" REPO_DIR="$REPO_DIR" \
      zsh -i -c '
        export PATH="'"$tmp"'/bin:$PATH"
        export REMOTE_DOTS_DIR="$REPO_DIR/dots"
        source "$REPO_DIR/lib/guards.sh"
        source "$REPO_DIR/lib/helpers.sh"
        source "$REPO_DIR/shell/rc.d/22-starship.sh"
        print -r -- "shell=${REMOTE_SSH_TEST_STARSHIP_SHELL:-missing}"
        print -r -- "config=${STARSHIP_CONFIG:-missing}"
      ' 2>/dev/null
  )"

  grep -q '^shell=zsh$' <<<"$got"
  grep -q '^config='"$REPO_DIR"'/dots/starship.toml$' <<<"$got"

  trap - RETURN
  rm -rf "$tmp"
}

register_test test_starship_initializes_for_bash
register_test test_starship_initializes_for_zsh
