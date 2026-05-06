# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="rg"
GH_REPO="BurntSushi/ripgrep"
RELEASE_TAG="15.1.0"
VERSION="15.1.0"

BINARY_NAME="rg"

ASSETS=(
  "darwin:aarch64:any|ripgrep-15.1.0-aarch64-apple-darwin.tar.gz"
  "darwin:x86_64:any|ripgrep-15.1.0-x86_64-apple-darwin.tar.gz"
  "linux:x86_64:musl|ripgrep-15.1.0-x86_64-unknown-linux-musl.tar.gz"
  "linux:aarch64:gnu|ripgrep-15.1.0-aarch64-unknown-linux-gnu.tar.gz"
)
