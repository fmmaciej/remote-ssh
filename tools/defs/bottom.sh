# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="bottom"
GH_REPO="ClementTsang/bottom"
RELEASE_TAG="0.12.3"
VERSION="0.12.3"

BINARY_NAME="btm"
BINARY_ALIASES=("btm")

ASSETS=(
  "darwin:aarch64:any|bottom_aarch64-apple-darwin.tar.gz"
  "darwin:x86_64:any|bottom_x86_64-apple-darwin.tar.gz"
  "linux:aarch64:gnu|bottom_aarch64-unknown-linux-gnu.tar.gz"
  "linux:aarch64:musl|bottom_aarch64-unknown-linux-musl.tar.gz"
  "linux:x86_64:gnu|bottom_x86_64-unknown-linux-gnu-2-17.tar.gz"
  "linux:x86_64:musl|bottom_x86_64-unknown-linux-musl.tar.gz"
)

CHECKSUMS=(
  "bottom_aarch64-apple-darwin.tar.gz|106e9493d20192d18dbe46d4c99f680d817c796724103ee258567070fcd16429"
  "bottom_x86_64-apple-darwin.tar.gz|5744b5c78db14b85e025c31ded93ba038041e6ff2e8c16ea1d2f9bdb6487316f"
  "bottom_aarch64-unknown-linux-gnu.tar.gz|5138f2fab99e267073ad542de0e3da85af842761e8083127161073d4a8ef25b2"
  "bottom_aarch64-unknown-linux-musl.tar.gz|944f372beeaac326cbe3eb4424d7bae600173cec2b0bba363557cd72cc98a3e2"
  "bottom_x86_64-unknown-linux-gnu-2-17.tar.gz|3a53ecaf07d1a2e2c50081a5e752e44c9d01fd5d8dc53cfe647959f77a2b4b4e"
  "bottom_x86_64-unknown-linux-musl.tar.gz|0d6352079422fda8f4ee242eb849f45a6008db96d6c1cd35e8436babc51bc33f"
)
