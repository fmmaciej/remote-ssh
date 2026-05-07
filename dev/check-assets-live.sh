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

live_checksum() {
  local repo="$1" tag="$2" asset="$3"
  local url="https://github.com/${repo}/releases/download/${tag}/${asset}.sha256"

  fetch_json "$url" |
    sed -n 's/^\([0-9a-fA-F]\{64\}\).*/\1/p' |
    tr '[:upper:]' '[:lower:]' |
    head -n1
}

release_asset_digest() {
  local json="$1" asset="$2"

  awk -v asset="$asset" '
    index($0, "\"name\": \"" asset "\"") { in_asset = 1 }
    in_asset && /"digest": "sha256:/ {
      digest = $0
      sub(/^.*"digest": "sha256:/, "", digest)
      sub(/".*$/, "", digest)
      print tolower(digest)
      exit
    }
    in_asset && /^[[:space:]]*}[,]?$/ { in_asset = 0 }
  ' <<<"$json"
}

check_def_assets() {
  :

  local tag="${RELEASE_TAG}"
  log "${TOOL_NAME}: ${GH_REPO}@${tag}"

  local json
  if ! json="$(release_json "$GH_REPO" "$tag")"; then
    printf 'Could not fetch GitHub release metadata for %s %s\n' "$GH_REPO" "$tag" >&2
    return 1
  fi

  local rec asset
  for rec in "${ASSETS[@]}"; do
    asset="$(manifest_asset_name "$rec")"
    check_asset_exists "$GH_REPO" "$tag" "$asset" "$json"
  done

  local expected got
  for rec in "${CHECKSUMS[@]}"; do
    asset="${rec%%|*}"
    expected="${rec#*|}"
    got="$(release_asset_digest "$json" "$asset")"
    if [[ -z $got ]] && ! got="$(live_checksum "$GH_REPO" "$tag" "$asset")"; then
      got=""
    fi
    if [[ -z $got ]]; then
      printf 'Could not fetch live checksum for %s %s: %s\n' "$GH_REPO" "$tag" "$asset" >&2
      return 1
    fi
    if [[ $got != "$expected" ]]; then
      printf 'Checksum mismatch for %s %s: %s\n' "$GH_REPO" "$tag" "$asset" >&2
      printf '  expected: %s\n' "$expected" >&2
      printf '  live:     %s\n' "$got" >&2
      return 1
    fi
  done
}

main() {
  require_cmd curl
  require_cmd grep
  require_cmd awk

  source_tool_libs

  local failed=0
  with_each_tool_def check_def_assets || failed=1

  ((failed == 0))
}

main "$@"
