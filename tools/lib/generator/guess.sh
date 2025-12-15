# shellcheck shell=bash

ensure_this_file_sourced

# guess_os_kind <asset_name>
# Input: asset filename
# Output: echoes OS_KIND for map_os() ("rust_triple", "rust_musl", "linux_macos", "linux_darwin")
guess_os_kind() {
  local n="${1,,}"

  # nvim assets use "macos"
  [[ "$n" =~ (^|[^a-z])macos([^a-z]|$) ]]         && { echo "linux_macos"; return; }
  [[ "$n" =~ unknown-linux-musl ]]                && { echo "rust_musl"; return; }
  [[ "$n" =~ (unknown-linux-gnu|apple-darwin) ]]  && { echo "rust_triple"; return; }

  echo "linux_darwin"
}

# guess_arch_kind <asset_name>
# Output: echoes ARCH_KIND
guess_arch_kind() {
  local n="${1,,}"

  # nvim: x86_64 + arm64 (nie amd64!)
  [[ "$n" == *nvim-* ]] && [[ "$n" == *x86_64* ]] && [[ "$n" == *arm64* ]] && {
    echo "x86_64_arm64"
    return
  }

  # fzf-style: amd64/arm64
  [[ "$n" =~ (_amd64|_arm64|amd64|arm64) ]] && { echo "amd64_arm64"; return; }

  # nvim-ish: arm64 but not aarch64 token
  [[ "$n" =~ arm64 && ! "$n" =~ aarch64 ]] && { echo "x86_64_arm64"; return; }

  echo "x86_64_aarch64"
}

# guess_template <asset_name>
# Output: echoes ASSET_TEMPLATE
guess_template() {
  local n="${1,,}"

  # nvim: bez wersji w nazwie
  [[ "$n" =~ (^|/)nvim-(macos|linux)- ]] && { echo "prefix-os-arch"; return; }

  # fzf: ...-linux_amd64.tar.gz
  [[ "$n" =~ _[a-z0-9]+\.tar\.gz$ ]] && { echo "prefix-version-os_arch"; return; }

  # zip tools
  [[ "$n" =~ \.zip$ ]] && { echo "prefix-arch-os"; return; }

  # starship-like: brak wersji, zaczyna się od arch (np. starship-x86_64-unknown-linux-gnu.tar.gz)
  [[ "$n" =~ ^[a-z0-9._-]+-(x86_64|aarch64|arm64|amd64)-.+\.tar\.gz$ ]] \
    && [[ ! "$n" =~ -v?[0-9]+\.[0-9]+ ]] && { echo "prefix-arch-os-tgz"; return; }

  # default: rustowe "prefix-version-arch-os"
  echo "prefix-version-arch-os"
}
