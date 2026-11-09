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

CHECKSUMS=(
  "nvim-linux-arm64.tar.gz|ea4f9a31b11cc1477ff014aebb7b207684e7280f94ffa97abdab6cacd9b98519"
  "nvim-linux-x86_64.tar.gz|b2f91117be5b5ea39edd7297156dc2a4a8df4add6c95a90809a8df19e7ab6f52"
  "nvim-macos-arm64.tar.gz|79143d3b408f7034f90b7cf59af2276de09ef8a4c2f1a28e4c99581b249d3107"
  "nvim-macos-x86_64.tar.gz|6612760a7037ca2518e456908baf5e43101fa79819d18979fc4d4e8441d9dfa5"
)
