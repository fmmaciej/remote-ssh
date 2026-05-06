#!/usr/bin/env bash
# shellcheck disable=SC2030,SC2031

test_install_bin_idempotency() {
  log "install checks INSTALL_BIN_DIR"

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/home" "$tmp/bin" "$tmp/opt"
  printf '#!/usr/bin/env bash\n' >"$tmp/bin/rg"
  chmod +x "$tmp/bin/rg"

  (
    export HOME="$tmp/home"
    export INSTALL_PREFIX="$tmp/opt"
    export INSTALL_BIN_DIR="$tmp/bin"
    cd "$REPO_DIR" || exit
    # shellcheck source=/dev/null
    . "$REPO_DIR/tools/lib/env.sh"
    # shellcheck source=/dev/null
    . "$TOOLS_LIB_DIR/install.lib.sh"
    is_tool_installed rg
  )

  trap - RETURN
  rm -rf "$tmp"
}

register_test test_install_bin_idempotency

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
