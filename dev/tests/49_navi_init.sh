#!/usr/bin/env bash

test_navi_init_sets_cheats_path() {
  log "navi rc plugin sets bundled cheats path"

  local tmp output
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/bin" "$tmp/repo/dots/navi/cheats" "$tmp/repo/shell/rc.d"
  cp "$REPO_DIR/shell/rc.d/24-navi.sh" "$tmp/repo/shell/rc.d/24-navi.sh"
  printf '#!/usr/bin/env bash\n' >"$tmp/bin/navi"
  chmod +x "$tmp/bin/navi"

  output="$(
    PATH="$tmp/bin:/usr/bin:/bin" \
      REMOTE_DOTS_DIR="$tmp/repo/dots" \
      bash -c '
        have() { command -v "$1" >/dev/null 2>&1; }
        ensure_this_file_sourced() { :; }
        source "$1"
        alias cheats
        printf "NAVI_PATH=%s\n" "$NAVI_PATH"
      ' _ "$tmp/repo/shell/rc.d/24-navi.sh"
  )"

  grep -q '^NAVI_PATH='"$tmp"'/repo/dots/navi/cheats$' <<<"$output"
  grep -q "^alias cheats='navi'$" <<<"$output"

  trap - RETURN
  rm -rf "$tmp"
}

test_navi_init_preserves_existing_cheats_path() {
  log "navi rc plugin preserves existing cheats path"

  local tmp output
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/repo/dots/navi/cheats" "$tmp/repo/shell/rc.d"
  cp "$REPO_DIR/shell/rc.d/24-navi.sh" "$tmp/repo/shell/rc.d/24-navi.sh"

  output="$(
    REMOTE_DOTS_DIR="$tmp/repo/dots" \
      NAVI_PATH="$tmp/personal" \
      bash -c '
        have() { return 1; }
        ensure_this_file_sourced() { :; }
        source "$1"
        printf "NAVI_PATH=%s\n" "$NAVI_PATH"
      ' _ "$tmp/repo/shell/rc.d/24-navi.sh"
  )"

  grep -q '^NAVI_PATH='"$tmp"'/repo/dots/navi/cheats:'"$tmp"'/personal$' <<<"$output"

  trap - RETURN
  rm -rf "$tmp"
}

register_test test_navi_init_sets_cheats_path
register_test test_navi_init_preserves_existing_cheats_path
