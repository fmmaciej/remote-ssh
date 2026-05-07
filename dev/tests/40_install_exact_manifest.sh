#!/usr/bin/env bash
# shellcheck disable=SC2030,SC2031

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
