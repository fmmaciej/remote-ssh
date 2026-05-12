#!/usr/bin/env bash

test_remote_ssh_usage_and_unknown_command() {
  log "remote-ssh shows usage and rejects unknown commands"

  local got
  got="$(bash "$REPO_DIR/bin/remote-ssh" --help 2>&1)"
  assert_contains "remote-ssh usage" "Usage: remote-ssh <command> [args]" "$got"
  assert_contains "remote-ssh commands" "prune [--apply]" "$got"
  assert_contains "remote-ssh guide command" "guide [section]" "$got"
  assert_contains "remote-ssh git command" "git <command>" "$got"
  assert_contains "remote-ssh update command" "update [check]" "$got"
  assert_contains "remote-ssh install full command" "install --full [--yes]" "$got"
  assert_contains "remote-ssh tool list command" "tool list" "$got"

  got="$(bash "$REPO_DIR/bin/remote-ssh" help 2>&1)"
  assert_contains "remote-ssh help usage" "Usage: remote-ssh <command> [args]" "$got"
  assert_contains "remote-ssh help guide command" "guide [section]" "$got"

  got="$(bash "$REPO_DIR/bin/remote-ssh" help aliases 2>&1)" && {
    printf 'Expected remote-ssh help aliases to fail\n' >&2
    return 1
  }
  assert_contains "remote-ssh help aliases error" "remote-ssh help does not accept sections." "$got"
  assert_contains "remote-ssh help aliases hint" "Use: remote-ssh guide aliases" "$got"

  got="$(bash "$REPO_DIR/bin/remote-ssh" wat 2>&1)" && {
    printf 'Expected unknown command to fail\n' >&2
    return 1
  }
  assert_contains "remote-ssh unknown" "Unknown remote-ssh command: wat" "$got"
}

test_remote_ssh_guide_renders_commands_section() {
  log "remote-ssh guide renders commands section"

  local got
  got="$(bash "$REPO_DIR/bin/remote-ssh" guide commands)"

  assert_contains "remote-ssh guide commands" "Commands" "$got"
  assert_contains "remote-ssh guide command" "remote-ssh guide [section]  Show this configuration guide" "$got"
  assert_contains "remote-ssh check command" "remote-ssh check --strict   Report pinned tools vs local bin and PATH" "$got"
  assert_contains "remote-ssh tool list guide command" "remote-ssh tool list        Show tool selection and install state" "$got"
  assert_contains "remote-ssh git setup command" "remote-ssh git setup        Add remote-ssh Git config via include.path" "$got"
  assert_contains "remote-ssh update check command" "remote-ssh update check     Check whether upstream has changed" "$got"
}

test_remote_ssh_git_usage_and_unknown_command() {
  log "remote-ssh git shows usage and rejects unknown commands"

  local got
  got="$(bash "$REPO_DIR/bin/remote-ssh" git --help 2>&1)"
  assert_contains "remote-ssh git usage" "Usage: remote-ssh git <command> [args]" "$got"
  assert_contains "remote-ssh git setup" "setup" "$got"
  assert_contains "remote-ssh git status" "status [ssh-host]" "$got"

  got="$(bash "$REPO_DIR/bin/remote-ssh" git wat 2>&1)" && {
    printf 'Expected unknown git command to fail\n' >&2
    return 1
  }
  assert_contains "remote-ssh git unknown" "Unknown remote-ssh git command: wat" "$got"
}

test_remote_ssh_check_delegates_to_check_command() {
  log "remote-ssh check reports tool state"

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

  assert_contains "remote-ssh check title" "remote-ssh check" "$got"
  assert_contains "remote-ssh check status" "status:    ok" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

test_remote_ssh_tool_list_reports_tool_sets() {
  log "remote-ssh tool list reports tool sets"

  local tmp got
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/home" "$tmp/config/remote-ssh" "$tmp/bin" "$tmp/opt/rg-15.1.0"
  printf 'rg\nfd\n' >"$tmp/config/remote-ssh/expected-tools"
  printf '#!/usr/bin/env bash\nprintf rg\n' >"$tmp/opt/rg-15.1.0/rg"
  chmod +x "$tmp/opt/rg-15.1.0/rg"
  ln -s "$tmp/opt/rg-15.1.0/rg" "$tmp/bin/rg"

  got="$(
    HOME="$tmp/home" \
      XDG_CONFIG_HOME="$tmp/config" \
      INSTALL_PREFIX="$tmp/opt" \
      INSTALL_BIN_DIR="$tmp/bin" \
      PATH="$tmp/bin:/usr/bin:/bin" \
      bash "$REPO_DIR/bin/remote-ssh" tool list
  )"

  assert_contains "tool list title" "remote-ssh tool list" "$got"
  assert_contains "tool list default" "Default tools:" "$got"
  assert_contains "tool list expected" "Expected tools:" "$got"
  assert_contains "tool list expected rg" "  rg" "$got"
  assert_contains "tool list installed" "Managed installed tools:" "$got"
  assert_contains "tool list unsupported" "Unsupported default tools on this platform:" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

register_test test_remote_ssh_usage_and_unknown_command
register_test test_remote_ssh_guide_renders_commands_section
register_test test_remote_ssh_git_usage_and_unknown_command
register_test test_remote_ssh_check_delegates_to_check_command
register_test test_remote_ssh_tool_list_reports_tool_sets
