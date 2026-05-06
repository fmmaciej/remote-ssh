# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="fd"
GH_REPO="sharkdp/fd"
RELEASE_TAG="v10.3.0"
VERSION="10.3.0"

BINARY_NAME="fd"

ASSETS=(
  "darwin:aarch64:any|fd-v10.3.0-aarch64-apple-darwin.tar.gz"
  "darwin:x86_64:any|fd-v10.3.0-x86_64-apple-darwin.tar.gz"
  "linux:aarch64:musl|fd-v10.3.0-aarch64-unknown-linux-musl.tar.gz"
  "linux:x86_64:musl|fd-v10.3.0-x86_64-unknown-linux-musl.tar.gz"
  "linux:aarch64:gnu|fd-v10.3.0-aarch64-unknown-linux-gnu.tar.gz"
  "linux:x86_64:gnu|fd-v10.3.0-x86_64-unknown-linux-gnu.tar.gz"
)
