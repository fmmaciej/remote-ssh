# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="vector"
GH_REPO="vectordotdev/vector"
RELEASE_TAG="v0.61.0"
VERSION="0.61.0"
BINARY_NAME="vector"

ASSETS=(
  "darwin:aarch64:any|vector-0.61.0-arm64-apple-darwin.tar.gz"
  "linux:aarch64:gnu|vector-0.61.0-aarch64-unknown-linux-gnu.tar.gz"
  "linux:aarch64:musl|vector-0.61.0-aarch64-unknown-linux-musl.tar.gz"
  "linux:x86_64:gnu|vector-0.61.0-x86_64-unknown-linux-gnu.tar.gz"
  "linux:x86_64:musl|vector-0.61.0-x86_64-unknown-linux-musl.tar.gz"
)

CHECKSUMS=(
  "vector-0.61.0-arm64-apple-darwin.tar.gz|5e747594bb12c8d9ab85c16f2fb5e9fa35bc92911e17099a9721f7d833ae3503"
  "vector-0.61.0-aarch64-unknown-linux-gnu.tar.gz|4f6e3093c0963611c8e31478137adca07920e729bdcc734d4ba7ab6f948a7e9f"
  "vector-0.61.0-aarch64-unknown-linux-musl.tar.gz|12d7e91db2e447003558c955c4f510b17ed1d77340757f3e591e5222e464675c"
  "vector-0.61.0-x86_64-unknown-linux-gnu.tar.gz|84a27c3ad6b772fdb05bb76ea01a31498bfc8f5e71f32cc78a0d96841f1aa827"
  "vector-0.61.0-x86_64-unknown-linux-musl.tar.gz|e1609b8a55ef1c1fc4fd88633e2bc6366e9a4022f6f1ae846cadd27af5237621"
)
