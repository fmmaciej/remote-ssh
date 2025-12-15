#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=/dev/null
. "$SCRIPT_DIR/lib/env.sh"

# shellcheck source=/dev/null
. "$TOOLS_LIB_DIR/installer.lib.sh"

usage() {
  echo "Usage: $0 <tool> [version|latest]" >&2
  exit 1
}

main() {
  local tool="${1:-}"
  local ver="${2:-}"

  [[ -n "$tool" ]] || usage

  install_tool_main "$SCRIPT_DIR" "$tool" "$ver"
}

main "$@"
