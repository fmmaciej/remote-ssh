# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="rg"
GH_REPO="BurntSushi/ripgrep"
RELEASE_TAG="15.2.0"
VERSION="15.2.0"

BINARY_NAME="rg"

ASSETS=(
  "darwin:aarch64:any|ripgrep-15.2.0-aarch64-apple-darwin.tar.gz"
  "darwin:x86_64:any|ripgrep-15.2.0-x86_64-apple-darwin.tar.gz"
  "linux:x86_64:musl|ripgrep-15.2.0-x86_64-unknown-linux-musl.tar.gz"
  "linux:aarch64:gnu|ripgrep-15.2.0-aarch64-unknown-linux-gnu.tar.gz"
)

CHECKSUMS=(
  "ripgrep-15.2.0-aarch64-apple-darwin.tar.gz|3750b2e93f37e0c692657da574d7019a101c0084da05a790c83fd335bad973e4"
  "ripgrep-15.2.0-x86_64-apple-darwin.tar.gz|af7825fcc69a2afc7a7aea55fc9af90e26421d8f20fe59df32e233c0b8a231c1"
  "ripgrep-15.2.0-x86_64-unknown-linux-musl.tar.gz|33e15bcf1624b25cdd2a55813a47a2f95dbe126268203e76aa6a585d1e7b149c"
  "ripgrep-15.2.0-aarch64-unknown-linux-gnu.tar.gz|a740b91c82eaf9914cfedd353572f2791cbe0162c84101ee0951058f4dcbc90d"
)
