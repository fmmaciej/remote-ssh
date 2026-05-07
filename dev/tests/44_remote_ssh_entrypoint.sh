#!/usr/bin/env bash

test_remote_ssh_usage_and_unknown_command() {
  log "remote-ssh shows usage and rejects unknown commands"

  local got
  got="$(bash "$REPO_DIR/bin/remote-ssh" --help 2>&1)"
  assert_contains "remote-ssh usage" "Usage: remote-ssh <command> [args]" "$got"
  assert_contains "remote-ssh commands" "prune [--apply]" "$got"
  assert_contains "remote-ssh guide command" "guide [section]" "$got"

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

test_remote_ssh_guide_delegates_to_guide_command() {
  log "remote-ssh guide delegates to remote-ssh-guide"

  local got
  got="$(bash "$REPO_DIR/bin/remote-ssh" guide commands)"

  assert_contains "remote-ssh guide commands" "Commands" "$got"
  assert_contains "remote-ssh guide command" "remote-ssh guide [section]  Show this configuration guide" "$got"
  assert_contains "remote-ssh check command" "remote-ssh check --strict   Report pinned tools vs local bin and PATH" "$got"
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

test_remote_ssh_doctor_reports_missing_tools() {
  log "remote-ssh doctor reports missing managed tools"

  local tmp got
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/home" "$tmp/bin" "$tmp/opt"

  got="$(
    HOME="$tmp/home" \
      INSTALL_PREFIX="$tmp/opt" \
      INSTALL_BIN_DIR="$tmp/bin" \
      PATH="$tmp/bin:/usr/bin:/bin" \
      bash "$REPO_DIR/bin/remote-ssh" doctor
  )" && {
    printf 'Expected doctor to fail with missing tools\n' >&2
    return 1
  }

  assert_contains "doctor title" "remote-ssh doctor" "$got"
  assert_contains "doctor path" "status: ok" "$got"
  assert_contains "doctor repo" "Repository" "$got"
  assert_contains "doctor branch" "branch:" "$got"
  assert_contains "doctor commit" "commit:" "$got"
  assert_contains "doctor dirty" "dirty:" "$got"
  assert_contains "doctor rc" "Shell rc" "$got"
  assert_contains "doctor rc file" "shell/rc.sh" "$got"
  assert_contains "doctor rc status" "status: ok" "$got"
  assert_contains "doctor optional" "Optional helpers" "$got"
  assert_contains "doctor python" "sshf python3:" "$got"
  assert_contains "doctor check" "Tool check" "$got"
  assert_contains "doctor failed" "summary: failed" "$got"
  assert_contains "doctor next steps" "Next steps" "$got"
  assert_contains "doctor install hint" "run: remote-ssh install" "$got"
  assert_contains "doctor inspect hint" "inspect: remote-ssh check --strict" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

test_remote_ssh_doctor_rejects_mismatched_remote_env_dir() {
  log "remote-ssh doctor rejects mismatched REMOTE_ENV_DIR"

  local tmp got
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/home" "$tmp/bin" "$tmp/opt" "$tmp/other"

  got="$(
    HOME="$tmp/home" \
      REMOTE_ENV_DIR="$tmp/other" \
      INSTALL_PREFIX="$tmp/opt" \
      INSTALL_BIN_DIR="$tmp/bin" \
      PATH="$tmp/bin:/usr/bin:/bin" \
      bash "$REPO_DIR/bin/remote-ssh" doctor
  )" && {
    printf 'Expected doctor to fail with mismatched REMOTE_ENV_DIR\n' >&2
    return 1
  }

  assert_contains "doctor env mismatch" "env status: mismatch" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

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

register_test test_remote_ssh_usage_and_unknown_command
register_test test_remote_ssh_guide_delegates_to_guide_command
register_test test_remote_ssh_check_delegates_to_check_command
register_test test_remote_ssh_doctor_reports_missing_tools
register_test test_remote_ssh_doctor_rejects_mismatched_remote_env_dir
register_test test_remote_ssh_prune_dry_run_keeps_candidates
register_test test_remote_ssh_prune_apply_removes_only_candidates
