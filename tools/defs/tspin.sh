# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="tspin"
GH_REPO="bensadeh/tailspin"
RELEASE_TAG="7.0.0"
VERSION="7.0.0"

BINARY_NAME="tspin"

ASSETS=(
  "darwin:aarch64:any|tailspin-aarch64-apple-darwin.tar.gz"
  "darwin:x86_64:any|tailspin-x86_64-apple-darwin.tar.gz"
  "linux:aarch64:musl|tailspin-aarch64-unknown-linux-musl.tar.gz"
  "linux:x86_64:musl|tailspin-x86_64-unknown-linux-musl.tar.gz"
)

CHECKSUMS=(
  "tailspin-aarch64-apple-darwin.tar.gz|8a815e7c2449c8ba3d25a475cdd92d9d9127b991d7b46e73623d2992e4bb9ce4"
  "tailspin-x86_64-apple-darwin.tar.gz|27e38a1e132234a208cf228b0671b27d59a0484b54d4b4fe356d2cd4ed78f41e"
  "tailspin-aarch64-unknown-linux-musl.tar.gz|de78d9e9204af6817cc3dae342e92d41c41975c2bb11ae1abeabf30c43bc86ad"
  "tailspin-x86_64-unknown-linux-musl.tar.gz|f2de9268dc24811908e63a170507d860ac90c7f6a2f1937f59e5cca78cef21a2"
)
