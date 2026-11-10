# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="bottom"
GH_REPO="ClementTsang/bottom"
RELEASE_TAG="0.15.0"
VERSION="0.15.0"

BINARY_NAME="btm"
BINARY_ALIASES=("btm")

ASSETS=(
  "darwin:aarch64:any|bottom_aarch64-apple-darwin.tar.gz"
  "darwin:x86_64:any|bottom_x86_64-apple-darwin.tar.gz"
  "linux:aarch64:gnu|bottom_aarch64-unknown-linux-gnu.tar.gz"
  "linux:aarch64:musl|bottom_aarch64-unknown-linux-musl.tar.gz"
  "linux:x86_64:gnu|bottom_x86_64-unknown-linux-gnu-2-17.tar.gz"
  "linux:x86_64:musl|bottom_x86_64-unknown-linux-musl.tar.gz"
)

CHECKSUMS=(
  "bottom_aarch64-apple-darwin.tar.gz|6d83c9eba811dd139392fa5b04baa75225c6aa120dad36a070e636660db023fd"
  "bottom_x86_64-apple-darwin.tar.gz|6a7f5e32fc2c272256ad5c77aa8aaede02e1e86cf3ba4715acb894d3d6d5b361"
  "bottom_aarch64-unknown-linux-gnu.tar.gz|93221c07d549750e5cfac2a76f70e5d792c744958ecc466bbeb9d3bef34288b6"
  "bottom_aarch64-unknown-linux-musl.tar.gz|78e03e96d02e946be1f94066cd78f1adc3bb8c0db5f53fdf24d70a3ab351e05c"
  "bottom_x86_64-unknown-linux-gnu-2-17.tar.gz|8f13d0edf167d1772cd1252c1f5d87c8c7203e48f29af60a84d21c9d7243a796"
  "bottom_x86_64-unknown-linux-musl.tar.gz|c66d6a0148102f107800919cd0ff6cce8767ae998f3c954b72e37a7f769e3ae2"
)
