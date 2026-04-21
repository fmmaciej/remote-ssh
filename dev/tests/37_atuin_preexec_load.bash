#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

output="$(
    bash -i -c '
        export REMOTE_SSH_REPO_DIR="'"$repo_root"'"
        source "$REMOTE_SSH_REPO_DIR/shell/rc.d/05-bash-preexec.sh"
        printf "%s\n" "${bash_preexec_imported:-missing}"
    ' 2>/dev/null
)"

test "$output" != "missing"
