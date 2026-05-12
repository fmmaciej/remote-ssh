#!/usr/bin/env bash

test_remote_ssh_doctor_reports_missing_tools() {
  log "remote-ssh doctor reports missing managed tools"

  local tmp got
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/home" "$tmp/config/remote-ssh" "$tmp/bin" "$tmp/opt"
  printf 'rg\n' >"$tmp/config/remote-ssh/expected-tools"

  got="$(
    HOME="$tmp/home" \
      XDG_CONFIG_HOME="$tmp/config" \
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

test_remote_ssh_doctor_reports_path_shadow_hint() {
  log "remote-ssh doctor reports PATH shadow hint"

  local tmp got
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/home" "$tmp/config/remote-ssh" "$tmp/bin" "$tmp/opt/rg-15.1.0" "$tmp/external"
  printf 'rg\n' >"$tmp/config/remote-ssh/expected-tools"
  printf '#!/usr/bin/env bash\nprintf managed-rg\n' >"$tmp/opt/rg-15.1.0/rg"
  chmod +x "$tmp/opt/rg-15.1.0/rg"
  ln -s "$tmp/opt/rg-15.1.0/rg" "$tmp/bin/rg"
  printf '#!/usr/bin/env bash\nprintf external-rg\n' >"$tmp/external/rg"
  chmod +x "$tmp/external/rg"

  got="$(
    HOME="$tmp/home" \
      XDG_CONFIG_HOME="$tmp/config" \
      INSTALL_PREFIX="$tmp/opt" \
      INSTALL_BIN_DIR="$tmp/bin" \
      PATH="$tmp/external:$tmp/bin:/usr/bin:/bin" \
      bash "$REPO_DIR/bin/remote-ssh" doctor
  )" && {
    printf 'Expected doctor to fail with path-shadowed tool\n' >&2
    return 1
  }

  assert_contains "doctor path shadow status" "status:    path-shadowed" "$got"
  assert_contains "doctor path shadow hint" "check PATH order: $tmp/bin should come before external tool directories" "$got"
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

test_remote_ssh_doctor_reports_missing_expected_tools_config() {
  log "remote-ssh doctor reports missing expected tools config"

  local tmp got
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/home" "$tmp/bin" "$tmp/opt"

  got="$(
    HOME="$tmp/home" \
      XDG_CONFIG_HOME="$tmp/config" \
      INSTALL_PREFIX="$tmp/opt" \
      INSTALL_BIN_DIR="$tmp/bin" \
      PATH="$tmp/bin:/usr/bin:/bin" \
      bash "$REPO_DIR/bin/remote-ssh" doctor
  )" && {
    printf 'Expected doctor to fail without expected tools config\n' >&2
    return 1
  }

  assert_contains "doctor missing expected config" "No expected tools config found:" "$got"
  assert_contains "doctor choose tools hint" "choose tools: remote-ssh install fd rg fzf" "$got"
  assert_contains "doctor full install hint" "remote-ssh install --full --yes" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

test_remote_ssh_doctor_reports_missing_binary_alias() {
  log "remote-ssh doctor reports missing binary alias"

  local tmp got
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/home" "$tmp/config/remote-ssh" "$tmp/bin" "$tmp/opt/nu-0.112.2"
  printf 'nu\n' >"$tmp/config/remote-ssh/expected-tools"
  printf '#!/usr/bin/env bash\nprintf nu\n' >"$tmp/opt/nu-0.112.2/nu"
  chmod +x "$tmp/opt/nu-0.112.2/nu"
  ln -s "$tmp/opt/nu-0.112.2/nu" "$tmp/bin/nu"

  got="$(
    HOME="$tmp/home" \
      XDG_CONFIG_HOME="$tmp/config" \
      INSTALL_PREFIX="$tmp/opt" \
      INSTALL_BIN_DIR="$tmp/bin" \
      PATH="$tmp/bin:/usr/bin:/bin" \
      bash "$REPO_DIR/bin/remote-ssh" doctor
  )" && {
    printf 'Expected doctor to fail with missing binary alias\n' >&2
    return 1
  }

  assert_contains "doctor alias status" "alias:     nushell -> [missing] status=missing target=[missing]" "$got"
  assert_contains "doctor alias install hint" "run: remote-ssh install" "$got"
  assert_contains "doctor alias inspect hint" "inspect: remote-ssh check --strict" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

register_test test_remote_ssh_doctor_reports_missing_tools
register_test test_remote_ssh_doctor_reports_path_shadow_hint
register_test test_remote_ssh_doctor_rejects_mismatched_remote_env_dir
register_test test_remote_ssh_doctor_reports_missing_expected_tools_config
register_test test_remote_ssh_doctor_reports_missing_binary_alias
