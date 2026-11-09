# shellcheck shell=bash
# shellcheck disable=SC2034
# Publication deferred by user. REVIEW CANDIDATE ONLY. Promote to tools/defs after publishing and verifying
# the exact release asset below. No production URL exists yet.

TOOL_NAME="flyline"
GH_REPO="fmmaciej/flyline"
RELEASE_TAG="remote-ssh-v1.10.0-pr974.aae68bb4.r5"
VERSION="1.10.0-pr974.aae68bb4.r5"
INSTALL_LAYOUT="bash-builtin"

ASSETS=(
  "darwin:aarch64:any|flyline-1.10.0-pr974.aae68bb4.r5-aarch64-apple-darwin.tar.gz"
)
LIBRARY_MEMBERS=(
  "flyline-1.10.0-pr974.aae68bb4.r5-aarch64-apple-darwin.tar.gz|libflyline.dylib"
)
CHECKSUMS=(
  "flyline-1.10.0-pr974.aae68bb4.r5-aarch64-apple-darwin.tar.gz|38a7c65eb6e3c8c7458cdebea36607ae2e5577279b96ce2f6e2907b5ff9afaf3"
)
