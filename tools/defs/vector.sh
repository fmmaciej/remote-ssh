# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="vector"
GH_REPO="vectordotdev/vector"
RELEASE_TAG="v0.55.0"
VERSION="0.55.0"
BINARY_NAME="vector"

ASSETS=(
  "darwin:aarch64:any|vector-0.55.0-arm64-apple-darwin.tar.gz"
  "linux:aarch64:gnu|vector-0.55.0-aarch64-unknown-linux-gnu.tar.gz"
  "linux:aarch64:musl|vector-0.55.0-aarch64-unknown-linux-musl.tar.gz"
  "linux:x86_64:gnu|vector-0.55.0-x86_64-unknown-linux-gnu.tar.gz"
  "linux:x86_64:musl|vector-0.55.0-x86_64-unknown-linux-musl.tar.gz"
)

CHECKSUMS=(
  "vector-0.55.0-arm64-apple-darwin.tar.gz|0691862ffa7c1135f0be5258ea34e3edf11288cc192bb67a3cd8d8cad914e8c3"
  "vector-0.55.0-aarch64-unknown-linux-gnu.tar.gz|00ce049bd42291165eb207b413e9fa8afacacf2e8ac4312e7dc89488a6ec4e4c"
  "vector-0.55.0-aarch64-unknown-linux-musl.tar.gz|ebc1ed5d8527f2586390dc23122a89ef129de74276b3afb5af37a3d4f956662e"
  "vector-0.55.0-x86_64-unknown-linux-gnu.tar.gz|e0221681b1cd1f93c46008fde19c5ac5811718d10a803a4e320ff4e72ab9e4a9"
  "vector-0.55.0-x86_64-unknown-linux-musl.tar.gz|accdf10b062ee1af31d4babdb2ca2170aab3b8f2c741167cf822296a57d79fa6"
)
