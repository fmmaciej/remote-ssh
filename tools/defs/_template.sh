#!/usr/bin/env bash

# Nazwa narzędzia (będzie też nazwą symlinku w ~/.local/bin)
TOOL_NAME=""

# Repozytorium GitHub
GH_REPO=""

# Domyślna wersja (bez "v" - TAG_PREFIX doda ją do URL-a)
# Można zaktualizować ręcznie, albo używać `latest` przy instalacji.
DEFAULT_VERSION=""

# Tag w GitHub Releases ma postać "v1.24.1"
TAG_PREFIX=""

# Nazwa binarki po rozpakowaniu
BINARY_NAME=""

# Nazwa prefixu w pliku assetu:
#   TOOL_NAME-aarch64-unknown-linux-musl.tar.gz
ASSET_PREFIX=""

# Układ nazwy pliku: TOOL_NAME-ARCH-OS.tar.gz
ASSET_TEMPLATE=""

# Architektura: x86_64 -> x86_64, arm64/aarch64 -> aarch64
ARCH_KIND=""

# System: linux -> unknown-linux-musl, darwin -> apple-darwin
OS_KIND=""
