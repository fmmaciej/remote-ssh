#!/usr/bin/env bash

test_remote_ssh_prune_dry_run_keeps_candidates() {
  log "remote-ssh prune dry-run reports candidates"

  local tmp got
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/home" "$tmp/bin" "$tmp/opt/rg-15.1.0" "$tmp/opt/rg-14.1.0" "$tmp/opt/not-a-tool-1.0.0"
  printf '#!/usr/bin/env bash\nprintf rg\n' >"$tmp/opt/rg-15.1.0/rg"
  chmod +x "$tmp/opt/rg-15.1.0/rg"
  ln -s "$tmp/opt/rg-15.1.0/rg" "$tmp/bin/rg"

  got="$(
    HOME="$tmp/home" \
      INSTALL_PREFIX="$tmp/opt" \
      INSTALL_BIN_DIR="$tmp/bin" \
      PATH="$tmp/bin:/usr/bin:/bin" \
      bash "$REPO_DIR/bin/remote-ssh" prune
  )"

  assert_contains "prune dry run" "remote-ssh prune (dry-run)" "$got"
  assert_contains "prune candidate" "candidate: $tmp/opt/rg-14.1.0" "$got"
  [[ -d "$tmp/opt/rg-14.1.0" ]]
  [[ -d "$tmp/opt/rg-15.1.0" ]]
  [[ -d "$tmp/opt/not-a-tool-1.0.0" ]]

  trap - RETURN
  rm -rf "$tmp"
}

test_remote_ssh_prune_apply_removes_only_candidates() {
  log "remote-ssh prune apply removes only candidates"

  local tmp got
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/home" "$tmp/bin" "$tmp/opt/rg-15.1.0" "$tmp/opt/rg-14.1.0" "$tmp/opt/not-a-tool-1.0.0"
  printf '#!/usr/bin/env bash\nprintf rg\n' >"$tmp/opt/rg-15.1.0/rg"
  chmod +x "$tmp/opt/rg-15.1.0/rg"
  ln -s "$tmp/opt/rg-15.1.0/rg" "$tmp/bin/rg"

  got="$(
    HOME="$tmp/home" \
      INSTALL_PREFIX="$tmp/opt" \
      INSTALL_BIN_DIR="$tmp/bin" \
      PATH="$tmp/bin:/usr/bin:/bin" \
      bash "$REPO_DIR/bin/remote-ssh" prune --apply
  )"

  assert_contains "prune apply" "remote-ssh prune --apply" "$got"
  assert_contains "prune removed" "removed: $tmp/opt/rg-14.1.0" "$got"
  [[ ! -e "$tmp/opt/rg-14.1.0" ]]
  [[ -d "$tmp/opt/rg-15.1.0" ]]
  [[ -d "$tmp/opt/not-a-tool-1.0.0" ]]

  trap - RETURN
  rm -rf "$tmp"
}

test_remote_ssh_prune_preserves_relative_symlink_target() {
  log "remote-ssh prune preserves relative symlink target"

  local tmp got
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/home" "$tmp/bin" "$tmp/opt/rg-15.1.0" "$tmp/opt/rg-14.1.0"
  printf '#!/usr/bin/env bash\nprintf rg\n' >"$tmp/opt/rg-15.1.0/rg"
  chmod +x "$tmp/opt/rg-15.1.0/rg"
  (
    cd "$tmp/bin" || exit
    ln -s "../opt/rg-15.1.0/rg" rg
  )

  got="$(
    HOME="$tmp/home" \
      INSTALL_PREFIX="$tmp/opt" \
      INSTALL_BIN_DIR="$tmp/bin" \
      PATH="$tmp/bin:/usr/bin:/bin" \
      bash "$REPO_DIR/bin/remote-ssh" prune --apply
  )"

  assert_contains "prune apply" "remote-ssh prune --apply" "$got"
  assert_contains "prune removed" "removed: $tmp/opt/rg-14.1.0" "$got"
  [[ ! -e "$tmp/opt/rg-14.1.0" ]]
  [[ -d "$tmp/opt/rg-15.1.0" ]]

  trap - RETURN
  rm -rf "$tmp"
}

register_test test_remote_ssh_prune_dry_run_keeps_candidates
register_test test_remote_ssh_prune_apply_removes_only_candidates
register_test test_remote_ssh_prune_preserves_relative_symlink_target
