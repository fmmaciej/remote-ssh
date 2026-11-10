# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="nvim"
GH_REPO="neovim/neovim"
RELEASE_TAG="v0.12.6"
VERSION="0.12.6"

BINARY_NAME="nvim"
INSTALL_LAYOUT="bundle"
BINARY_PATH="bin/nvim"
BUNDLE_REQUIRED_PATHS=("share/nvim/runtime")
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
  "nvim-linux-arm64.tar.gz|8f1f64a0bdb97247034038c3823c6cbad5bdf9ecd5751b85494b71c3ee04c815"
  "nvim-linux-x86_64.tar.gz|474430d53e6264f6d6dd18db42d6dc9df3a1b56ca9e88a325bbf860e1a811d87"
  "nvim-macos-arm64.tar.gz|1dbd148222b051ba6c307c4d17a318ed083df018a4f6a5a0ce46955ffc9ab87b"
  "nvim-macos-x86_64.tar.gz|481424f1dbc85f637d57e47d27d042aa9c883e5a4fe9ee64fc4ee9573b221998"
)
