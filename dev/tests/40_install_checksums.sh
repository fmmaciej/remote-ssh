#!/usr/bin/env bash
# shellcheck disable=SC2030,SC2031

test_verify_asset_checksum_accepts_match() {
  log "install accepts matching checksums"

  local tmp checksum
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  printf 'hello\n' >"$tmp/demo"
  checksum="5891b5b522d5df086d0ff0b110fbd9d21bb4fc7163af34d08286a2e846f6be03"

  (
    cd "$tmp" || exit
    # shellcheck source=/dev/null
    . "$REPO_DIR/tools/lib/env.sh"
    # shellcheck source=/dev/null
    . "$TOOLS_LIB_DIR/install-tool.lib.sh"
    verify_asset_checksum demo "$checksum"
  )

  trap - RETURN
  rm -rf "$tmp"
}

register_test test_verify_asset_checksum_accepts_match

test_verify_asset_checksum_rejects_mismatch() {
  log "install rejects checksum mismatches"

  local tmp got
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  printf 'hello\n' >"$tmp/demo"

  got="$(
    (
      cd "$tmp" || exit
      # shellcheck source=/dev/null
      . "$REPO_DIR/tools/lib/env.sh"
      # shellcheck source=/dev/null
      . "$TOOLS_LIB_DIR/install-tool.lib.sh"
      verify_asset_checksum demo 0000000000000000000000000000000000000000000000000000000000000000
    ) 2>&1
  )" && {
    printf 'Expected checksum mismatch to fail\n' >&2
    return 1
  }

  assert_contains "checksum mismatch" "Checksum mismatch for demo" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

register_test test_verify_asset_checksum_rejects_mismatch
