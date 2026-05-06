# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="nvim"
GH_REPO="neovim/neovim"
RELEASE_TAG="v0.11.5"
VERSION="0.11.5"

BINARY_NAME="nvim"

ASSETS=(
  "linux:aarch64:gnu|nvim-linux-arm64.tar.gz"
  "linux:x86_64:gnu|nvim-linux-x86_64.tar.gz"
  "darwin:aarch64:any|nvim-macos-arm64.tar.gz"
  "darwin:x86_64:any|nvim-macos-x86_64.tar.gz"
)
