# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="nvim"
GH_REPO="neovim/neovim"
RELEASE_TAG="v0.11.5"
VERSION="0.11.5"

BINARY_NAME="nvim"
INSTALL_LAYOUT="bundle"
BINARY_PATH="bin/nvim"
BUNDLE_ROOTS=(
  "nvim-linux-arm64.tar.gz|nvim-linux-arm64"
  "nvim-linux-x86_64.tar.gz|nvim-linux-x86_64"
  "nvim-macos-arm64.tar.gz|nvim-macos-arm64"
  "nvim-macos-x86_64.tar.gz|nvim-macos-x86_64"
)

ASSETS=(
  "linux:aarch64:gnu|nvim-linux-arm64.tar.gz"
  "linux:x86_64:gnu|nvim-linux-x86_64.tar.gz"
  "darwin:aarch64:any|nvim-macos-arm64.tar.gz"
  "darwin:x86_64:any|nvim-macos-x86_64.tar.gz"
)
