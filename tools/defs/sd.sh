# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="sd"
GH_REPO="chmln/sd"
RELEASE_TAG="v1.1.0"
VERSION="1.1.0"
BINARY_NAME="sd"

ASSETS=(
  "darwin:aarch64:any|sd-v1.1.0-aarch64-apple-darwin.tar.gz"
  "darwin:x86_64:any|sd-v1.1.0-x86_64-apple-darwin.tar.gz"
  "linux:aarch64:musl|sd-v1.1.0-aarch64-unknown-linux-musl.tar.gz"
  "linux:x86_64:gnu|sd-v1.1.0-x86_64-unknown-linux-gnu.tar.gz"
  "linux:x86_64:musl|sd-v1.1.0-x86_64-unknown-linux-musl.tar.gz"
)

CHECKSUMS=(
  "sd-v1.1.0-aarch64-apple-darwin.tar.gz|4bd3c09226376ca0a1d69589c91e86276fae36c5fbaaee669afce583f6682030"
  "sd-v1.1.0-x86_64-apple-darwin.tar.gz|1fca1e9c91813a8aac6821063c923107ba0f66a83309e095edcd3b202f67f97e"
  "sd-v1.1.0-aarch64-unknown-linux-musl.tar.gz|ec8c93c0533ff21f4851d11566808d4082544baf063d9b96ea77c27e98b7cd99"
  "sd-v1.1.0-x86_64-unknown-linux-gnu.tar.gz|3613eca74cd686739bb5a6d68319aa56c747e7315274d02323a2ca2b1c5d82d2"
  "sd-v1.1.0-x86_64-unknown-linux-musl.tar.gz|02f00f4777d43e8e95b7b8d49e1a0d6e502fed4b8e79c1c8b8063857a30caa2e"
)
