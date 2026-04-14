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
