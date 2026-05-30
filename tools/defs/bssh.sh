# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="bssh"
GH_REPO="lablup/bssh"
RELEASE_TAG="v2.2.3"
VERSION="2.2.3"

BINARY_NAME="bssh"

ASSETS=(
  "linux:aarch64:musl|bssh-linux-aarch64-musl.tar.gz"
  "linux:aarch64:gnu|bssh-linux-aarch64.tar.gz"
  "linux:x86_64:musl|bssh-linux-x86_64-musl.tar.gz"
  "linux:x86_64:gnu|bssh-linux-x86_64.tar.gz"
  "darwin:aarch64:any|bssh-macos-aarch64.zip"
)

CHECKSUMS=(
  "bssh-linux-aarch64-musl.tar.gz|56718236f7cffca6bb495a29fc71d058c399d5e7615c01c31e854042b4b77fc1"
  "bssh-linux-aarch64.tar.gz|17df3c7916273cdef664fc5528609f4ae1317f7907ed8a7ff0214d81edd14e78"
  "bssh-linux-x86_64-musl.tar.gz|b2608ad06245bdbacbbcd6b93f11a6e8fc76cbaa1587658c31372e95199025d8"
  "bssh-linux-x86_64.tar.gz|6e1ce2f4ae8a5850aeb24539926f9fe54cf8410ed53429c8a1cf64e1249021ca"
  "bssh-macos-aarch64.zip|f3a2a4b926d86ad71b5a199954f5286215232c73a4b6a10a47b350f5ed4c64c8"
)
