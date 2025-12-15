# shellcheck shell=bash

TOOL_NAME="starship"
GH_REPO="starship/starship"
DEFAULT_VERSION="1.24.1"
TAG_PREFIX="v"

BINARY_NAME="starship"

ASSET_PREFIX="starship"

# "<os>:<arch>:<libc>|<asset_template>|<arch_kind>|<os_kind>"
#
# Uwaga: szkic na podstawie assets z tagu: v1.24.1
VARIANTS=(
  "darwin:aarch64:any|prefix-arch-os-tgz|x86_64_aarch64|rust_triple"
  "linux:aarch64:musl|prefix-arch-os-tgz|x86_64_aarch64|rust_musl"
  "darwin:x86_64:any|prefix-arch-os-tgz|x86_64_aarch64|rust_triple"
  "linux:x86_64:gnu|prefix-arch-os-tgz|x86_64_aarch64|rust_triple"
  "linux:x86_64:musl|prefix-arch-os-tgz|x86_64_aarch64|rust_musl"
)
