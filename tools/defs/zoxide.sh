# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="zoxide"
GH_REPO="ajeetdsouza/zoxide"
DEFAULT_VERSION="0.9.9"
TAG_PREFIX="v"

BINARY_NAME="zoxide"

ASSET_PREFIX="zoxide"

# "<os>:<arch>:<libc>|<asset_template>|<arch_kind>|<os_kind>"
#
# Based on release assets from v0.9.9.
VARIANTS=(
  "darwin:aarch64:any|prefix-version-arch-os|x86_64_aarch64|rust_triple"
  "darwin:x86_64:any|prefix-version-arch-os|x86_64_aarch64|rust_triple"
  "linux:aarch64:musl|prefix-version-arch-os|x86_64_aarch64|rust_musl"
  "linux:x86_64:musl|prefix-version-arch-os|x86_64_aarch64|rust_musl"
)
