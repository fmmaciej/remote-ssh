# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="eza"
GH_REPO="eza-community/eza"
RELEASE_TAG="v0.23.4"
VERSION="0.23.4"

BINARY_NAME="eza"

ASSETS=(
  "linux:aarch64:gnu|eza_aarch64-unknown-linux-gnu.tar.gz"
  "linux:x86_64:musl|eza_x86_64-unknown-linux-musl.tar.gz"
  "linux:x86_64:gnu|eza_x86_64-unknown-linux-gnu.tar.gz"
)

CHECKSUMS=(
  "eza_aarch64-unknown-linux-gnu.tar.gz|366e8430225f9955c3dc659b452150c169894833ccfef455e01765e265a3edda"
  "eza_x86_64-unknown-linux-musl.tar.gz|d231bb3ee33b08c76279b5888845dceb7034d055c42bb9be46dbe0dae39394df"
  "eza_x86_64-unknown-linux-gnu.tar.gz|0c38665440226cd8bef5d1d4f3bc6ff77c927fb0d68b752739105db7ab5b358d"
)
