# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="ripgrep"
GH_REPO="BurntSushi/ripgrep"
DEFAULT_VERSION="15.1.0"
TAG_PREFIX=""

BINARY_NAME="rg"

ASSET_PREFIX="ripgrep"

# "<os>:<arch>:<libc>|<asset_template>|<arch_kind>|<os_kind>"
#
# Uwaga: szkic na podstawie assets z tagu: 15.1.0
VARIANTS=(
  "darwin:aarch64:any|prefix-version-arch-os|x86_64_aarch64|rust_triple"
  "darwin:x86_64:any|prefix-version-arch-os|x86_64_aarch64|rust_triple"
  "linux:x86_64:any|prefix-version-arch-os|x86_64_aarch64|rust_musl"
  "linux:aarch64:any|prefix-version-arch-os|x86_64_aarch64|rust_musl"
)
