# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="atuin"
GH_REPO="atuinsh/atuin"
DEFAULT_VERSION="18.14.1"
TAG_PREFIX="v"

BINARY_NAME="atuin"

ASSET_PREFIX="atuin"

# "<os>:<arch>:<libc>|<asset_template>|<arch_kind>|<os_kind>"
#
# Uwaga:  szkic na podstawie assets z tagu: v18.14.1
#         preferuj wersje musl
VARIANTS=(
  "darwin:aarch64:any|prefix-arch-os-tgz|x86_64_aarch64|rust_triple"
  "linux:aarch64:gnu|prefix-arch-os-tgz|x86_64_aarch64|rust_triple"
  "linux:aarch64:musl|prefix-arch-os-tgz|x86_64_aarch64|rust_musl"
  "linux:x86_64:gnu|prefix-arch-os-tgz|x86_64_aarch64|rust_triple"
  "linux:x86_64:musl|prefix-arch-os-tgz|x86_64_aarch64|rust_musl"
)
