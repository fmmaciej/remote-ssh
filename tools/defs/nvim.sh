# shellcheck shell=bash

TOOL_NAME="nvim"
GH_REPO="neovim/neovim"
DEFAULT_VERSION="0.11.5"
TAG_PREFIX="v"

BINARY_NAME="nvim"

ASSET_PREFIX="nvim"

# "<os>:<arch>:<libc>|<asset_template>|<arch_kind>|<os_kind>"
#
# Uwaga: szkic na podstawie assets z tagu: v0.11.5
VARIANTS=(
  "linux:aarch64:gnu|prefix-os-arch|amd64_arm64|linux_darwin"
  "linux:x86_64:gnu|prefix-os-arch|x86_64_aarch64|linux_darwin"
  "darwin:aarch64:any|prefix-os-arch|amd64_arm64|linux_macos"
  "darwin:x86_64:any|prefix-version-os_arch|x86_64_aarch64|linux_macos"
)
