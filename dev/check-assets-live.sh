#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"

export SCRIPT_DIR REPO_DIR TEST_LOG_PREFIX="assets-live"

if [[ -f "$SCRIPT_DIR/.env" ]]; then
  set -a
  # shellcheck source=/dev/null
  . "$SCRIPT_DIR/.env"
  set +a
fi

# shellcheck disable=SC1091
. "$SCRIPT_DIR/tests/lib.sh"
# shellcheck disable=SC1091
. "$SCRIPT_DIR/tests/tool_assets_lib.sh"

release_json() {
  local repo="$1" tag="$2"
  local api="https://api.github.com/repos/${repo}/releases/tags/${tag}"

  fetch_json "$api"
}

check_asset_exists() {
  local repo="$1" tag="$2" asset="$3" json="$4"

  if github_parse_asset_names "$json" | grep -Fx -- "$asset" >/dev/null; then
    return 0
  fi

  printf 'Missing asset for %s %s: %s\n' "$repo" "$tag" "$asset" >&2
  return 1
}

check_def_assets() {
  :

  local tag="${TAG_PREFIX}${DEFAULT_VERSION}"
  log "${TOOL_NAME}: ${GH_REPO}@${tag}"

  local json
  if ! json="$(release_json "$GH_REPO" "$tag")"; then
    printf 'Could not fetch GitHub release metadata for %s %s\n' "$GH_REPO" "$tag" >&2
    return 1
  fi

  local rec asset
  for rec in "${VARIANTS[@]}"; do
    asset="$(variant_asset_name "$rec")"
    check_asset_exists "$GH_REPO" "$tag" "$asset" "$json"
  done
}

main() {
  require_cmd curl
  require_cmd grep

  source_tool_libs

  local failed=0
  with_each_tool_def check_def_assets || failed=1

  ((failed == 0))
}

main "$@"
