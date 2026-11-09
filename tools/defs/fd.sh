# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="fd"
GH_REPO="sharkdp/fd"
RELEASE_TAG="v10.3.0"
VERSION="10.3.0"

BINARY_NAME="fd"

ASSETS=(
  "darwin:aarch64:any|fd-v10.3.0-aarch64-apple-darwin.tar.gz"
  "darwin:x86_64:any|fd-v10.3.0-x86_64-apple-darwin.tar.gz"
  "linux:aarch64:musl|fd-v10.3.0-aarch64-unknown-linux-musl.tar.gz"
  "linux:x86_64:musl|fd-v10.3.0-x86_64-unknown-linux-musl.tar.gz"
  "linux:aarch64:gnu|fd-v10.3.0-aarch64-unknown-linux-gnu.tar.gz"
  "linux:x86_64:gnu|fd-v10.3.0-x86_64-unknown-linux-gnu.tar.gz"
)

CHECKSUMS=(
  "fd-v10.3.0-aarch64-apple-darwin.tar.gz|0570263812089120bc2a5d84f9e65cd0c25e4a4d724c80075c357239c74ae904"
  "fd-v10.3.0-x86_64-apple-darwin.tar.gz|50d30f13fe3d5914b14c4fff5abcbd4d0cdab4b855970a6956f4f006c17117a3"
  "fd-v10.3.0-aarch64-unknown-linux-musl.tar.gz|996b9b1366433b211cb3bbedba91c9dbce2431842144d925428ead0adf32020b"
  "fd-v10.3.0-x86_64-unknown-linux-musl.tar.gz|2b6bfaae8c48f12050813c2ffe1884c61ea26e750d803df9c9114550a314cd14"
  "fd-v10.3.0-aarch64-unknown-linux-gnu.tar.gz|66f297e404400a3358e9a0c0b2f3f4725956e7e4435427a9ae56e22adbe73a68"
  "fd-v10.3.0-x86_64-unknown-linux-gnu.tar.gz|c3c2bc79f838e780173fc8f18b337ec273e7ba17c7ff8f551be29fc3c19b7916"
)
