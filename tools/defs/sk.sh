# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="sk"
GH_REPO="skim-rs/skim"
RELEASE_TAG="v5.9.0"
VERSION="5.9.0"

BINARY_NAME="sk"

ASSETS=(
  "darwin:aarch64:any|skim-aarch64-apple-darwin.tar.xz"
  "linux:aarch64:gnu|skim-aarch64-unknown-linux-gnu.tar.xz"
  "linux:aarch64:musl|skim-aarch64-unknown-linux-musl.tar.xz"
  "darwin:x86_64:any|skim-x86_64-apple-darwin.tar.xz"
  "linux:x86_64:gnu|skim-x86_64-unknown-linux-gnu.tar.xz"
  "linux:x86_64:musl|skim-x86_64-unknown-linux-musl.tar.xz"
)

CHECKSUMS=(
  "skim-aarch64-apple-darwin.tar.xz|9fe50c046ca23def3fb6b6d01cf60cc2c4aa24752936f5745899c61c324b6b26"
  "skim-aarch64-unknown-linux-gnu.tar.xz|b2f64629ea312778e25bbdcad2d009b68cdc5e4376a164f95d92db4ad7170dda"
  "skim-aarch64-unknown-linux-musl.tar.xz|651fa4314223e3c32478f32cab22cf046943c6852caa220c73f211f785bc257a"
  "skim-x86_64-apple-darwin.tar.xz|71832e5264f15a617991061232c09eaa85a6c9afe49cbf09848ba5a07d8438d8"
  "skim-x86_64-unknown-linux-gnu.tar.xz|9a9331f464f353afbb27a8edd40c5175c892eaf1660a337ab40db546b6f9f41f"
  "skim-x86_64-unknown-linux-musl.tar.xz|de1ab4c6a0e53e3ed7850048ddd622b830b5aee2dc8ad8f0925f1fbf79e01eef"
)
