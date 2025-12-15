# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="fzf"
GH_REPO="junegunn/fzf"
DEFAULT_VERSION="0.67.0"
TAG_PREFIX="v"

BINARY_NAME="fzf"

ASSET_PREFIX="fzf"

# "<os>:<arch>:<libc>|<asset_template>|<arch_kind>|<os_kind>"
#
# Uwaga: szkic na podstawie assets z tagu: v0.67.0
VARIANTS=(
  "darwin:x86_64:any|prefix-version-os_arch|amd64_arm64|linux_darwin"
  "darwin:aarch64:any|prefix-version-os_arch|amd64_arm64|linux_darwin"
  "linux:x86_64:gnu|prefix-version-os_arch|amd64_arm64|linux_darwin"
  "linux:aarch64:gnu|prefix-version-os_arch|amd64_arm64|linux_darwin"
)
