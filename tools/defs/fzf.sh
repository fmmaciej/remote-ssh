# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="fzf"
GH_REPO="junegunn/fzf"
RELEASE_TAG="v0.67.0"
VERSION="0.67.0"

BINARY_NAME="fzf"

ASSETS=(
  "darwin:x86_64:any|fzf-0.67.0-darwin_amd64.tar.gz"
  "darwin:aarch64:any|fzf-0.67.0-darwin_arm64.tar.gz"
  "linux:x86_64:any|fzf-0.67.0-linux_amd64.tar.gz"
  "linux:aarch64:any|fzf-0.67.0-linux_arm64.tar.gz"
)

CHECKSUMS=(
  "fzf-0.67.0-darwin_amd64.tar.gz|88dc853e0914793a2e7be0d1acfe6c922d9ccad08e3302df092399775b0279ff"
  "fzf-0.67.0-darwin_arm64.tar.gz|b7f34c964d8e52c471c933cef8ec43dc71997c266cafafd1b013bed10fc229a1"
  "fzf-0.67.0-linux_amd64.tar.gz|4be08018ca37b32518c608741933ea335a406de3558242b60619e98f25be2be1"
  "fzf-0.67.0-linux_arm64.tar.gz|7071f48c2ac0f2bc992d6d33cc36fd675a579a98cc976dda699eea07dd5e9c58"
)
