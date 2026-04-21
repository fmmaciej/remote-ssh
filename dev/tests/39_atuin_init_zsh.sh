#!/usr/bin/env bash
set -euo pipefail

if ! command -v zsh >/dev/null 2>&1; then
    echo "SKIP: zsh not available"
    exit 0
fi

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
stub_dir="$(mktemp -d)"
trap 'rm -rf "$stub_dir"' EXIT

cat >"$stub_dir/atuin" <<'EOF'
#!/usr/bin/env bash
if [[ "${1:-}" == "init" && "${2:-}" == "zsh" ]]; then
    cat <<'SCRIPT'
export REMOTE_SSH_TEST_ATUIN_ZSH_INIT=1
SCRIPT
    exit 0
fi
exit 1
EOF
chmod +x "$stub_dir/atuin"

output="$(
    PATH="$stub_dir:$PATH" zsh -i -c '
        export REMOTE_SSH_REPO_DIR="'"$repo_root"'"
        export REMOTE_DOTS_DIR="$REMOTE_SSH_REPO_DIR/dots"
        source "$REMOTE_SSH_REPO_DIR/shell/rc.d/20-atuin.sh"
        print -r -- "init=${REMOTE_SSH_TEST_ATUIN_ZSH_INIT:-0}"
        print -r -- "config=${ATUIN_CONFIG_DIR:-}"
    ' 2>/dev/null
)"

grep -q '^init=1$' <<<"$output"
grep -q '^config='"$repo_root"'/dots/atuin$' <<<"$output"
