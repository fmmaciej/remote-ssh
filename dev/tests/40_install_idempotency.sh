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

register_test test_install_bin_idempotency
register_test test_install_bin_ignores_external_path_tool
register_test test_install_bin_reinstalls_stale_local_version
