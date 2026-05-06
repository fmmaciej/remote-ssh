# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="nu"
GH_REPO="nushell/nushell"
RELEASE_TAG="0.112.2"
VERSION="0.112.2"

BINARY_NAME="nu"
BINARY_ALIASES=("nushell")

ASSETS=(
  "darwin:aarch64:any|nu-0.112.2-aarch64-apple-darwin.tar.gz"
  "darwin:x86_64:any|nu-0.112.2-x86_64-apple-darwin.tar.gz"
  "linux:aarch64:musl|nu-0.112.2-aarch64-unknown-linux-musl.tar.gz"
  "linux:x86_64:musl|nu-0.112.2-x86_64-unknown-linux-musl.tar.gz"
  "linux:aarch64:gnu|nu-0.112.2-aarch64-unknown-linux-gnu.tar.gz"
  "linux:x86_64:gnu|nu-0.112.2-x86_64-unknown-linux-gnu.tar.gz"
)
