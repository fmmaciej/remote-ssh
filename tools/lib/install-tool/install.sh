# shellcheck shell=bash

ensure_this_file_sourced

find_binary_path_by_name() {
  local extract_dir="$1" bin_name="$2"
  local bin

  bin="$(find "$extract_dir" -maxdepth 4 -type f -name "$bin_name" | head -n1)"
  bin="${bin#"$extract_dir"/}"

  echo "$bin"
}

install_binary() {
  local tool_name="$1" binary_name="$2" version="$3" extract_dir="$4"

  local rel target_dir
  rel="$(find_binary_path_by_name "$extract_dir" "$binary_name")"

  [[ -n "$rel" ]] || { log_error "Binary '$binary_name' not found"; return 1; }
  [[ -x "$extract_dir/$rel" ]] || { log_error "Not executable: $extract_dir/$rel"; return 1; }

  target_dir="${INSTALL_PREFIX}/${tool_name}-${version}"

  rm -rf "$target_dir"
  mkdir -p "$target_dir"

  cp "$extract_dir/$rel" "$target_dir/"
  ln -sf "$target_dir/$binary_name" "$INSTALL_BIN_DIR/$tool_name"

  log_info "Installed: $target_dir"
  log_info "Symlink:   $INSTALL_BIN_DIR/$tool_name"
}
