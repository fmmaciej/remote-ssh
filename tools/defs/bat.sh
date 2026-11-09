# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="bat"
GH_REPO="sharkdp/bat"
RELEASE_TAG="v0.26.1"
VERSION="0.26.1"

BINARY_NAME="bat"

ASSETS=(
  "darwin:aarch64:any|bat-v0.26.1-aarch64-apple-darwin.tar.gz"
  "darwin:x86_64:any|bat-v0.26.1-x86_64-apple-darwin.tar.gz"
  "linux:aarch64:musl|bat-v0.26.1-aarch64-unknown-linux-musl.tar.gz"
  "linux:x86_64:musl|bat-v0.26.1-x86_64-unknown-linux-musl.tar.gz"
  "linux:aarch64:gnu|bat-v0.26.1-aarch64-unknown-linux-gnu.tar.gz"
  "linux:x86_64:gnu|bat-v0.26.1-x86_64-unknown-linux-gnu.tar.gz"
)

CHECKSUMS=(
  "bat-v0.26.1-aarch64-apple-darwin.tar.gz|e30beff26779c9bf60bb541e1d79046250cb74378f2757f8eb250afddb19e114"
  "bat-v0.26.1-x86_64-apple-darwin.tar.gz|830d63b0bba1fa040542ec569e3cf77f60d3356b9de75116a344b061e0894245"
  "bat-v0.26.1-aarch64-unknown-linux-musl.tar.gz|6369242c584065f195fb20cb36fbd7cb63ae690605bbe89868a7596b596c2c23"
  "bat-v0.26.1-x86_64-unknown-linux-musl.tar.gz|0dcd8ac79732c0d5b136f11f4ee00e581440e16a44eab5b3105b611bbf2cf191"
  "bat-v0.26.1-aarch64-unknown-linux-gnu.tar.gz|422eb73e11c854fddd99f5ca8461c2f1d6e6dce0a2a8c3d5daade5ffcb6564aa"
  "bat-v0.26.1-x86_64-unknown-linux-gnu.tar.gz|726f04c8f576a7fd18b7634f1bbf2f915c43494c1c0f013baa3287edb0d5a2a3"
)
