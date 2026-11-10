# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="dust"
GH_REPO="bootandy/dust"
RELEASE_TAG="v1.2.7"
VERSION="1.2.7"
BINARY_NAME="dust"

ASSETS=(
  "linux:aarch64:gnu|dust-v1.2.7-aarch64-unknown-linux-gnu.tar.gz"
  "linux:aarch64:musl|dust-v1.2.7-aarch64-unknown-linux-musl.tar.gz"
  "darwin:x86_64:any|dust-v1.2.7-x86_64-apple-darwin.tar.gz"
  "linux:x86_64:gnu|dust-v1.2.7-x86_64-unknown-linux-gnu.tar.gz"
  "linux:x86_64:musl|dust-v1.2.7-x86_64-unknown-linux-musl.tar.gz"
)

CHECKSUMS=(
  "dust-v1.2.7-aarch64-unknown-linux-gnu.tar.gz|64496fe9e56dabb379308b3a079816818f6022d0b93638d06206a9144ca795d9"
  "dust-v1.2.7-aarch64-unknown-linux-musl.tar.gz|4c8ebaf224179bfd42db45d8a50fd5304bbd89532eda94db684d309c7b734ed6"
  "dust-v1.2.7-x86_64-apple-darwin.tar.gz|5eef77d18dfd2d1d56d1b3c415bc2d41b5b793bc63b5c7f706005d058a48a363"
  "dust-v1.2.7-x86_64-unknown-linux-gnu.tar.gz|ec3bf712c660dcaa5578b996741f5cca36b30c021c1e4b49352b11137a95a96e"
  "dust-v1.2.7-x86_64-unknown-linux-musl.tar.gz|2f1a1106f1f14c0b684b2f0a5f4482c6d53e07a871df4afc11e3b91ade300b55"
)
