#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"

export SCRIPT_DIR REPO_DIR

# shellcheck disable=SC1091
. "$SCRIPT_DIR/tests/lib.sh"
# shellcheck disable=SC1091
. "$SCRIPT_DIR/tests/tool_assets_lib.sh"

for test_file in "$SCRIPT_DIR"/tests/*.sh; do
  case "$(basename "$test_file")" in
    lib.sh|tool_assets_lib.sh) continue ;;
  esac
  # shellcheck source=/dev/null
  . "$test_file"
done

for test_name in "${SMOKE_TESTS[@]}"; do
  "$test_name"
done

log "ok"
