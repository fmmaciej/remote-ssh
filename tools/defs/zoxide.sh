# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="zoxide"
GH_REPO="ajeetdsouza/zoxide"
RELEASE_TAG="v0.10.0"
VERSION="0.10.0"

BINARY_NAME="zoxide"

ASSETS=(
  "darwin:aarch64:any|zoxide-0.10.0-aarch64-apple-darwin.tar.gz"
  "darwin:x86_64:any|zoxide-0.10.0-x86_64-apple-darwin.tar.gz"
  "linux:aarch64:musl|zoxide-0.10.0-aarch64-unknown-linux-musl.tar.gz"
  "linux:x86_64:musl|zoxide-0.10.0-x86_64-unknown-linux-musl.tar.gz"
)

CHECKSUMS=(
  "zoxide-0.10.0-aarch64-apple-darwin.tar.gz|b55ae6f2f5f23d0a6ccb3bd4eeb2af9c7e0a6556e5255c82100e40305129bbb0"
  "zoxide-0.10.0-x86_64-apple-darwin.tar.gz|18ab7ae2633ad6e2ab79a4e665cbba1e95b7c872d44523326efb793202451dad"
  "zoxide-0.10.0-aarch64-unknown-linux-musl.tar.gz|f1f16c5d6298d63dee467eedea1cdcd8490e43e493bea43acd416dc9033ef641"
  "zoxide-0.10.0-x86_64-unknown-linux-musl.tar.gz|2d93385b99f3e82cf2701609a1bffcad863fbeb75aa3fe7eb6be4d29be68b1ae"
)
