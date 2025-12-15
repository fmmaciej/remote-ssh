# shellcheck shell=bash

ensure_this_file_sourced

# --- guess mapping kinds (your common.sh conventions) ---
guess_os_kind() {
  local n="$1"
  if [[ "$n" =~ unknown-linux-musl ]];  then echo "rust_musl"; return; fi
  if [[ "$n" =~ unknown-linux-gnu ]];   then echo "rust_triple"; return; fi
  if [[ "$n" =~ apple-darwin ]];        then echo "rust_triple"; return; fi
  if [[ "$n" =~ macos ]];               then echo "linux_macos"; return; fi

  echo "linux_darwin"
}

guess_arch_kind() {
  local n="$1"

  # fzf często: linux_amd64 / darwin_arm64
  if [[ "$n" =~ (_amd64|_arm64|amd64|arm64) ]]; then echo "amd64_arm64"; return; fi

  # nvim: arm64 (nie aarch64) => x86_64_arm64
  if [[ "$n" =~ arm64 && ! "$n" =~ aarch64 ]];  then echo "x86_64_arm64"; return; fi

  echo "x86_64_aarch64"
}

guess_template() {
  local n="$1"

  # starship: starship-x86_64-unknown-linux-musl.tar.gz / starship-aarch64-apple-darwin.tar.gz
  if [[ "$n" =~ ^starship-(x86_64|aarch64)-(unknown-linux-(musl|gnu)|apple-darwin)\.tar\.gz$ ]]; then
    echo "prefix-arch-os-tgz"
    return
  fi

  # fzf: fzf-0.67.0-linux_amd64.tar.gz
  if [[ "$n" =~ _[a-z0-9]+\.tar\.gz$ ]];    then echo "prefix-version-os_arch"; return; fi

  # nvim: nvim-macos-arm64.tar.gz / nvim-linux-x86_64.tar.gz
  if [[ "$n" =~ (^|-)macos-|(^|-)linux- ]]; then echo "prefix-os-arch"; return; fi

  # yazi: ...zip
  if [[ "$n" =~ \.zip$ ]];                  then echo "prefix-arch-os"; return; fi

  echo "prefix-version-arch-os"
}

