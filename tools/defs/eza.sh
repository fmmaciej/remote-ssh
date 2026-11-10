# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="eza"
GH_REPO="eza-community/eza"
RELEASE_TAG="v0.23.5"
VERSION="0.23.5"

BINARY_NAME="eza"

ASSETS=(
  "linux:aarch64:gnu|eza_aarch64-unknown-linux-gnu.tar.gz"
  "linux:x86_64:musl|eza_x86_64-unknown-linux-musl.tar.gz"
  "linux:x86_64:gnu|eza_x86_64-unknown-linux-gnu.tar.gz"
)

CHECKSUMS=(
  "eza_aarch64-unknown-linux-gnu.tar.gz|40b87ae8628aa2ff0f0d2dc24ab52f689631366385c3da630bae745671fd71ec"
  "eza_x86_64-unknown-linux-musl.tar.gz|e06eebab74b73d6b7d51a796a353824b001bea82df077706382e100815d28904"
  "eza_x86_64-unknown-linux-gnu.tar.gz|35c70c5c43c29108075e58b893234c67ef585f0b53a7eaf8e9e7d4eec9f339b4"
)
