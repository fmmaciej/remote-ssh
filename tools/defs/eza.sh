# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="eza"
GH_REPO="eza-community/eza"
RELEASE_TAG="v0.23.4"
VERSION="0.23.4"

BINARY_NAME="eza"

ASSETS=(
  "linux:aarch64:gnu|eza_aarch64-unknown-linux-gnu.tar.gz"
  "linux:x86_64:musl|eza_x86_64-unknown-linux-musl.tar.gz"
  "linux:x86_64:gnu|eza_x86_64-unknown-linux-gnu.tar.gz"
)
