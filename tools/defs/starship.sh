# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="starship"
GH_REPO="starship/starship"
RELEASE_TAG="v1.24.1"
VERSION="1.24.1"

BINARY_NAME="starship"

ASSETS=(
  "darwin:aarch64:any|starship-aarch64-apple-darwin.tar.gz"
  "darwin:x86_64:any|starship-x86_64-apple-darwin.tar.gz"
  "linux:aarch64:musl|starship-aarch64-unknown-linux-musl.tar.gz"
  "linux:x86_64:musl|starship-x86_64-unknown-linux-musl.tar.gz"
  "linux:x86_64:gnu|starship-x86_64-unknown-linux-gnu.tar.gz"
)
