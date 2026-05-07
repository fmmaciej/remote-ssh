# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="dust"
GH_REPO="bootandy/dust"
RELEASE_TAG="v1.2.4"
VERSION="1.2.4"
BINARY_NAME="dust"

ASSETS=(
  "linux:aarch64:gnu|dust-v1.2.4-aarch64-unknown-linux-gnu.tar.gz"
  "linux:aarch64:musl|dust-v1.2.4-aarch64-unknown-linux-musl.tar.gz"
  "darwin:x86_64:any|dust-v1.2.4-x86_64-apple-darwin.tar.gz"
  "linux:x86_64:gnu|dust-v1.2.4-x86_64-unknown-linux-gnu.tar.gz"
  "linux:x86_64:musl|dust-v1.2.4-x86_64-unknown-linux-musl.tar.gz"
)

CHECKSUMS=(
  "dust-v1.2.4-aarch64-unknown-linux-gnu.tar.gz|1903296e662a80a504b132525c9360b503de3b900970e1245268605fc65e366d"
  "dust-v1.2.4-aarch64-unknown-linux-musl.tar.gz|e09b0d24b5da0fa06aecf1561849c13ae41ef055c1ce7077e35e9a46744b16af"
  "dust-v1.2.4-x86_64-apple-darwin.tar.gz|bf84d3ff7f58e325d3eb5bb7696df6b22ef1e01fec80c2d8f7c9d3e611be66f4"
  "dust-v1.2.4-x86_64-unknown-linux-gnu.tar.gz|707cfdbfb9d2dc536f8c3853815bbe98a01012f2772463835edae06816551160"
  "dust-v1.2.4-x86_64-unknown-linux-musl.tar.gz|4e313f9f854017e58a2ada4c0d1774677b8cf53d63ab55a991d5871d5f504452"
)
