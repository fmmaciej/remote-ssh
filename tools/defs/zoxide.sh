# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="zoxide"
GH_REPO="ajeetdsouza/zoxide"
RELEASE_TAG="v0.9.9"
VERSION="0.9.9"

BINARY_NAME="zoxide"

ASSETS=(
  "darwin:aarch64:any|zoxide-0.9.9-aarch64-apple-darwin.tar.gz"
  "darwin:x86_64:any|zoxide-0.9.9-x86_64-apple-darwin.tar.gz"
  "linux:aarch64:musl|zoxide-0.9.9-aarch64-unknown-linux-musl.tar.gz"
  "linux:x86_64:musl|zoxide-0.9.9-x86_64-unknown-linux-musl.tar.gz"
)

CHECKSUMS=(
  "zoxide-0.9.9-aarch64-apple-darwin.tar.gz|57e733d0436309dae2ed97e46bba43937209395298e1d88812d4e893900cb40a"
  "zoxide-0.9.9-x86_64-apple-darwin.tar.gz|364249cff18354397c72ebb6b8f7358404c051c486e0f2f7a46e36c86c16f8c7"
  "zoxide-0.9.9-aarch64-unknown-linux-musl.tar.gz|96e6ea2e47a71db42cb7ad5a36e9209c8cb3708f8ae00f6945573d0d93315cb0"
  "zoxide-0.9.9-x86_64-unknown-linux-musl.tar.gz|4ff057d3c4d957946937274c2b8be7af2a9bbae7f90a1b5e9baaa7cb65a20caa"
)
