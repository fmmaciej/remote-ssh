#!/usr/bin/env bash

generate_def_from_fixture() {
  cd "$REPO_DIR" || return
  # shellcheck source=/dev/null
  . "$REPO_DIR/tools/lib/env.sh"
  # shellcheck source=/dev/null
  . "$TOOLS_LIB_DIR/generate-def.lib.sh"

  GITHUB_TAG="v18.14.1"
  GITHUB_ASSETS=(
    "atuin-aarch64-apple-darwin-update"
    "atuin-aarch64-apple-darwin.tar.gz"
    "atuin-aarch64-unknown-linux-gnu-update"
    "atuin-aarch64-unknown-linux-gnu.tar.gz"
    "atuin-x86_64-unknown-linux-gnu-update"
    "atuin-x86_64-unknown-linux-gnu.tar.gz"
    "atuin-aarch64-unknown-linux-musl-update"
    "atuin-aarch64-unknown-linux-musl.tar.gz"
    "atuin-x86_64-unknown-linux-musl-update"
    "atuin-x86_64-unknown-linux-musl.tar.gz"
    "atuin-x86_64-pc-windows-msvc.zip"
    "atuin-installer.sh"
    "atuin-aarch64-apple-darwin.tar.gz.sha256"
    "atuin-server-x86_64-apple-darwin.tar.gz"
  )

  tag_prefix_and_version "$GITHUB_TAG"
  detect_asset_prefix "atuin" "$DEFAULT_VERSION" "${GITHUB_ASSETS[@]}"
  build_variants_from_assets "${GITHUB_ASSETS[@]}"
  render_defs "atuin" "atuinsh/atuin" "$GITHUB_TAG"
}

test_generate_def_atuin_fixture() {
  log "generate-def renders atuin fixture"

  local expected got
  expected="$(cat <<'EOF'
# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="atuin"
GH_REPO="atuinsh/atuin"
DEFAULT_VERSION="18.14.1"
TAG_PREFIX="v"

BINARY_NAME="atuin"

ASSET_PREFIX="atuin"

# "<os>:<arch>:<libc>|<asset_template>|<arch_kind>|<os_kind>"
#
# Uwaga:  szkic na podstawie assets z tagu: v18.14.1
#         preferuj wersje musl
VARIANTS=(
  "darwin:aarch64:any|prefix-arch-os-tgz|x86_64_aarch64|rust_triple"
  "linux:aarch64:gnu|prefix-arch-os-tgz|x86_64_aarch64|rust_triple"
  "linux:x86_64:gnu|prefix-arch-os-tgz|x86_64_aarch64|rust_triple"
  "linux:aarch64:musl|prefix-arch-os-tgz|x86_64_aarch64|rust_musl"
  "linux:x86_64:musl|prefix-arch-os-tgz|x86_64_aarch64|rust_musl"
)
EOF
)"
  got="$(generate_def_from_fixture)"

  assert_eq "atuin generated def" "$expected" "$got"
}

register_test test_generate_def_atuin_fixture
