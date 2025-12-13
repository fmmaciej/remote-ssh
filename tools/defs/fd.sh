# shellcheck shell=bash

TOOL_NAME="fd"
GH_REPO="sharkdp/fd"
DEFAULT_VERSION="10.3.0"
TAG_PREFIX="v"

BINARY_NAME="fd"
ASSET_PREFIX="fd-v"
ASSET_TEMPLATE="prefix-version-arch-os"

ARCH_KIND="x86_64_aarch64"
OS_KIND="rust_triple"

# .../download/$TAG_PREFIX$TAG/$ASSET_PREFIX-$VERSION-aarch64-apple-darwin.tar.gz

# .../download/v10.3.0/fd-v10.3.0-aarch64-apple-darwin.tar.gz
# .../download/0.67.0/fzf-0.67.0-darwin_arm64.tar.gz
# .../download/14.1.0/ripgrep-14.1.0-aarch64-apple-darwin.tar.gz

# https://github.com/sharkdp/fd/releases/download/10.3.0/fd-v10.3.0-aarch64-apple-darwin.tar.gz
# https://github.com/sharkdp/fd/releases/download/v10.3.0/fd-v10.3.0-aarch64-apple-darwin.tar.gz
