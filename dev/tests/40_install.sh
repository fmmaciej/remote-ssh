#!/usr/bin/env bash
# shellcheck disable=SC2030,SC2031

test_install_bin_idempotency() {
  log "install skips managed pinned version"

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/home" "$tmp/bin" "$tmp/opt/rg-15.1.0"
  printf '#!/usr/bin/env bash\n' >"$tmp/opt/rg-15.1.0/rg"
  chmod +x "$tmp/opt/rg-15.1.0/rg"
  ln -s "$tmp/opt/rg-15.1.0/rg" "$tmp/bin/rg"

  (
    export HOME="$tmp/home"
    export INSTALL_PREFIX="$tmp/opt"
    export INSTALL_BIN_DIR="$tmp/bin"
    cd "$REPO_DIR" || exit
    # shellcheck source=/dev/null
    . "$REPO_DIR/tools/lib/env.sh"
    # shellcheck source=/dev/null
    . "$TOOLS_LIB_DIR/install.lib.sh"
    is_tool_installed rg 15.1.0
  )

  trap - RETURN
  rm -rf "$tmp"
}

register_test test_install_bin_idempotency

test_install_bin_ignores_external_path_tool() {
  log "install does not skip external PATH tool"

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/home" "$tmp/bin" "$tmp/opt" "$tmp/external"
  printf '#!/usr/bin/env bash\n' >"$tmp/external/rg"
  chmod +x "$tmp/external/rg"

  (
    export HOME="$tmp/home"
    export INSTALL_PREFIX="$tmp/opt"
    export INSTALL_BIN_DIR="$tmp/bin"
    export PATH="$tmp/external:/usr/bin:/bin"
    cd "$REPO_DIR" || exit
    # shellcheck source=/dev/null
    . "$REPO_DIR/tools/lib/env.sh"
    # shellcheck source=/dev/null
    . "$TOOLS_LIB_DIR/install.lib.sh"
    ! is_tool_installed rg 15.1.0
  )

  trap - RETURN
  rm -rf "$tmp"
}

register_test test_install_bin_ignores_external_path_tool

test_install_bin_reinstalls_stale_local_version() {
  log "install does not skip stale local version"

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/home" "$tmp/bin" "$tmp/opt/rg-14.1.0"
  printf '#!/usr/bin/env bash\n' >"$tmp/opt/rg-14.1.0/rg"
  chmod +x "$tmp/opt/rg-14.1.0/rg"
  ln -s "$tmp/opt/rg-14.1.0/rg" "$tmp/bin/rg"

  (
    export HOME="$tmp/home"
    export INSTALL_PREFIX="$tmp/opt"
    export INSTALL_BIN_DIR="$tmp/bin"
    cd "$REPO_DIR" || exit
    # shellcheck source=/dev/null
    . "$REPO_DIR/tools/lib/env.sh"
    # shellcheck source=/dev/null
    . "$TOOLS_LIB_DIR/install.lib.sh"
    ! is_tool_installed rg 15.1.0
  )

  trap - RETURN
  rm -rf "$tmp"
}

register_test test_install_bin_reinstalls_stale_local_version

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

register_test test_default_tools_are_filtered_by_platform

test_install_binary_aliases() {
  log "install creates configured binary aliases"

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/home" "$tmp/bin" "$tmp/opt" "$tmp/extract/bin"
  printf '#!/usr/bin/env bash\n' >"$tmp/extract/bin/nu"
  chmod +x "$tmp/extract/bin/nu"

  (
    export HOME="$tmp/home"
    export INSTALL_PREFIX="$tmp/opt"
    export INSTALL_BIN_DIR="$tmp/bin"
    cd "$REPO_DIR" || exit
    # shellcheck source=/dev/null
    . "$REPO_DIR/tools/lib/env.sh"
    # shellcheck source=/dev/null
    . "$TOOLS_LIB_DIR/install-tool.lib.sh"
    install_binary nu nu 1.2.3 "$tmp/extract" nushell

    assert_eq "primary binary symlink" "$tmp/opt/nu-1.2.3/nu" "$(readlink "$tmp/bin/nu")"
    assert_eq "binary alias symlink" "$tmp/opt/nu-1.2.3/nu" "$(readlink "$tmp/bin/nushell")"
  )

  trap - RETURN
  rm -rf "$tmp"
}

register_test test_install_binary_aliases

test_install_binary_preserves_existing_version_on_failure() {
  log "install keeps existing version when replacement fails"

  local tmp got
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/home" "$tmp/bin" "$tmp/opt/demo-1.0.0" "$tmp/extract/bin"
  printf '#!/usr/bin/env bash\nprintf old\n' >"$tmp/opt/demo-1.0.0/demo"
  chmod +x "$tmp/opt/demo-1.0.0/demo"
  ln -s "$tmp/opt/demo-1.0.0/demo" "$tmp/bin/demo"

  printf '#!/usr/bin/env bash\nprintf new\n' >"$tmp/extract/bin/demo"
  chmod 111 "$tmp/extract/bin/demo"

  got="$(
    (
      export HOME="$tmp/home"
      export INSTALL_PREFIX="$tmp/opt"
      export INSTALL_BIN_DIR="$tmp/bin"
      cd "$REPO_DIR" || exit
      # shellcheck source=/dev/null
      . "$REPO_DIR/tools/lib/env.sh"
      # shellcheck source=/dev/null
      . "$TOOLS_LIB_DIR/install-tool.lib.sh"
      install_binary demo demo 1.0.0 "$tmp/extract"
    ) 2>&1
  )" && {
    printf 'Expected replacement install to fail\n' >&2
    return 1
  }

  assert_eq "existing symlink target" "$tmp/opt/demo-1.0.0/demo" "$(readlink "$tmp/bin/demo")"
  assert_eq "existing binary output" "old" "$("$tmp/bin/demo")"
  assert_contains "copy failure output" "Permission denied" "$got"

  chmod +r "$tmp/extract/bin/demo"
  trap - RETURN
  rm -rf "$tmp"
}

register_test test_install_binary_preserves_existing_version_on_failure
