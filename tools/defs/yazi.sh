# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="yazi"
GH_REPO="sxyazi/yazi"
RELEASE_TAG="v25.5.31"
VERSION="25.5.31"

BINARY_NAME="yazi"

ASSETS=(
  "darwin:aarch64:any|yazi-aarch64-apple-darwin.zip"
  "darwin:x86_64:any|yazi-x86_64-apple-darwin.zip"
  "linux:aarch64:musl|yazi-aarch64-unknown-linux-musl.zip"
  "linux:x86_64:musl|yazi-x86_64-unknown-linux-musl.zip"
  "linux:aarch64:gnu|yazi-aarch64-unknown-linux-gnu.zip"
  "linux:x86_64:gnu|yazi-x86_64-unknown-linux-gnu.zip"
)
