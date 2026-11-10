# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="atuin"
GH_REPO="atuinsh/atuin"
RELEASE_TAG="v18.24.6"
VERSION="18.24.6"

BINARY_NAME="atuin"

ASSETS=(
  "darwin:aarch64:any|atuin-aarch64-apple-darwin.tar.gz"
  "linux:aarch64:gnu|atuin-aarch64-unknown-linux-gnu.tar.gz"
  "linux:aarch64:musl|atuin-aarch64-unknown-linux-musl.tar.gz"
  "linux:x86_64:gnu|atuin-x86_64-unknown-linux-gnu.tar.gz"
  "linux:x86_64:musl|atuin-x86_64-unknown-linux-musl.tar.gz"
)

CHECKSUMS=(
  "atuin-aarch64-apple-darwin.tar.gz|756b7d2f8cb919d29888ea52b2fb19aba92ed52ddbca456839088ccc63257f5b"
  "atuin-aarch64-unknown-linux-gnu.tar.gz|8e984995d681a8bb8af1b3f5798539a45123e3a2db2a67b9dc95dee3cfac86f3"
  "atuin-aarch64-unknown-linux-musl.tar.gz|0dcc72a06738f913040cdd990298a37d9ef062c8849026d0a3410d2def4c6bf7"
  "atuin-x86_64-unknown-linux-gnu.tar.gz|8be1b3083ca19ed2743f71f4b08be2b68208336b8cf5b71870263abc76899af3"
  "atuin-x86_64-unknown-linux-musl.tar.gz|49b6e7a93cd6d8c77ee02bdb0eef0acff4c80ddaa0efb00c8179285771043698"
)
