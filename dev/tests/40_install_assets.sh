#!/usr/bin/env bash
# shellcheck disable=SC2030,SC2031

make_fake_binary() {
  local path="$1"
  printf '#!/usr/bin/env bash\n' >"$path"
  chmod +x "$path"
}

test_stage_tar_gz_asset() {
  log "install stages .tar.gz assets"

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/src/bin" "$tmp/work"
  make_fake_binary "$tmp/src/bin/demo"
  tar -C "$tmp/src" -czf "$tmp/work/demo.tar.gz" .

  (
    cd "$tmp/work" || exit
    # shellcheck source=/dev/null
    . "$REPO_DIR/tools/lib/env.sh"
    # shellcheck source=/dev/null
    . "$TOOLS_LIB_DIR/install-tool.lib.sh"
    stage_downloaded_asset demo.tar.gz demo
    [[ -x "$tmp/work/bin/demo" ]]
  )

  trap - RETURN
  rm -rf "$tmp"
}

register_test test_stage_tar_gz_asset

test_stage_tgz_asset() {
  log "install stages .tgz assets"

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/src/bin" "$tmp/work"
  make_fake_binary "$tmp/src/bin/demo"
  tar -C "$tmp/src" -czf "$tmp/work/demo.tgz" .

  (
    cd "$tmp/work" || exit
    # shellcheck source=/dev/null
    . "$REPO_DIR/tools/lib/env.sh"
    # shellcheck source=/dev/null
    . "$TOOLS_LIB_DIR/install-tool.lib.sh"
    stage_downloaded_asset demo.tgz demo
    [[ -x "$tmp/work/bin/demo" ]]
  )

  trap - RETURN
  rm -rf "$tmp"
}

register_test test_stage_tgz_asset

test_stage_zip_asset() {
  log "install stages .zip assets"

  require_cmd zip
  require_cmd unzip

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/src/bin" "$tmp/work"
  make_fake_binary "$tmp/src/bin/demo"
  (
    cd "$tmp/src" || exit
    zip -qr "$tmp/work/demo.zip" .
  )

  (
    cd "$tmp/work" || exit
    # shellcheck source=/dev/null
    . "$REPO_DIR/tools/lib/env.sh"
    # shellcheck source=/dev/null
    . "$TOOLS_LIB_DIR/install-tool.lib.sh"
    # shellcheck disable=SC2034
    ZIP_SUPPORTED=1
    stage_downloaded_asset demo.zip demo
    [[ -x "$tmp/work/bin/demo" ]]
  )

  trap - RETURN
  rm -rf "$tmp"
}

register_test test_stage_zip_asset

test_stage_raw_executable_asset() {
  log "install stages raw executable assets"

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/work"
  printf '#!/usr/bin/env bash\n' >"$tmp/work/demo-linux-amd64"

  (
    cd "$tmp/work" || exit
    # shellcheck source=/dev/null
    . "$REPO_DIR/tools/lib/env.sh"
    # shellcheck source=/dev/null
    . "$TOOLS_LIB_DIR/install-tool.lib.sh"
    stage_downloaded_asset demo-linux-amd64 demo
    [[ -x "$tmp/work/demo" ]]
  )

  trap - RETURN
  rm -rf "$tmp"
}

register_test test_stage_raw_executable_asset
