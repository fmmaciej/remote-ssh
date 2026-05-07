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

make_fake_binary() {
  local path="$1"
  printf '#!/usr/bin/env bash\n' >"$path"
  chmod +x "$path"
}

test_stage_tar_gz_asset() {
  log "install stages .tar.gz assets"

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/src/bin" "$tmp/work"
  make_fake_binary "$tmp/src/bin/demo"
  tar -C "$tmp/src" -czf "$tmp/work/demo.tar.gz" .

  (
    cd "$tmp/work" || exit
    # shellcheck source=/dev/null
    . "$REPO_DIR/tools/lib/env.sh"
    # shellcheck source=/dev/null
    . "$TOOLS_LIB_DIR/install-tool.lib.sh"
    stage_downloaded_asset demo.tar.gz demo
    [[ -x "$tmp/work/bin/demo" ]]
  )

  trap - RETURN
  rm -rf "$tmp"
}

register_test test_stage_tar_gz_asset

test_stage_tgz_asset() {
  log "install stages .tgz assets"

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/src/bin" "$tmp/work"
  make_fake_binary "$tmp/src/bin/demo"
  tar -C "$tmp/src" -czf "$tmp/work/demo.tgz" .

  (
    cd "$tmp/work" || exit
    # shellcheck source=/dev/null
    . "$REPO_DIR/tools/lib/env.sh"
    # shellcheck source=/dev/null
    . "$TOOLS_LIB_DIR/install-tool.lib.sh"
    stage_downloaded_asset demo.tgz demo
    [[ -x "$tmp/work/bin/demo" ]]
  )

  trap - RETURN
  rm -rf "$tmp"
}

register_test test_stage_tgz_asset

test_stage_zip_asset() {
  log "install stages .zip assets"

  require_cmd zip
  require_cmd unzip

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/src/bin" "$tmp/work"
  make_fake_binary "$tmp/src/bin/demo"
  (
    cd "$tmp/src" || exit
    zip -qr "$tmp/work/demo.zip" .
  )

  (
    cd "$tmp/work" || exit
    # shellcheck source=/dev/null
    . "$REPO_DIR/tools/lib/env.sh"
    # shellcheck source=/dev/null
    . "$TOOLS_LIB_DIR/install-tool.lib.sh"
    # shellcheck disable=SC2034
    ZIP_SUPPORTED=1
    stage_downloaded_asset demo.zip demo
    [[ -x "$tmp/work/bin/demo" ]]
  )

  trap - RETURN
  rm -rf "$tmp"
}

register_test test_stage_zip_asset

test_stage_raw_executable_asset() {
  log "install stages raw executable assets"

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/work"
  printf '#!/usr/bin/env bash\n' >"$tmp/work/demo-linux-amd64"

  (
    cd "$tmp/work" || exit
    # shellcheck source=/dev/null
    . "$REPO_DIR/tools/lib/env.sh"
    # shellcheck source=/dev/null
    . "$TOOLS_LIB_DIR/install-tool.lib.sh"
    stage_downloaded_asset demo-linux-amd64 demo
    [[ -x "$tmp/work/demo" ]]
  )

  trap - RETURN
  rm -rf "$tmp"
}

register_test test_stage_raw_executable_asset

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

exact_manifest_error() {
  local req_version="$1" asset_key="$2"
  local tmp output status
  tmp="$(mktemp -d)"

  mkdir -p "$tmp/defs" "$tmp/tools"
  {
    printf '%s\n' '# shellcheck shell=bash'
    printf '%s\n' 'TOOL_NAME="exact"'
    printf '%s\n' 'GH_REPO="owner/repo"'
    printf '%s\n' 'RELEASE_TAG="v1.2.3"'
    printf '%s\n' 'VERSION="1.2.3"'
    printf '%s\n' 'BINARY_NAME="exact"'
    printf '%s\n' 'ASSETS=('
    printf '  "%s|exact.tar.gz"\n' "$asset_key"
    printf '%s\n' ')'
  } >"$tmp/defs/exact.sh"

  set +e
  output="$(
    (
      cd "$REPO_DIR" || exit
      # shellcheck source=/dev/null
      . "$REPO_DIR/tools/lib/env.sh"
      # shellcheck source=/dev/null
      . "$TOOLS_LIB_DIR/install-tool.lib.sh"
      install_tool_main "$tmp/tools" exact "$req_version"
    ) 2>&1
  )"
  status=$?
  set -e

  printf '%s\n' "$output"
  rm -rf "$tmp"
  return "$status"
}

test_exact_manifest_rejects_latest() {
  log "exact manifest rejects latest"

  local got
  if got="$(exact_manifest_error latest "darwin:aarch64:any")"; then
    printf 'Expected latest request to fail\n' >&2
    return 1
  fi
  assert_contains "latest error" "supports only VERSION=1.2.3" "$got"
  assert_contains "latest error" "requested 'latest'" "$got"
}

register_test test_exact_manifest_rejects_latest

test_exact_manifest_rejects_other_version() {
  log "exact manifest rejects other versions"

  local got
  if got="$(exact_manifest_error 9.9.9 "darwin:aarch64:any")"; then
    printf 'Expected foreign version request to fail\n' >&2
    return 1
  fi
  assert_contains "version error" "supports only VERSION=1.2.3" "$got"
  assert_contains "version error" "requested '9.9.9'" "$got"
}

register_test test_exact_manifest_rejects_other_version

test_exact_manifest_reports_missing_asset() {
  log "exact manifest reports missing asset"

  local got
  if got="$(exact_manifest_error "" "plan9:x86_64:any")"; then
    printf 'Expected unsupported platform to fail\n' >&2
    return 1
  fi
  assert_contains "missing asset error" "No matching asset for exact" "$got"
  assert_contains "missing asset error" "Available assets:" "$got"
  assert_contains "missing asset error" "plan9:x86_64:any|exact.tar.gz" "$got"
}

register_test test_exact_manifest_reports_missing_asset
