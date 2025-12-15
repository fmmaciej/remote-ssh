# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="eza"
GH_REPO="eza-community/eza"
DEFAULT_VERSION="0.23.4"
TAG_PREFIX="v"

BINARY_NAME="eza"

ASSET_PREFIX="eza"

# "<os>:<arch>:<libc>|<asset_template>|<arch_kind>|<os_kind>"
#
# Uwaga:  szkic na podstawie assets z tagu: v0.23.4
#         preferuj wersje musl
VARIANTS=(
  "linux:aarch64:any|prefix_underscore_arch_os|x86_64_aarch64|rust_triple"
  "linux:x86_64:musl|prefix_underscore_arch_os|x86_64_aarch64|rust_musl"
  "linux:x86_64:gnu|prefix_underscore_arch_os|x86_64_aarch64|rust_triple"
)
