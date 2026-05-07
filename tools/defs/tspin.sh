# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="tspin"
GH_REPO="bensadeh/tailspin"
RELEASE_TAG="6.0.0"
VERSION="6.0.0"

BINARY_NAME="tspin"

ASSETS=(
  "darwin:aarch64:any|tailspin-aarch64-apple-darwin.tar.gz"
  "darwin:x86_64:any|tailspin-x86_64-apple-darwin.tar.gz"
  "linux:aarch64:musl|tailspin-aarch64-unknown-linux-musl.tar.gz"
  "linux:x86_64:musl|tailspin-x86_64-unknown-linux-musl.tar.gz"
)

CHECKSUMS=(
  "tailspin-aarch64-apple-darwin.tar.gz|3b3227433f50478d5f70572d879a7bef844ab40bc91bbaa180043a6ae06e1363"
  "tailspin-x86_64-apple-darwin.tar.gz|077f6fcc9ea88b4ed584d1e9256b5af3339afb425f1d7bd447fcb0e7fabd0fd3"
  "tailspin-aarch64-unknown-linux-musl.tar.gz|b01a5d7354a70a7bb9a8d93c8920a782c428db7f24964076fe5c4d738e599477"
  "tailspin-x86_64-unknown-linux-musl.tar.gz|cb96d5cb1160cc4679c67a4c465d8e232688f34882776b5a8ea2a7a312f0e066"
)
