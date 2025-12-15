# shellcheck shell=bash

ensure_this_file_sourced

render_defs() {
  local tool="${1:?tool required}"
  local repo="${2:?repo required}"
  local tag="${3:?tag required}"

  cat <<EOF
# shellcheck shell=bash

TOOL_NAME="${tool}"
GH_REPO="${repo}"
DEFAULT_VERSION="${DEFAULT_VERSION}"
TAG_PREFIX="${TAG_PREFIX}"

BINARY_NAME="${tool}"

ASSET_PREFIX="${ASSET_PREFIX}"

# "<os>:<arch>:<libc>|<asset_template>|<arch_kind>|<os_kind>"
#
# Uwaga: szkic na podstawie assets z tagu: ${tag}
VARIANTS=(
EOF

  printf '  %s\n' "${VARIANTS_EMIT[@]}"

  cat <<'EOF'
)
EOF
}
