TOOL_NAME="nvim"
GH_REPO="neovim/neovim"

# Użyjemy standardowego flow:
#   - bez wersji → DEFAULT_VERSION = "stable" (tag "stable")
#   - "latest" → /releases/latest, działa z Twoim get_latest_github_tag
#
# Możesz też ustawić konkretny numer, np. "v0.11.5".
DEFAULT_VERSION="stable"
TAG_PREFIX=""        # bo tag jest "stable" albo "v0.11.5" już jako całość

# Binarka w środku archiwum nazywa się po prostu 'nvim'
BINARY_NAME="nvim"

# Nazwa pliku: nvim-linux-x86_64.tar.gz, nvim-macos-arm64.tar.gz itd.
ASSET_PREFIX="nvim"
ASSET_TEMPLATE="prefix-os-arch"

# Mapowanie arch/OS na schemat neovima
ARCH_KIND="x86_64_arm64"   # x86_64 / arm64
OS_KIND="linux_macos"      # linux / macos
