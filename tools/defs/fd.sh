# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="fd"
GH_REPO="sharkdp/fd"
DEFAULT_VERSION="10.3.0"
TAG_PREFIX="v"

BINARY_NAME="fd"

ASSET_PREFIX="fd"

# "<os>:<arch>:<libc>|<asset_template>|<arch_kind>|<os_kind>"
#
# Uwaga: szkic na podstawie assets z tagu: v10.3.0
VARIANTS=(
  "darwin:aarch64:any|prefix-arch-os-tgz|x86_64_aarch64|rust_triple"
  "linux:aarch64:gnu|prefix-arch-os-tgz|x86_64_aarch64|rust_triple"
  "linux:aarch64:musl|prefix-arch-os-tgz|x86_64_aarch64|rust_musl"
  "darwin:x86_64:any|prefix-arch-os-tgz|x86_64_aarch64|rust_triple"
  "linux:x86_64:gnu|prefix-arch-os-tgz|x86_64_aarch64|rust_triple"
  "linux:x86_64:musl|prefix-arch-os-tgz|x86_64_aarch64|rust_musl"
)
