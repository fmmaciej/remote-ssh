#!/usr/bin/env bash

TOOL_NAME="rg"
GH_REPO="BurntSushi/ripgrep"
DEFAULT_VERSION="15.1.0"
TAG_PREFIX=""

BINARY_NAME="rg"
ASSET_PREFIX="ripgrep"
ASSET_TEMPLATE="prefix-version-arch-os"

ARCH_KIND="x86_64_aarch64"
OS_KIND="rust_triple"   # dla linux/apple-darwin
