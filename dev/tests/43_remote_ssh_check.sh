#!/usr/bin/env bash

test_remote_ssh_check_reports_local_tool() {
  log "remote-ssh check reports local tool state"

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
      bash "$REPO_DIR/bin/remote-ssh" check rg
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

test_remote_ssh_check_uses_expected_tools_by_default() {
  log "remote-ssh check uses expected tools by default"

  local tmp got
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/home" "$tmp/config/remote-ssh" "$tmp/bin" "$tmp/opt/rg-15.1.0"
  printf '# comment\n\nrg\n' >"$tmp/config/remote-ssh/expected-tools"
  printf '#!/usr/bin/env bash\nprintf rg\n' >"$tmp/opt/rg-15.1.0/rg"
  chmod +x "$tmp/opt/rg-15.1.0/rg"
  ln -s "$tmp/opt/rg-15.1.0/rg" "$tmp/bin/rg"

  got="$(
    HOME="$tmp/home" \
      XDG_CONFIG_HOME="$tmp/config" \
      INSTALL_PREFIX="$tmp/opt" \
      INSTALL_BIN_DIR="$tmp/bin" \
      PATH="$tmp/bin:/usr/bin:/bin" \
      bash "$REPO_DIR/bin/remote-ssh" check
  )"

  assert_contains "check expected tool" "rg" "$got"
  assert_contains "check expected status" "status:    ok" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

test_remote_ssh_check_reports_missing_expected_config() {
  log "remote-ssh check reports missing expected tools config"

  local tmp got
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  got="$(
    HOME="$tmp/home" \
      XDG_CONFIG_HOME="$tmp/config" \
      bash "$REPO_DIR/bin/remote-ssh" check 2>&1
  )" && {
    printf 'Expected check without expected tools to fail\n' >&2
    return 1
  }

  assert_contains "check missing expected config" "No expected tools config found:" "$got"
  assert_contains "check missing expected hint" "remote-ssh install --full --yes" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

test_remote_ssh_check_warns_about_unknown_expected_tool() {
  log "remote-ssh check warns about unknown expected tools"

  local tmp got
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/home" "$tmp/config/remote-ssh" "$tmp/bin" "$tmp/opt/rg-15.1.0"
  printf 'rg\noldtool\n' >"$tmp/config/remote-ssh/expected-tools"
  printf '#!/usr/bin/env bash\nprintf rg\n' >"$tmp/opt/rg-15.1.0/rg"
  chmod +x "$tmp/opt/rg-15.1.0/rg"
  ln -s "$tmp/opt/rg-15.1.0/rg" "$tmp/bin/rg"

  got="$(
    HOME="$tmp/home" \
      XDG_CONFIG_HOME="$tmp/config" \
      INSTALL_PREFIX="$tmp/opt" \
      INSTALL_BIN_DIR="$tmp/bin" \
      PATH="$tmp/bin:/usr/bin:/bin" \
      bash "$REPO_DIR/bin/remote-ssh" check
  )"

  assert_contains "check unknown expected warning" "unknown expected tool: oldtool" "$got"
  assert_contains "check still reports known tool" "status:    ok" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

test_remote_ssh_check_strict_rejects_external_only_tool() {
  log "remote-ssh check strict rejects external-only tool"

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
      bash "$REPO_DIR/bin/remote-ssh" check --strict rg
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
  log "remote-ssh check strict rejects stale local tool"

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
      bash "$REPO_DIR/bin/remote-ssh" check --strict rg
  )" && {
    printf 'Expected strict check to fail for stale local tool\n' >&2
    return 1
  }

  assert_contains "check stale status" "status:    stale-local" "$got"
  assert_contains "check stale target" "target:    $tmp/opt/rg-14.1.0/rg" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

test_remote_ssh_check_strict_accepts_binary_alias() {
  log "remote-ssh check strict accepts valid binary alias"

  local tmp got
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/home" "$tmp/bin" "$tmp/opt/nu-0.112.2"
  printf '#!/usr/bin/env bash\nprintf nu\n' >"$tmp/opt/nu-0.112.2/nu"
  chmod +x "$tmp/opt/nu-0.112.2/nu"
  ln -s "$tmp/opt/nu-0.112.2/nu" "$tmp/bin/nu"
  ln -s "$tmp/opt/nu-0.112.2/nu" "$tmp/bin/nushell"

  got="$(
    HOME="$tmp/home" \
      INSTALL_PREFIX="$tmp/opt" \
      INSTALL_BIN_DIR="$tmp/bin" \
      PATH="$tmp/bin:/usr/bin:/bin" \
      bash "$REPO_DIR/bin/remote-ssh" check --strict nu
  )"

  assert_contains "check alias ok" "alias:     nushell -> $tmp/bin/nushell status=ok target=$tmp/opt/nu-0.112.2/nu" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

test_remote_ssh_check_strict_rejects_missing_binary_alias() {
  log "remote-ssh check strict rejects missing binary alias"

  local tmp got
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/home" "$tmp/bin" "$tmp/opt/nu-0.112.2"
  printf '#!/usr/bin/env bash\nprintf nu\n' >"$tmp/opt/nu-0.112.2/nu"
  chmod +x "$tmp/opt/nu-0.112.2/nu"
  ln -s "$tmp/opt/nu-0.112.2/nu" "$tmp/bin/nu"

  got="$(
    HOME="$tmp/home" \
      INSTALL_PREFIX="$tmp/opt" \
      INSTALL_BIN_DIR="$tmp/bin" \
      PATH="$tmp/bin:/usr/bin:/bin" \
      bash "$REPO_DIR/bin/remote-ssh" check --strict nu
  )" && {
    printf 'Expected strict check to fail for missing alias\n' >&2
    return 1
  }

  assert_contains "check missing alias" "alias:     nushell -> [missing] status=missing target=[missing]" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

test_remote_ssh_check_strict_rejects_stale_binary_alias() {
  log "remote-ssh check strict rejects stale binary alias"

  local tmp got
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/home" "$tmp/bin" "$tmp/opt/nu-0.112.2" "$tmp/opt/nu-0.111.0"
  printf '#!/usr/bin/env bash\nprintf nu\n' >"$tmp/opt/nu-0.112.2/nu"
  printf '#!/usr/bin/env bash\nprintf old\n' >"$tmp/opt/nu-0.111.0/nu"
  chmod +x "$tmp/opt/nu-0.112.2/nu" "$tmp/opt/nu-0.111.0/nu"
  ln -s "$tmp/opt/nu-0.112.2/nu" "$tmp/bin/nu"
  ln -s "$tmp/opt/nu-0.111.0/nu" "$tmp/bin/nushell"

  got="$(
    HOME="$tmp/home" \
      INSTALL_PREFIX="$tmp/opt" \
      INSTALL_BIN_DIR="$tmp/bin" \
      PATH="$tmp/bin:/usr/bin:/bin" \
      bash "$REPO_DIR/bin/remote-ssh" check --strict nu
  )" && {
    printf 'Expected strict check to fail for stale alias\n' >&2
    return 1
  }

  assert_contains "check stale alias" "alias:     nushell -> $tmp/bin/nushell status=stale-local target=$tmp/opt/nu-0.111.0/nu" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

test_remote_ssh_check_strict_rejects_external_binary_alias() {
  log "remote-ssh check strict rejects external-only binary alias"

  local tmp got
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/home" "$tmp/bin" "$tmp/opt/nu-0.112.2" "$tmp/external"
  printf '#!/usr/bin/env bash\nprintf nu\n' >"$tmp/opt/nu-0.112.2/nu"
  printf '#!/usr/bin/env bash\nprintf external\n' >"$tmp/external/nushell"
  chmod +x "$tmp/opt/nu-0.112.2/nu" "$tmp/external/nushell"
  ln -s "$tmp/opt/nu-0.112.2/nu" "$tmp/bin/nu"

  got="$(
    HOME="$tmp/home" \
      INSTALL_PREFIX="$tmp/opt" \
      INSTALL_BIN_DIR="$tmp/bin" \
      PATH="$tmp/bin:$tmp/external:/usr/bin:/bin" \
      bash "$REPO_DIR/bin/remote-ssh" check --strict nu
  )" && {
    printf 'Expected strict check to fail for external alias\n' >&2
    return 1
  }

  assert_contains "check external alias" "alias:     nushell -> $tmp/external/nushell status=external-only target=[missing]" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

register_test test_remote_ssh_check_reports_local_tool
register_test test_remote_ssh_check_uses_expected_tools_by_default
register_test test_remote_ssh_check_reports_missing_expected_config
register_test test_remote_ssh_check_warns_about_unknown_expected_tool
register_test test_remote_ssh_check_strict_rejects_external_only_tool
register_test test_remote_ssh_check_strict_rejects_stale_local_tool
register_test test_remote_ssh_check_strict_accepts_binary_alias
register_test test_remote_ssh_check_strict_rejects_missing_binary_alias
register_test test_remote_ssh_check_strict_rejects_stale_binary_alias
register_test test_remote_ssh_check_strict_rejects_external_binary_alias
