# shellcheck shell=bash

TOOL_NAME="fzf"
GH_REPO="junegunn/fzf"
DEFAULT_VERSION="0.67.0"
TAG_PREFIX="v"

BINARY_NAME="fzf"
ASSET_PREFIX="fzf"
ASSET_TEMPLATE="prefix-version-os_arch"

ARCH_KIND="amd64_arm64"
OS_KIND="linux_darwin"

# https://github.com/sharkdp/fd/releases/download/v10.3.0/fd-v10.3.0-aarch64-apple-darwin.tar.gz
# .../releases/download/$TAG_PREFIX$TAG/$ASSET_PREFIX-$VERSION-aarch64-apple-darwin.tar.gz
