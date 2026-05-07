# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="starship"
GH_REPO="starship/starship"
RELEASE_TAG="v1.24.1"
VERSION="1.24.1"

BINARY_NAME="starship"

ASSETS=(
  "darwin:aarch64:any|starship-aarch64-apple-darwin.tar.gz"
  "darwin:x86_64:any|starship-x86_64-apple-darwin.tar.gz"
  "linux:aarch64:musl|starship-aarch64-unknown-linux-musl.tar.gz"
  "linux:x86_64:musl|starship-x86_64-unknown-linux-musl.tar.gz"
  "linux:x86_64:gnu|starship-x86_64-unknown-linux-gnu.tar.gz"
)

CHECKSUMS=(
  "starship-aarch64-apple-darwin.tar.gz|877e6b18d8f826167ca6b6f2ff00ebac2477fa1924c06b89befe524840ffc726"
  "starship-x86_64-apple-darwin.tar.gz|66625a719017f93ffd0f2071abb78295665c916329bb89dd6a09163cb395e3f1"
  "starship-aarch64-unknown-linux-musl.tar.gz|a01ac37aa5993b78ecd6761c5ff4f805032b8ba566357ffbb2227980216f2216"
  "starship-x86_64-unknown-linux-musl.tar.gz|44a729c34aea5b0451fba49108cdc5ef6b1ae68db65e7623cc244a52efcd23d1"
  "starship-x86_64-unknown-linux-gnu.tar.gz|afa28fc0b33cfcf6da95f0f2cf2ec47b5f7460d64cf3eff17e2c11c5dfffab43"
)
