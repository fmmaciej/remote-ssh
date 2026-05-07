#!/usr/bin/env bash

test_remote_ssh_check_reports_local_tool() {
  log "remote-ssh-check reports local tool state"

  local tmp got
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/home" "$tmp/bin" "$tmp/opt/rg-15.1.0"
  printf '#!/usr/bin/env bash\nprintf rg\n' >"$tmp/opt/rg-15.1.0/rg"
  chmod +x "$tmp/opt/rg-15.1.0/rg"
  ln -s "$tmp/opt/rg-15.1.0/rg" "$tmp/bin/rg"

  got="$(
    HOME="$tmp/home" \
      INSTALL_PREFIX="$tmp/opt" \
      INSTALL_BIN_DIR="$tmp/bin" \
      PATH="$tmp/bin:/usr/bin:/bin" \
      bash "$REPO_DIR/bin/remote-ssh-check" rg
  )"

  assert_contains "check title" "remote-ssh check" "$got"
  assert_contains "check expected" "VERSION=15.1.0 BurntSushi/ripgrep@15.1.0" "$got"
  assert_contains "check local" "local:     $tmp/bin/rg" "$got"
  assert_contains "check target" "target:    $tmp/opt/rg-15.1.0/rg" "$got"
  assert_contains "check path" "path:      $tmp/bin/rg" "$got"
  assert_contains "check status" "status:    ok" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

test_remote_ssh_check_strict_rejects_external_only_tool() {
  log "remote-ssh-check strict rejects external-only tool"

  local tmp got
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/home" "$tmp/bin" "$tmp/opt" "$tmp/external"
  printf '#!/usr/bin/env bash\nprintf rg\n' >"$tmp/external/rg"
  chmod +x "$tmp/external/rg"

  got="$(
    HOME="$tmp/home" \
      INSTALL_PREFIX="$tmp/opt" \
      INSTALL_BIN_DIR="$tmp/bin" \
      PATH="$tmp/external:/usr/bin:/bin" \
      bash "$REPO_DIR/bin/remote-ssh-check" --strict rg
  )" && {
    printf 'Expected strict check to fail for external-only tool\n' >&2
    return 1
  }

  assert_contains "check external status" "status:    external-only" "$got"
  assert_contains "check external path" "path:      $tmp/external/rg" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

test_remote_ssh_check_strict_rejects_stale_local_tool() {
  log "remote-ssh-check strict rejects stale local tool"

  local tmp got
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/home" "$tmp/bin" "$tmp/opt/rg-14.1.0"
  printf '#!/usr/bin/env bash\nprintf rg\n' >"$tmp/opt/rg-14.1.0/rg"
  chmod +x "$tmp/opt/rg-14.1.0/rg"
  ln -s "$tmp/opt/rg-14.1.0/rg" "$tmp/bin/rg"

  got="$(
    HOME="$tmp/home" \
      INSTALL_PREFIX="$tmp/opt" \
      INSTALL_BIN_DIR="$tmp/bin" \
      PATH="$tmp/bin:/usr/bin:/bin" \
      bash "$REPO_DIR/bin/remote-ssh-check" --strict rg
  )" && {
    printf 'Expected strict check to fail for stale local tool\n' >&2
    return 1
  }

  assert_contains "check stale status" "status:    stale-local" "$got"
  assert_contains "check stale target" "target:    $tmp/opt/rg-14.1.0/rg" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

register_test test_remote_ssh_check_reports_local_tool
register_test test_remote_ssh_check_strict_rejects_external_only_tool
register_test test_remote_ssh_check_strict_rejects_stale_local_tool
