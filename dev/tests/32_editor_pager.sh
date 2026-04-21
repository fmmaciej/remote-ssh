#!/usr/bin/env bash
# shellcheck disable=SC2030,SC2031

test_editor_prefers_nvim_and_sets_visual() {
  log "editor setup prefers nvim"

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/bin"
  printf '#!/usr/bin/env bash\nexit 0\n' >"$tmp/bin/nvim"
  chmod +x "$tmp/bin/nvim"

  local got
  got="$(
    PATH="$tmp/bin:/usr/bin:/bin:/usr/sbin:/sbin" REPO_DIR="$REPO_DIR" \
      bash --noprofile --norc -ic '
        . "$REPO_DIR/lib/guards.sh"
        . "$REPO_DIR/lib/helpers.sh"
        . "$REPO_DIR/shell/rc.d/10-editor-pager.sh"
        printf "editor=%s\n" "${EDITOR:-missing}"
        printf "visual=%s\n" "${VISUAL:-missing}"
      ' 2>/dev/null
  )"

  grep -q '^editor=nvim$' <<<"$got"
  grep -q '^visual=nvim$' <<<"$got"

  trap - RETURN
  rm -rf "$tmp"
}

test_editor_warns_when_missing() {
  log "editor setup warns when no vim or nvim is available"

  local got
  got="$(
    PATH="/usr/bin:/bin:/usr/sbin:/sbin" REPO_DIR="$REPO_DIR" \
      bash --noprofile --norc -ic '
        have() { return 1; }
        . "$REPO_DIR/shell/rc.d/10-editor-pager.sh"
        printf "editor=%s\n" "${EDITOR:-missing}"
        printf "visual=%s\n" "${VISUAL:-missing}"
      ' 2>&1
  )"

  grep -q '^editor=missing$' <<<"$got"
  grep -q '^visual=missing$' <<<"$got"
  grep -q '^\[WARN\] No vim/nvim found in PATH\. Install one manually if you want an editor\.$' <<<"$got"
}

register_test test_editor_prefers_nvim_and_sets_visual
register_test test_editor_warns_when_missing
