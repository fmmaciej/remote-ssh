# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="atuin"
GH_REPO="atuinsh/atuin"
RELEASE_TAG="v18.14.1"
VERSION="18.14.1"

BINARY_NAME="atuin"

ASSETS=(
  "darwin:aarch64:any|atuin-aarch64-apple-darwin.tar.gz"
  "linux:aarch64:gnu|atuin-aarch64-unknown-linux-gnu.tar.gz"
  "linux:aarch64:musl|atuin-aarch64-unknown-linux-musl.tar.gz"
  "linux:x86_64:gnu|atuin-x86_64-unknown-linux-gnu.tar.gz"
  "linux:x86_64:musl|atuin-x86_64-unknown-linux-musl.tar.gz"
)

CHECKSUMS=(
  "atuin-aarch64-apple-darwin.tar.gz|67ca2694583eac0d02c442d1ffd1cb2d0c505d9f60357e7550aaef2b966597f5"
  "atuin-aarch64-unknown-linux-gnu.tar.gz|cd4ebee1937dd8de5aed25ca1c8a1c8f08446c0ce04d14941f17688b2443e0fd"
  "atuin-aarch64-unknown-linux-musl.tar.gz|cf67d0978def478e7d149cdb94a1e572eb008c8151d95f6a53ee5560720f1141"
  "atuin-x86_64-unknown-linux-gnu.tar.gz|73269ed865c88d830b6106e706f6a074f3815a26d5b26fb9d73738e289ad48bb"
  "atuin-x86_64-unknown-linux-musl.tar.gz|f648ecb4248eb2cd77e17b42370d6229defe306d35443b0601c2c8a5a5fd0a16"
)
