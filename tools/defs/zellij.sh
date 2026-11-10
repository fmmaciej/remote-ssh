# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="zellij"
GH_REPO="zellij-org/zellij"
RELEASE_TAG="v0.45.1"
VERSION="0.45.1"
BINARY_NAME="zellij"

ASSETS=(
  "darwin:aarch64:any|zellij-aarch64-apple-darwin.tar.gz"
  "linux:aarch64:musl|zellij-aarch64-unknown-linux-musl.tar.gz"
  "darwin:x86_64:any|zellij-x86_64-apple-darwin.tar.gz"
  "linux:x86_64:musl|zellij-x86_64-unknown-linux-musl.tar.gz"
)

CHECKSUMS=(
  "zellij-aarch64-apple-darwin.tar.gz|c029ba4fe1927b79ad9f0cdd59155c4dff80777863c85857d4d09b88b56f9891"
  "zellij-aarch64-unknown-linux-musl.tar.gz|05f0802afadd53f8db9514e7cae53c9ae8432fed1b35b8294aa816ee3044a16b"
  "zellij-x86_64-apple-darwin.tar.gz|8e8bea22737d1652278c51fc5c26c7c22c9855d0ebb9634a84b8873823093114"
  "zellij-x86_64-unknown-linux-musl.tar.gz|40bcc2e03f5d5ae8e054e39f676081fe12ab70871506996ba595834c3718eefc"
)
