# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="flyline"
GH_REPO="fmmaciej/flyline"
RELEASE_TAG="remote-ssh-v1.10.0-pr974.aae68bb4.r5"
VERSION="1.10.0-pr974.aae68bb4.r5"

INSTALL_LAYOUT="bash-builtin"
LIBRARY_MEMBERS=(
  flyline-1.10.0-pr974.aae68bb4.r5-aarch64-apple-darwin.tar.gz\|libflyline.dylib
)

# "<os>:<arch>:<libc>|<asset_name>"
#
# Uwaga: szkic na podstawie assets z tagu: remote-ssh-v1.10.0-pr974.aae68bb4.r5
ASSETS=(
  "darwin:aarch64:any|flyline-1.10.0-pr974.aae68bb4.r5-aarch64-apple-darwin.tar.gz"
)

CHECKSUMS=(
  "flyline-1.10.0-pr974.aae68bb4.r5-aarch64-apple-darwin.tar.gz|38a7c65eb6e3c8c7458cdebea36607ae2e5577279b96ce2f6e2907b5ff9afaf3"
)
