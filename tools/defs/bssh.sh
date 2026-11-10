# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="bssh"
GH_REPO="lablup/bssh"
RELEASE_TAG="v2.4.3"
VERSION="2.4.3"

BINARY_NAME="bssh"

ASSETS=(
  "linux:aarch64:musl|bssh-linux-aarch64-musl.tar.gz"
  "linux:aarch64:gnu|bssh-linux-aarch64.tar.gz"
  "linux:x86_64:musl|bssh-linux-x86_64-musl.tar.gz"
  "linux:x86_64:gnu|bssh-linux-x86_64.tar.gz"
  "darwin:aarch64:any|bssh-macos-aarch64.zip"
)

CHECKSUMS=(
  "bssh-linux-aarch64-musl.tar.gz|a3004fc0bf6ca22cf48249e59bb2264f445becbefee4071e867d4c3304275b70"
  "bssh-linux-aarch64.tar.gz|ad552321375a3800c91ae66a866ea2afe11b963b6a7788562d4f64aa3a91ebca"
  "bssh-linux-x86_64-musl.tar.gz|485c85a02e679c0b29f68626d112822bc6147c7d18a1f873a63e512bf676ed27"
  "bssh-linux-x86_64.tar.gz|d948d44fa9402823ec0f0a641cdfa15ed567093604f7b2f776364734822cc980"
  "bssh-macos-aarch64.zip|1e6543028f319a89023d674cea591ba7ec46667063c30aee1fbc3d3577b32d55"
)
