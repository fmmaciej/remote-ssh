#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=/dev/null
. "$SCRIPT_DIR/lib/env.sh"

if [[ -f "$REPO_DIR/dev/.env" ]]; then
  set -a
  # shellcheck source=/dev/null
  . "$REPO_DIR/dev/.env"
  set +a
fi

# shellcheck source=/dev/null
. "$TOOLS_LIB_DIR/generate-def.lib.sh"

usage() {
  echo "Usage: $0 <owner>/<name> <name>" >&2
  exit 1
}

main() {
  local repo="${1:?owner/repo required}"
  local tool="${2:?tool name required}"

  github_latest_release "$repo"

  # echo "ASSETS count: ${#GITHUB_ASSETS[@]}" >&2
  # printf '  - [%s]\n' "${GITHUB_ASSETS[@]}" >&2

  tag_prefix_and_version "$GITHUB_TAG"

  detect_asset_prefix "$tool" "$VERSION" "${GITHUB_ASSETS[@]}"

  build_assets_from_assets "${GITHUB_ASSETS[@]}"
  render_defs "$tool" "$repo" "$GITHUB_TAG"
}

main "$@"
