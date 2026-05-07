# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="zellij"
GH_REPO="zellij-org/zellij"
RELEASE_TAG="v0.44.2"
VERSION="0.44.2"
BINARY_NAME="zellij"

ASSETS=(
  "darwin:aarch64:any|zellij-aarch64-apple-darwin.tar.gz"
  "linux:aarch64:musl|zellij-aarch64-unknown-linux-musl.tar.gz"
  "darwin:x86_64:any|zellij-x86_64-apple-darwin.tar.gz"
  "linux:x86_64:musl|zellij-x86_64-unknown-linux-musl.tar.gz"
)

CHECKSUMS=(
  "zellij-aarch64-apple-darwin.tar.gz|2f914c95d9d57e15573cbfb3848071b8f34a0b7f3f8951876b3de20ec9e32ac7"
  "zellij-aarch64-unknown-linux-musl.tar.gz|e0b2ddbf050d58577b09b2a032a54f1a3fac0e214d1605c5969e8936340fff6b"
  "zellij-x86_64-apple-darwin.tar.gz|1150710e3f78211144a7b0e58235b8fa459ea3797b2063cfa03b183487298cd0"
  "zellij-x86_64-unknown-linux-musl.tar.gz|26e1753b4c8451912523c7d8700c5aed75392ea57f0b1c988560f3bbc7775744"
)
