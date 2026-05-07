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
  detect_asset_prefix "atuin" "$VERSION" "${GITHUB_ASSETS[@]}"
  build_assets_from_assets "${GITHUB_ASSETS[@]}"
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
RELEASE_TAG="v18.14.1"
VERSION="18.14.1"

BINARY_NAME="atuin"

# "<os>:<arch>:<libc>|<asset_name>"
#
# Uwaga: szkic na podstawie assets z tagu: v18.14.1
ASSETS=(
  "darwin:aarch64:any|atuin-aarch64-apple-darwin.tar.gz"
  "linux:aarch64:gnu|atuin-aarch64-unknown-linux-gnu.tar.gz"
  "linux:x86_64:gnu|atuin-x86_64-unknown-linux-gnu.tar.gz"
  "linux:aarch64:musl|atuin-aarch64-unknown-linux-musl.tar.gz"
  "linux:x86_64:musl|atuin-x86_64-unknown-linux-musl.tar.gz"
)
EOF
)"
  got="$(generate_def_from_fixture)"

  assert_eq "atuin generated def" "$expected" "$got"
}

register_test test_generate_def_atuin_fixture

test_generate_def_infers_tool_from_repo() {
  log "generate-def infers tool name from repo"

  cd "$REPO_DIR" || return
  # shellcheck source=/dev/null
  . "$REPO_DIR/tools/lib/env.sh"
  # shellcheck source=/dev/null
  . "$TOOLS_LIB_DIR/generate-def.lib.sh"

  assert_eq "repo basename" "sd" "$(infer_tool_name_from_repo chmln/sd)"
  assert_eq "repo basename strips git suffix" "ripgrep" "$(infer_tool_name_from_repo BurntSushi/ripgrep.git)"
}

test_github_parse_release_tags() {
  log "github parser lists release tags"

  cd "$REPO_DIR" || return
  # shellcheck source=/dev/null
  . "$REPO_DIR/tools/lib/env.sh"
  # shellcheck source=/dev/null
  . "$TOOLS_LIB_DIR/generate-def.lib.sh"

  local json got
  json='[
    {"tag_name": "v1.2.0", "name": "one"},
    {"tag_name": "v1.1.0", "name": "two"}
  ]'
  got="$(github_parse_release_tags "$json")"

  assert_eq "release tags" $'v1.2.0\nv1.1.0' "$got"
}

register_test test_generate_def_infers_tool_from_repo
register_test test_github_parse_release_tags
