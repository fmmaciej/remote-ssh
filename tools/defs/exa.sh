# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="exa"
GH_REPO="ogham/exa"
DEFAULT_VERSION="0.10.1"
TAG_PREFIX="v"

BINARY_NAME="exa"

ASSET_PREFIX="exa"

# "<os>:<arch>:<libc>|<asset_template>|<arch_kind>|<os_kind>"
#
# Uwaga:  szkic na podstawie assets z tagu: v0.10.1
#         preferuj wersje musl
VARIANTS=(
  "darwin:x86_64:any|prefix-arch-os|x86_64_aarch64|linux_macos"
  "linux:x86_64:musl|prefix-arch-os|x86_64_aarch64|rust_musl"
  "linux:x86_64:gnu|prefix-arch-os|x86_64_aarch64|linux_darwin"
)
