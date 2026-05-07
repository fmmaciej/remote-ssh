# shellcheck shell=bash

ensure_this_file_sourced

render_defs() {
  local tool="${1:?tool required}"
  local repo="${2:?repo required}"
  local tag="${3:?tag required}"

  cat <<EOF
# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="${tool}"
GH_REPO="${repo}"
RELEASE_TAG="${RELEASE_TAG}"
VERSION="${VERSION}"

BINARY_NAME="${tool}"

# "<os>:<arch>:<libc>|<asset_name>"
#
# Uwaga: szkic na podstawie assets z tagu: ${tag}
ASSETS=(
EOF

  printf '  %s\n' "${ASSETS_EMIT[@]}"

  cat <<'EOF'
)
EOF

  if declare -p CHECKSUMS_EMIT >/dev/null 2>&1 && ((${#CHECKSUMS_EMIT[@]} > 0)); then
    cat <<'EOF'

CHECKSUMS=(
EOF

    printf '  %s\n' "${CHECKSUMS_EMIT[@]}"

    cat <<'EOF'
)
EOF
  fi
}
