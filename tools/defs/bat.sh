# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="bat"
GH_REPO="sharkdp/bat"
RELEASE_TAG="v0.26.1"
VERSION="0.26.1"

BINARY_NAME="bat"

ASSETS=(
  "darwin:aarch64:any|bat-v0.26.1-aarch64-apple-darwin.tar.gz"
  "darwin:x86_64:any|bat-v0.26.1-x86_64-apple-darwin.tar.gz"
  "linux:aarch64:musl|bat-v0.26.1-aarch64-unknown-linux-musl.tar.gz"
  "linux:x86_64:musl|bat-v0.26.1-x86_64-unknown-linux-musl.tar.gz"
  "linux:aarch64:gnu|bat-v0.26.1-aarch64-unknown-linux-gnu.tar.gz"
  "linux:x86_64:gnu|bat-v0.26.1-x86_64-unknown-linux-gnu.tar.gz"
)
