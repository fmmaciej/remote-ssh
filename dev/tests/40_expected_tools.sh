#!/usr/bin/env bash
# shellcheck disable=SC2030,SC2031,SC2329

test_default_tools_are_filtered_by_platform() {
  log "default tools are filtered by platform asset support"

  local got unsupported
  got="$(
    cd "$REPO_DIR" || exit
    # shellcheck source=/dev/null
    . "$REPO_DIR/tools/lib/env.sh"
    # shellcheck source=/dev/null
    . "$TOOLS_LIB_DIR/install.lib.sh"
    default_tools_for_platform darwin aarch64 any
  )"
  unsupported="$(
    cd "$REPO_DIR" || exit
    # shellcheck source=/dev/null
    . "$REPO_DIR/tools/lib/env.sh"
    # shellcheck source=/dev/null
    . "$TOOLS_LIB_DIR/install.lib.sh"
    unsupported_default_tools_for_platform darwin aarch64 any
  )"

  grep -Fxq 'fd' <<<"$got"
  grep -Fxq 'vector' <<<"$got"
  grep -Fxq 'zellij' <<<"$got"
  if grep -Fxq 'eza' <<<"$got"; then
    printf 'Expected eza to be unsupported on darwin/aarch64\n' >&2
    return 1
  fi
  if grep -Fxq 'dust' <<<"$got"; then
    printf 'Expected dust to be unsupported on darwin/aarch64\n' >&2
    return 1
  fi

  grep -Fxq 'eza' <<<"$unsupported"
  grep -Fxq 'dust' <<<"$unsupported"
  if grep -Fxq 'vector' <<<"$unsupported"; then
    printf 'Expected vector to be supported on darwin/aarch64\n' >&2
    return 1
  fi
}

test_expected_tools_read_write_config() {
  log "expected tools config is read and written"

  local tmp got file
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  got="$(
    export HOME="$tmp/home"
    export XDG_CONFIG_HOME="$tmp/config"
    cd "$REPO_DIR" || exit
    # shellcheck source=/dev/null
    . "$REPO_DIR/tools/lib/env.sh"
    # shellcheck source=/dev/null
    . "$TOOLS_LIB_DIR/install.lib.sh"
    write_expected_tools fd rg
    {
      printf '# comment\n'
      printf '\n'
      printf '  fzf  # inline comment\n'
    } >>"$(expected_tools_file)"
    read_expected_tools
  )"

  assert_eq "expected tools config" $'fd\nrg\nfzf' "$got"
  file="$tmp/config/remote-ssh/expected-tools"
  [[ -f "$file" ]] || {
    printf 'Expected config file to exist: %s\n' "$file" >&2
    return 1
  }

  trap - RETURN
  rm -rf "$tmp"
}

test_install_command_saves_selected_expected_tools() {
  log "remote-ssh install selected tools saves expected tools"

  local tmp got
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  got="$(
    export HOME="$tmp/home"
    export XDG_CONFIG_HOME="$tmp/config"
    export INSTALL_PREFIX="$tmp/opt"
    export INSTALL_BIN_DIR="$tmp/bin"
    cd "$REPO_DIR" || exit
    # shellcheck source=/dev/null
    . "$REPO_DIR/tools/lib/env.sh"
    # shellcheck source=/dev/null
    . "$TOOLS_LIB_DIR/commands.lib.sh"
    remote_ssh_cmd_require_install_libs
    install_check_requirements() { :; }
    install_tools() { printf '%s\n' "$@" >"$tmp/installed"; }
    install_shell_dir() { :; }
    install_bin_dir() { :; }
    install_dots_dir() { :; }
    install_print_post_install() { :; }
    remote_ssh_cmd_install_main "$REPO_DIR" --yes fd rg >/dev/null
    printf 'installed=%s\n' "$(tr '\n' ' ' <"$tmp/installed" | sed 's/[[:space:]]$//')"
    printf 'expected=%s\n' "$(grep -v '^#' "$(expected_tools_file)" | tr '\n' ' ' | sed 's/[[:space:]]$//')"
  )"

  assert_contains "selected installed tools" "installed=fd rg" "$got"
  assert_contains "selected expected tools" "expected=fd rg" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

test_install_selected_requires_confirmation() {
  log "remote-ssh install selected tools requires confirmation"

  local tmp got
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  got="$(
    export HOME="$tmp/home"
    export XDG_CONFIG_HOME="$tmp/config"
    export INSTALL_PREFIX="$tmp/opt"
    export INSTALL_BIN_DIR="$tmp/bin"
    cd "$REPO_DIR" || exit
    # shellcheck source=/dev/null
    . "$REPO_DIR/tools/lib/env.sh"
    # shellcheck source=/dev/null
    . "$TOOLS_LIB_DIR/commands.lib.sh"
    remote_ssh_cmd_require_install_libs
    install_check_requirements() { :; }
    install_tools() { printf '%s\n' "$@" >"$tmp/installed"; }
    remote_ssh_cmd_install_main "$REPO_DIR" fd rg 2>&1
  )" && {
    printf 'Expected selected install without tty confirmation to fail\n' >&2
    return 1
  }

  assert_contains "selected confirmation" "requires confirmation" "$got"
  if [[ -e "$tmp/installed" ]]; then
    printf 'Expected selected install not to run install_tools without confirmation\n' >&2
    return 1
  fi
  if [[ -e "$tmp/config/remote-ssh/expected-tools" ]]; then
    printf 'Expected selected install not to write expected tools without confirmation\n' >&2
    return 1
  fi

  trap - RETURN
  rm -rf "$tmp"
}

test_install_command_skips_unsupported_tools() {
  log "remote-ssh install skips unsupported tools and reports them"

  local tmp got expected_file
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  got="$(
    export HOME="$tmp/home"
    export XDG_CONFIG_HOME="$tmp/config"
    export INSTALL_PREFIX="$tmp/opt"
    export INSTALL_BIN_DIR="$tmp/bin"
    cd "$REPO_DIR" || exit
    # shellcheck source=/dev/null
    . "$REPO_DIR/tools/lib/env.sh"
    # shellcheck source=/dev/null
    . "$TOOLS_LIB_DIR/commands.lib.sh"
    remote_ssh_cmd_require_install_libs
    detect_platform() { printf 'darwin|aarch64\n'; }
    detect_libc() { printf 'any\n'; }
    install_check_requirements() { :; }
    install_tools() { printf '%s\n' "$@" >"$tmp/installed"; }
    install_shell_dir() { :; }
    install_bin_dir() { :; }
    install_dots_dir() { :; }
    install_print_post_install() { :; }
    remote_ssh_cmd_install_main "$REPO_DIR" --yes fd eza
  )"

  assert_contains "unsupported report" "Skipped unsupported tools:" "$got"
  assert_contains "unsupported tool" "eza" "$got"
  assert_eq "installed supported tools" "fd" "$(cat "$tmp/installed")"
  expected_file="$tmp/config/remote-ssh/expected-tools"
  assert_contains "expected supported tool" "fd" "$(cat "$expected_file")"
  if grep -Fxq 'eza' "$expected_file"; then
    printf 'Expected unsupported tool not to be saved\n' >&2
    return 1
  fi

  trap - RETURN
  rm -rf "$tmp"
}

test_install_without_expected_tools_reports_next_step() {
  log "remote-ssh install without expected tools reports next step"

  local tmp got
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  got="$(
    export HOME="$tmp/home"
    export XDG_CONFIG_HOME="$tmp/config"
    cd "$REPO_DIR" || exit
    # shellcheck source=/dev/null
    . "$REPO_DIR/tools/lib/env.sh"
    # shellcheck source=/dev/null
    . "$TOOLS_LIB_DIR/commands.lib.sh"
    remote_ssh_cmd_require_install_libs
    install_check_requirements() { :; }
    remote_ssh_cmd_install_main "$REPO_DIR" 2>&1
  )" && {
    printf 'Expected install without expected tools to fail\n' >&2
    return 1
  }

  assert_contains "missing expected config" "No expected tools config found:" "$got"
  assert_contains "missing expected hint" "remote-ssh install --full --yes" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

test_install_full_requires_confirmation() {
  log "remote-ssh install --full requires confirmation"

  local tmp got
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  got="$(
    export HOME="$tmp/home"
    export XDG_CONFIG_HOME="$tmp/config"
    cd "$REPO_DIR" || exit
    # shellcheck source=/dev/null
    . "$REPO_DIR/tools/lib/env.sh"
    # shellcheck source=/dev/null
    . "$TOOLS_LIB_DIR/commands.lib.sh"
    remote_ssh_cmd_require_install_libs
    install_check_requirements() { :; }
    remote_ssh_cmd_install_main "$REPO_DIR" --full 2>&1
  )" && {
    printf 'Expected install --full without tty confirmation to fail\n' >&2
    return 1
  }

  assert_contains "full confirmation" "requires confirmation" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

test_install_full_yes_saves_supported_defaults() {
  log "remote-ssh install --full --yes saves supported defaults"

  local tmp got expected
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  got="$(
    export HOME="$tmp/home"
    export XDG_CONFIG_HOME="$tmp/config"
    export INSTALL_PREFIX="$tmp/opt"
    export INSTALL_BIN_DIR="$tmp/bin"
    cd "$REPO_DIR" || exit
    # shellcheck source=/dev/null
    . "$REPO_DIR/tools/lib/env.sh"
    # shellcheck source=/dev/null
    . "$TOOLS_LIB_DIR/commands.lib.sh"
    remote_ssh_cmd_require_install_libs
    install_check_requirements() { :; }
    install_tools() { printf '%s\n' "$@" >"$tmp/installed"; }
    install_shell_dir() { :; }
    install_bin_dir() { :; }
    install_dots_dir() { :; }
    install_print_post_install() { :; }
    remote_ssh_cmd_install_main "$REPO_DIR" --full --yes >/dev/null
    cat "$tmp/installed"
  )"
  expected="$(
    cd "$REPO_DIR" || exit
    # shellcheck source=/dev/null
    . "$REPO_DIR/tools/lib/env.sh"
    # shellcheck source=/dev/null
    . "$TOOLS_LIB_DIR/install.lib.sh"
    current_default_tools
  )"

  assert_eq "full supported defaults" "$expected" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

test_install_expected_tools_does_not_require_confirmation() {
  log "remote-ssh install saved expected tools does not require confirmation"

  local tmp got
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  got="$(
    export HOME="$tmp/home"
    export XDG_CONFIG_HOME="$tmp/config"
    export INSTALL_PREFIX="$tmp/opt"
    export INSTALL_BIN_DIR="$tmp/bin"
    cd "$REPO_DIR" || exit
    # shellcheck source=/dev/null
    . "$REPO_DIR/tools/lib/env.sh"
    # shellcheck source=/dev/null
    . "$TOOLS_LIB_DIR/commands.lib.sh"
    remote_ssh_cmd_require_install_libs
    write_expected_tools fd rg
    install_check_requirements() { :; }
    install_tools() { printf '%s\n' "$@" >"$tmp/installed"; }
    install_shell_dir() { :; }
    install_bin_dir() { :; }
    install_dots_dir() { :; }
    install_print_post_install() { :; }
    remote_ssh_cmd_install_main "$REPO_DIR" >/dev/null
    cat "$tmp/installed"
  )"

  assert_eq "expected tools install" $'fd\nrg' "$got"

  trap - RETURN
  rm -rf "$tmp"
}

test_tool_install_does_not_change_expected_tools() {
  log "remote-ssh tool install does not change expected tools"

  local tmp got
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  got="$(
    export HOME="$tmp/home"
    export XDG_CONFIG_HOME="$tmp/config"
    export INSTALL_PREFIX="$tmp/opt"
    export INSTALL_BIN_DIR="$tmp/bin"
    cd "$REPO_DIR" || exit
    # shellcheck source=/dev/null
    . "$REPO_DIR/tools/lib/env.sh"
    # shellcheck source=/dev/null
    . "$TOOLS_LIB_DIR/commands.lib.sh"
    remote_ssh_cmd_require_install_libs
    write_expected_tools fd rg
    install_check_requirements() { :; }
    install_tools() { printf '%s\n' "$@" >"$tmp/tool-installed"; }
    remote_ssh_cmd_tool_main install fzf >/dev/null
    read_expected_tools
  )"

  assert_eq "expected tools after tool install" $'fd\nrg' "$got"

  trap - RETURN
  rm -rf "$tmp"
}

register_test test_default_tools_are_filtered_by_platform
register_test test_expected_tools_read_write_config
register_test test_install_command_saves_selected_expected_tools
register_test test_install_selected_requires_confirmation
register_test test_install_command_skips_unsupported_tools
register_test test_install_without_expected_tools_reports_next_step
register_test test_install_full_requires_confirmation
register_test test_install_full_yes_saves_supported_defaults
register_test test_install_expected_tools_does_not_require_confirmation
register_test test_tool_install_does_not_change_expected_tools
