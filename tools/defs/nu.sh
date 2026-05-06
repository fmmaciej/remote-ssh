# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="nu"
GH_REPO="nushell/nushell"
DEFAULT_VERSION="0.112.2"
TAG_PREFIX=""

BINARY_NAME="nu"
BINARY_ALIASES=("nushell")

ASSET_PREFIX="nu"

# "<os>:<arch>:<libc>|<asset_template>|<arch_kind>|<os_kind>"
#
# Uwaga: szkic na podstawie assets z tagu: 0.112.2
#        preferuj wersje musl
VARIANTS=(
  "darwin:aarch64:any|prefix-version-arch-os|x86_64_aarch64|rust_triple"
  "darwin:x86_64:any|prefix-version-arch-os|x86_64_aarch64|rust_triple"
  "linux:aarch64:musl|prefix-version-arch-os|x86_64_aarch64|rust_musl"
  "linux:x86_64:musl|prefix-version-arch-os|x86_64_aarch64|rust_musl"
  "linux:aarch64:gnu|prefix-version-arch-os|x86_64_aarch64|rust_triple"
  "linux:x86_64:gnu|prefix-version-arch-os|x86_64_aarch64|rust_triple"
)
