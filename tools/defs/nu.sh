# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="nu"
GH_REPO="nushell/nushell"
RELEASE_TAG="0.112.2"
VERSION="0.112.2"

BINARY_NAME="nu"
BINARY_ALIASES=("nushell")

ASSETS=(
  "darwin:aarch64:any|nu-0.112.2-aarch64-apple-darwin.tar.gz"
  "darwin:x86_64:any|nu-0.112.2-x86_64-apple-darwin.tar.gz"
  "linux:aarch64:musl|nu-0.112.2-aarch64-unknown-linux-musl.tar.gz"
  "linux:x86_64:musl|nu-0.112.2-x86_64-unknown-linux-musl.tar.gz"
  "linux:aarch64:gnu|nu-0.112.2-aarch64-unknown-linux-gnu.tar.gz"
  "linux:x86_64:gnu|nu-0.112.2-x86_64-unknown-linux-gnu.tar.gz"
)

CHECKSUMS=(
  "nu-0.112.2-aarch64-apple-darwin.tar.gz|a61806761db7bc2eddfc313d5ec496c92776a37124bc64a3036374bd55e8c881"
  "nu-0.112.2-x86_64-apple-darwin.tar.gz|8de1dc4a918a1af29fce75d263a8f673f16d35c04ebaa5e3c3ac4ce1eb154f3f"
  "nu-0.112.2-aarch64-unknown-linux-musl.tar.gz|ab32bb605cd11a7d9cfd45c3cb19f6141a724e204b20531802bacd9eb659879b"
  "nu-0.112.2-x86_64-unknown-linux-musl.tar.gz|d9c0ba0938beed6148c8a354c45612c0979d7a787794b8dd13e866ca3b571375"
  "nu-0.112.2-aarch64-unknown-linux-gnu.tar.gz|c25a713f4c10bd886162c62c278db6cf8a657754be53d33379af70fbadab07b8"
  "nu-0.112.2-x86_64-unknown-linux-gnu.tar.gz|4038c171dd2618f2413a2aa615b8dab7e9d04852be8200f1755df3e422328395"
)
