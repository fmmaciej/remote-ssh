# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="nu"
GH_REPO="nushell/nushell"
RELEASE_TAG="0.117.0"
VERSION="0.117.0"

BINARY_NAME="nu"
BINARY_ALIASES=("nushell")

ASSETS=(
  "darwin:aarch64:any|nu-0.117.0-aarch64-apple-darwin.tar.gz"
  "darwin:x86_64:any|nu-0.117.0-x86_64-apple-darwin.tar.gz"
  "linux:aarch64:musl|nu-0.117.0-aarch64-unknown-linux-musl.tar.gz"
  "linux:x86_64:musl|nu-0.117.0-x86_64-unknown-linux-musl.tar.gz"
  "linux:aarch64:gnu|nu-0.117.0-aarch64-unknown-linux-gnu.tar.gz"
  "linux:x86_64:gnu|nu-0.117.0-x86_64-unknown-linux-gnu.tar.gz"
)

CHECKSUMS=(
  "nu-0.117.0-aarch64-apple-darwin.tar.gz|1d0e642ef3bff22113a82749a0fa24a0126f4fea0db46a5909e56e94a4b57527"
  "nu-0.117.0-x86_64-apple-darwin.tar.gz|f44a99227d1fd19d7da9b4a60adbe32bf45700dc25f1a3cb08e4979dee0c1b2f"
  "nu-0.117.0-aarch64-unknown-linux-musl.tar.gz|19966b94ae19f52e2cf0402cb99844ddfa06e2361cf6c77b1b2e29abd17e9188"
  "nu-0.117.0-x86_64-unknown-linux-musl.tar.gz|2b808786d44af41170a29f8b9a15b5113bb6ea5dda9221098eca932f8a149924"
  "nu-0.117.0-aarch64-unknown-linux-gnu.tar.gz|e1a4ff6baa2d7976bb51eccfd44295a871cdd0bc69890a5e9b3b83a0abd9acb1"
  "nu-0.117.0-x86_64-unknown-linux-gnu.tar.gz|33b907da92b0e80bd10fea9fa0e8a1624cabfebd89ee2568e365da3c492ffc68"
)
