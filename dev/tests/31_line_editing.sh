#!/usr/bin/env bash
# shellcheck disable=SC2030,SC2031

test_line_editing_uses_vi_mode_for_bash() {
  log "line editing uses vi mode for bash"

  local got
  got="$(
    REPO_DIR="$REPO_DIR" bash --noprofile --norc -ic '
      . "$REPO_DIR/lib/guards.sh"
      . "$REPO_DIR/shell/rc.d/11-line-editing.sh"
      set -o | awk '"'"'$1 == "vi" { print $2 }'"'"'
    ' 2>/dev/null
  )"

  assert_eq "bash vi editing mode" "on" "$got"
}

test_line_editing_uses_vi_mode_for_zsh() {
  if ! command -v zsh >/dev/null 2>&1; then
    log "SKIP: zsh not available"
    return 0
  fi

  log "line editing uses vi mode for zsh"

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  local log_file="$tmp/bindkey.log"
  local got
  got="$(
    REPO_DIR="$REPO_DIR" BINDKEY_LOG="$log_file" zsh -i -c '
      bindkey() {
        print -r -- "$*" >> "$BINDKEY_LOG"
        builtin bindkey "$@"
      }
      source "$REPO_DIR/lib/guards.sh"
      source "$REPO_DIR/shell/rc.d/11-line-editing.sh"
      if [[ -s "$BINDKEY_LOG" ]]; then
        cat "$BINDKEY_LOG"
      fi
    ' 2>/dev/null
  )"

  grep -q '^-v$' <<<"$got"

  trap - RETURN
  rm -rf "$tmp"
}

register_test test_line_editing_uses_vi_mode_for_bash
register_test test_line_editing_uses_vi_mode_for_zsh
