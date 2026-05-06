#!/usr/bin/env bash

generated_asset_contract() {
  source_tool_libs

  # shellcheck disable=SC2329
  emit_tool_asset_contract() {
    local _def="$1"
    local rec key asset

    for rec in "${ASSETS[@]}"; do
      key="$(manifest_asset_key "$rec")"
      asset="$(manifest_asset_name "$rec")"
      printf '%s|%s|%s\n' "$TOOL_NAME" "$key" "$asset"
    done
  }

  with_each_tool_def emit_tool_asset_contract
}

test_asset_name_mappings() {
  log "tool exact asset manifest"

  local expected got
expected="$(cat <<'EOF'
atuin|darwin:aarch64:any|atuin-aarch64-apple-darwin.tar.gz
atuin|linux:aarch64:gnu|atuin-aarch64-unknown-linux-gnu.tar.gz
atuin|linux:aarch64:musl|atuin-aarch64-unknown-linux-musl.tar.gz
atuin|linux:x86_64:gnu|atuin-x86_64-unknown-linux-gnu.tar.gz
atuin|linux:x86_64:musl|atuin-x86_64-unknown-linux-musl.tar.gz
bat|darwin:aarch64:any|bat-v0.26.1-aarch64-apple-darwin.tar.gz
bat|darwin:x86_64:any|bat-v0.26.1-x86_64-apple-darwin.tar.gz
bat|linux:aarch64:musl|bat-v0.26.1-aarch64-unknown-linux-musl.tar.gz
bat|linux:x86_64:musl|bat-v0.26.1-x86_64-unknown-linux-musl.tar.gz
bat|linux:aarch64:gnu|bat-v0.26.1-aarch64-unknown-linux-gnu.tar.gz
bat|linux:x86_64:gnu|bat-v0.26.1-x86_64-unknown-linux-gnu.tar.gz
eza|linux:aarch64:gnu|eza_aarch64-unknown-linux-gnu.tar.gz
eza|linux:x86_64:musl|eza_x86_64-unknown-linux-musl.tar.gz
eza|linux:x86_64:gnu|eza_x86_64-unknown-linux-gnu.tar.gz
fd|darwin:aarch64:any|fd-v10.3.0-aarch64-apple-darwin.tar.gz
fd|darwin:x86_64:any|fd-v10.3.0-x86_64-apple-darwin.tar.gz
fd|linux:aarch64:musl|fd-v10.3.0-aarch64-unknown-linux-musl.tar.gz
fd|linux:x86_64:musl|fd-v10.3.0-x86_64-unknown-linux-musl.tar.gz
fd|linux:aarch64:gnu|fd-v10.3.0-aarch64-unknown-linux-gnu.tar.gz
fd|linux:x86_64:gnu|fd-v10.3.0-x86_64-unknown-linux-gnu.tar.gz
fzf|darwin:x86_64:any|fzf-0.67.0-darwin_amd64.tar.gz
fzf|darwin:aarch64:any|fzf-0.67.0-darwin_arm64.tar.gz
fzf|linux:x86_64:any|fzf-0.67.0-linux_amd64.tar.gz
fzf|linux:aarch64:any|fzf-0.67.0-linux_arm64.tar.gz
nu|darwin:aarch64:any|nu-0.112.2-aarch64-apple-darwin.tar.gz
nu|darwin:x86_64:any|nu-0.112.2-x86_64-apple-darwin.tar.gz
nu|linux:aarch64:musl|nu-0.112.2-aarch64-unknown-linux-musl.tar.gz
nu|linux:x86_64:musl|nu-0.112.2-x86_64-unknown-linux-musl.tar.gz
nu|linux:aarch64:gnu|nu-0.112.2-aarch64-unknown-linux-gnu.tar.gz
nu|linux:x86_64:gnu|nu-0.112.2-x86_64-unknown-linux-gnu.tar.gz
nvim|linux:aarch64:gnu|nvim-linux-arm64.tar.gz
nvim|linux:x86_64:gnu|nvim-linux-x86_64.tar.gz
nvim|darwin:aarch64:any|nvim-macos-arm64.tar.gz
nvim|darwin:x86_64:any|nvim-macos-x86_64.tar.gz
rg|darwin:aarch64:any|ripgrep-15.1.0-aarch64-apple-darwin.tar.gz
rg|darwin:x86_64:any|ripgrep-15.1.0-x86_64-apple-darwin.tar.gz
rg|linux:x86_64:musl|ripgrep-15.1.0-x86_64-unknown-linux-musl.tar.gz
rg|linux:aarch64:gnu|ripgrep-15.1.0-aarch64-unknown-linux-gnu.tar.gz
starship|darwin:aarch64:any|starship-aarch64-apple-darwin.tar.gz
starship|darwin:x86_64:any|starship-x86_64-apple-darwin.tar.gz
starship|linux:aarch64:musl|starship-aarch64-unknown-linux-musl.tar.gz
starship|linux:x86_64:musl|starship-x86_64-unknown-linux-musl.tar.gz
starship|linux:x86_64:gnu|starship-x86_64-unknown-linux-gnu.tar.gz
yazi|darwin:aarch64:any|yazi-aarch64-apple-darwin.zip
yazi|darwin:x86_64:any|yazi-x86_64-apple-darwin.zip
yazi|linux:aarch64:musl|yazi-aarch64-unknown-linux-musl.zip
yazi|linux:x86_64:musl|yazi-x86_64-unknown-linux-musl.zip
yazi|linux:aarch64:gnu|yazi-aarch64-unknown-linux-gnu.zip
yazi|linux:x86_64:gnu|yazi-x86_64-unknown-linux-gnu.zip
zoxide|darwin:aarch64:any|zoxide-0.9.9-aarch64-apple-darwin.tar.gz
zoxide|darwin:x86_64:any|zoxide-0.9.9-x86_64-apple-darwin.tar.gz
zoxide|linux:aarch64:musl|zoxide-0.9.9-aarch64-unknown-linux-musl.tar.gz
zoxide|linux:x86_64:musl|zoxide-0.9.9-x86_64-unknown-linux-musl.tar.gz
EOF
)"
  got="$(generated_asset_contract)"

  assert_eq "asset manifest contract" "$expected" "$got"
}

linux_gnu_selection_contract() {
  source_tool_selector_libs

  # shellcheck disable=SC2329
  emit_linux_gnu_selection_contract() {
    local _def="$1"
    local platform raw_os raw_arch libc asset

    for platform in linux:x86_64:gnu linux:aarch64:gnu; do
      IFS=: read -r raw_os raw_arch libc <<<"$platform"
      asset="$(selected_asset_name "$raw_os" "$raw_arch" "$libc")"
      printf '%s|%s|%s\n' "$TOOL_NAME" "$platform" "$asset"
    done
  }

  with_each_tool_def emit_linux_gnu_selection_contract
}

test_linux_gnu_asset_selection() {
  log "linux glibc hosts prefer portable variants"

  local expected got
expected="$(cat <<'EOF'
atuin|linux:x86_64:gnu|atuin-x86_64-unknown-linux-musl.tar.gz
atuin|linux:aarch64:gnu|atuin-aarch64-unknown-linux-musl.tar.gz
bat|linux:x86_64:gnu|bat-v0.26.1-x86_64-unknown-linux-musl.tar.gz
bat|linux:aarch64:gnu|bat-v0.26.1-aarch64-unknown-linux-musl.tar.gz
eza|linux:x86_64:gnu|eza_x86_64-unknown-linux-musl.tar.gz
eza|linux:aarch64:gnu|eza_aarch64-unknown-linux-gnu.tar.gz
fd|linux:x86_64:gnu|fd-v10.3.0-x86_64-unknown-linux-musl.tar.gz
fd|linux:aarch64:gnu|fd-v10.3.0-aarch64-unknown-linux-musl.tar.gz
fzf|linux:x86_64:gnu|fzf-0.67.0-linux_amd64.tar.gz
fzf|linux:aarch64:gnu|fzf-0.67.0-linux_arm64.tar.gz
nu|linux:x86_64:gnu|nu-0.112.2-x86_64-unknown-linux-musl.tar.gz
nu|linux:aarch64:gnu|nu-0.112.2-aarch64-unknown-linux-musl.tar.gz
nvim|linux:x86_64:gnu|nvim-linux-x86_64.tar.gz
nvim|linux:aarch64:gnu|nvim-linux-arm64.tar.gz
rg|linux:x86_64:gnu|ripgrep-15.1.0-x86_64-unknown-linux-musl.tar.gz
rg|linux:aarch64:gnu|ripgrep-15.1.0-aarch64-unknown-linux-gnu.tar.gz
starship|linux:x86_64:gnu|starship-x86_64-unknown-linux-musl.tar.gz
starship|linux:aarch64:gnu|starship-aarch64-unknown-linux-musl.tar.gz
yazi|linux:x86_64:gnu|yazi-x86_64-unknown-linux-musl.zip
yazi|linux:aarch64:gnu|yazi-aarch64-unknown-linux-musl.zip
zoxide|linux:x86_64:gnu|zoxide-0.9.9-x86_64-unknown-linux-musl.tar.gz
zoxide|linux:aarch64:gnu|zoxide-0.9.9-aarch64-unknown-linux-musl.tar.gz
EOF
)"
  got="$(linux_gnu_selection_contract)"

  assert_eq "linux glibc selection contract" "$expected" "$got"
}

test_linux_glibc_asset_fallback() {
  log "linux glibc hosts fall back to glibc asset"

  source_tool_selector_libs

  local -a ASSETS=(
    "linux:x86_64:glibc|tool-x86_64-linux-glibc.tgz"
    "linux:x86_64:any|tool-x86_64-linux-any.tgz"
  )
  local got
  got="$(select_asset linux x86_64 gnu "${ASSETS[@]}")"

  assert_eq "linux glibc fallback" "tool-x86_64-linux-glibc.tgz" "$got"
}

test_linux_any_asset_fallback() {
  log "linux hosts fall back to any asset"

  source_tool_selector_libs

  local -a ASSETS=(
    "linux:x86_64:any|tool-x86_64-linux-any.tgz"
  )
  local got
  got="$(select_asset linux x86_64 gnu "${ASSETS[@]}")"

  assert_eq "linux any fallback" "tool-x86_64-linux-any.tgz" "$got"
}

test_asset_selection_no_match() {
  log "asset selection reports no match"

  source_tool_selector_libs

  local -a ASSETS=(
    "linux:x86_64:any|tool-x86_64-linux-any.tgz"
  )

  if select_asset darwin aarch64 any "${ASSETS[@]}" >/dev/null; then
    printf 'Expected no matching asset for darwin/aarch64/any\n' >&2
    return 1
  fi
}

register_test test_asset_name_mappings
register_test test_linux_gnu_asset_selection
register_test test_linux_glibc_asset_fallback
register_test test_linux_any_asset_fallback
register_test test_asset_selection_no_match
