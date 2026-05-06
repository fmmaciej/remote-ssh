# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="fzf"
GH_REPO="junegunn/fzf"
RELEASE_TAG="v0.67.0"
VERSION="0.67.0"

BINARY_NAME="fzf"

ASSETS=(
  "darwin:x86_64:any|fzf-0.67.0-darwin_amd64.tar.gz"
  "darwin:aarch64:any|fzf-0.67.0-darwin_arm64.tar.gz"
  "linux:x86_64:any|fzf-0.67.0-linux_amd64.tar.gz"
  "linux:aarch64:any|fzf-0.67.0-linux_arm64.tar.gz"
)
