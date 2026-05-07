# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="navi"
GH_REPO="denisidoro/navi"
RELEASE_TAG="v2.23.0"
VERSION="2.23.0"

BINARY_NAME="navi"

ASSETS=(
  "darwin:aarch64:any|navi-v2.23.0-aarch64-apple-darwin.tar.gz"
  "darwin:x86_64:any|navi-v2.23.0-x86_64-apple-darwin.tar.gz"
  "linux:aarch64:gnu|navi-v2.23.0-aarch64-unknown-linux-gnu.tar.gz"
  "linux:x86_64:musl|navi-v2.23.0-x86_64-unknown-linux-musl.tar.gz"
)
