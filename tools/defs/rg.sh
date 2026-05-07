# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="rg"
GH_REPO="BurntSushi/ripgrep"
RELEASE_TAG="15.1.0"
VERSION="15.1.0"

BINARY_NAME="rg"

ASSETS=(
  "darwin:aarch64:any|ripgrep-15.1.0-aarch64-apple-darwin.tar.gz"
  "darwin:x86_64:any|ripgrep-15.1.0-x86_64-apple-darwin.tar.gz"
  "linux:x86_64:musl|ripgrep-15.1.0-x86_64-unknown-linux-musl.tar.gz"
  "linux:aarch64:gnu|ripgrep-15.1.0-aarch64-unknown-linux-gnu.tar.gz"
)

CHECKSUMS=(
  "ripgrep-15.1.0-aarch64-apple-darwin.tar.gz|378e973289176ca0c6054054ee7f631a065874a352bf43f0fa60ef079b6ba715"
  "ripgrep-15.1.0-x86_64-apple-darwin.tar.gz|64811cb24e77cac3057d6c40b63ac9becf9082eedd54ca411b475b755d334882"
  "ripgrep-15.1.0-x86_64-unknown-linux-musl.tar.gz|1c9297be4a084eea7ecaedf93eb03d058d6faae29bbc57ecdaf5063921491599"
  "ripgrep-15.1.0-aarch64-unknown-linux-gnu.tar.gz|2b661c6ef508e902f388e9098d9c4c5aca72c87b55922d94abdba830b4dc885e"
)
