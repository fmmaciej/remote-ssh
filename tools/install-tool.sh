#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
. "$SCRIPT_DIR/lib/env.sh"
# shellcheck source=/dev/null
. "$TOOLS_LIB_DIR/install-tool.lib.sh"

main() {
  local tool="${1:-}" requested="${2:-}"
  (($# >= 1 && $# <= 2)) && [[ "$tool" =~ ^[a-zA-Z0-9_][a-zA-Z0-9_.+-]*$ && -f "$TOOLS_DIR/defs/$tool.sh" ]] || {
    printf 'Usage: tools/install-tool.sh TOOL [PINNED_VERSION]\n' >&2; return 1;
  }
  load_defs "$TOOLS_DIR/defs" "$tool" || return 1
  if [[ -n "$requested" && "$requested" != "$VERSION" ]]; then
    printf "Tool '%s' supports only pinned VERSION=%s; requested '%s'.\n" "$tool" "$VERSION" "$requested" >&2
    return 1
  fi
  # The public script has no staging bypass. The same owner, confirmation,
  # adoption and prior-journal gate as remote-ssh install are mandatory.
  # shellcheck source=/dev/null
  . "$TOOLS_LIB_DIR/commands.lib.sh"
  remote_ssh_cmd_install_main "$REPO_DIR" "$tool"
}

main "$@"
