# shellcheck shell=bash
# shellcheck disable=SC2034

TOOL_NAME="yazi"
GH_REPO="sxyazi/yazi"
RELEASE_TAG="v26.9.1"
VERSION="26.9.1"

BINARY_NAME="yazi"

ASSETS=(
  "darwin:aarch64:any|yazi-aarch64-apple-darwin.zip"
  "darwin:x86_64:any|yazi-x86_64-apple-darwin.zip"
  "linux:aarch64:musl|yazi-aarch64-unknown-linux-musl.zip"
  "linux:x86_64:musl|yazi-x86_64-unknown-linux-musl.zip"
  "linux:aarch64:gnu|yazi-aarch64-unknown-linux-gnu.zip"
  "linux:x86_64:gnu|yazi-x86_64-unknown-linux-gnu.zip"
)

CHECKSUMS=(
  "yazi-aarch64-apple-darwin.zip|3921182a21cceb0a505e5dac578e1487d48104caa5f114e9f8adf40b5a7289a9"
  "yazi-x86_64-apple-darwin.zip|36e09036fcc446488d876d139a5e303f2443b82cfb6ac7dfcb43892d6fe6fa20"
  "yazi-aarch64-unknown-linux-musl.zip|dd569daecaae914185f295634109295ccd25c1b42b02eb89a74f651970024f2e"
  "yazi-x86_64-unknown-linux-musl.zip|9b9c39decccf8cb0ff53a7d637d38f8a79d93bbd0099f4ea9c619ef6bb392f5d"
  "yazi-aarch64-unknown-linux-gnu.zip|02807f08d6b589b65b7516a4e259d83f5995d7a23bb12b3a155141385b370b3a"
  "yazi-x86_64-unknown-linux-gnu.zip|a02fe91d3304294048c681f010f1100856872a4e98ecf6927328e888d40a6ad2"
)
