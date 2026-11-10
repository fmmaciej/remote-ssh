# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="fd"
GH_REPO="sharkdp/fd"
RELEASE_TAG="v10.5.2"
VERSION="10.5.2"

BINARY_NAME="fd"

ASSETS=(
  "darwin:aarch64:any|fd-v10.5.2-aarch64-apple-darwin.tar.gz"
  "darwin:x86_64:any|fd-v10.5.2-x86_64-apple-darwin.tar.gz"
  "linux:aarch64:musl|fd-v10.5.2-aarch64-unknown-linux-musl.tar.gz"
  "linux:x86_64:musl|fd-v10.5.2-x86_64-unknown-linux-musl.tar.gz"
  "linux:aarch64:gnu|fd-v10.5.2-aarch64-unknown-linux-gnu.tar.gz"
  "linux:x86_64:gnu|fd-v10.5.2-x86_64-unknown-linux-gnu.tar.gz"
)

CHECKSUMS=(
  "fd-v10.5.2-aarch64-apple-darwin.tar.gz|81bf98a16d3d7230e4a9123fcede243d71ea31a577113476ed43f1cdf4773162"
  "fd-v10.5.2-x86_64-apple-darwin.tar.gz|0f02e6000a8c896cd254cf4dccc7da1e604e77a32c6783609eed5e4cb07785e3"
  "fd-v10.5.2-aarch64-unknown-linux-musl.tar.gz|63ea52cb31586e6d98efa2f06d73d542f16c7d0c4af0f07b579aaf9714cf907a"
  "fd-v10.5.2-x86_64-unknown-linux-musl.tar.gz|7e2d07fa2b8807642aaec67b7e2972a9fbe4db26fcb340a7372392db42b26694"
  "fd-v10.5.2-aarch64-unknown-linux-gnu.tar.gz|4b144f38bd7352cd4c95020b58e8e575476e60edcdf1dc5e0733e3d01efba6dd"
  "fd-v10.5.2-x86_64-unknown-linux-gnu.tar.gz|985e24041e9ef6e9a38e9e088743405dde23d7220aa96740f091862167d9ff28"
)
