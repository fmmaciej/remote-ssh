# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="yazi"
GH_REPO="sxyazi/yazi"
DEFAULT_VERSION="25.5.31"
TAG_PREFIX="v"

BINARY_NAME="yazi"

ASSET_PREFIX="yazi"

# "<os>:<arch>:<libc>|<asset_template>|<arch_kind>|<os_kind>"
#
# Uwaga: szkic na podstawie assets z tagu: v25.5.31
VARIANTS=(
  "darwin:aarch64:any|prefix-arch-os|x86_64_aarch64|rust_triple"
  "darwin:x86_64:any|prefix-arch-os|x86_64_aarch64|rust_triple"
  "linux:aarch64:musl|prefix-arch-os|x86_64_aarch64|rust_musl"
  "linux:x86_64:musl|prefix-arch-os|x86_64_aarch64|rust_musl"
  "linux:aarch64:gnu|prefix-arch-os|x86_64_aarch64|rust_triple"
  "linux:x86_64:gnu|prefix-arch-os|x86_64_aarch64|rust_triple"
)
