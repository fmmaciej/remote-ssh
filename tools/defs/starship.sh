# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="starship"
GH_REPO="starship/starship"
RELEASE_TAG="v1.27.0"
VERSION="1.27.0"

BINARY_NAME="starship"

ASSETS=(
  "darwin:aarch64:any|starship-aarch64-apple-darwin.tar.gz"
  "darwin:x86_64:any|starship-x86_64-apple-darwin.tar.gz"
  "linux:aarch64:musl|starship-aarch64-unknown-linux-musl.tar.gz"
  "linux:x86_64:musl|starship-x86_64-unknown-linux-musl.tar.gz"
  "linux:x86_64:gnu|starship-x86_64-unknown-linux-gnu.tar.gz"
)

CHECKSUMS=(
  "starship-aarch64-apple-darwin.tar.gz|5362da8cb2928f98f3ce0ffda697cf0f8de70081db000dae316d6d3a404f6cf0"
  "starship-x86_64-apple-darwin.tar.gz|344e4d38787e0aa86dd522ae5462e6fb6da1227691f81a79ffed480a4563ccb3"
  "starship-aarch64-unknown-linux-musl.tar.gz|341f5cbf24699fa0b27ec88965ad25f862ea09e15d35a543fd6ffdff1d2aa00d"
  "starship-x86_64-unknown-linux-musl.tar.gz|10c8eb4cb3b761d9bf59ea828444c2dab36c900b7d69a69e08814b286969df89"
  "starship-x86_64-unknown-linux-gnu.tar.gz|3b94758850901717eb36aa1b53f8492c1322506ec6d41273bc6151e79ed8e4a1"
)
