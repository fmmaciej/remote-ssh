# shellcheck shell=bash

ensure_this_file_sourced

find_binary_path_by_name() {
  local extract_dir="$1" bin_name="$2"
  local bin

  bin="$(find "$extract_dir" -maxdepth 4 -type f -name "$bin_name" | head -n1)"
  bin="${bin#"$extract_dir"/}"

  echo "$bin"
}

make_install_staging_dir() {
  local tool_name="$1" version="$2"
  local tmp attempts_left=20

  while ((attempts_left > 0)); do
    tmp="${INSTALL_PREFIX}/.${tool_name}-${version}.tmp.$$-${RANDOM}"
    if mkdir "$tmp" 2>/dev/null; then
      echo "$tmp"
      return 0
    fi
    ((attempts_left--))
  done

  log_error "Could not create staging directory for ${tool_name}-${version}"
  return 1
}

choose_release_dir() {
  local tool_name="$1" version="$2" canonical_dir="$3"
  local release_dir attempts_left=20

  if [[ ! -e $canonical_dir ]]; then
    echo "$canonical_dir"
    return 0
  fi

  while ((attempts_left > 0)); do
    release_dir="${INSTALL_PREFIX}/${tool_name}-${version}.$$-${RANDOM}"
    if [[ ! -e $release_dir ]]; then
      echo "$release_dir"
      return 0
    fi
    ((attempts_left--))
  done

  log_error "Could not choose release directory for ${tool_name}-${version}"
  return 1
}

atomic_symlink() {
  local target="$1" link_path="$2"
  local tmp_link

  tmp_link="${link_path}.tmp.$$-${RANDOM}"
  ln -s "$target" "$tmp_link" || return 1
  mv -f "$tmp_link" "$link_path" || {
    rm -f "$tmp_link"
    return 1
  }
}

install_binary() {
  local tool_name="$1" binary_name="$2" version="$3" extract_dir="$4"
  local -a binary_aliases=("${@:5}")

  local rel target_dir stage_dir release_dir alias_name
  rel="$(find_binary_path_by_name "$extract_dir" "$binary_name")"

  [[ -n $rel ]] || {
    log_error "Binary '$binary_name' not found"
    return 1
  }
  [[ -x "$extract_dir/$rel" ]] || {
    log_error "Not executable: $extract_dir/$rel"
    return 1
  }

  target_dir="${INSTALL_PREFIX}/${tool_name}-${version}"
  mkdir -p "$INSTALL_PREFIX" "$INSTALL_BIN_DIR"

  stage_dir="$(make_install_staging_dir "$tool_name" "$version")" || return 1
  cp "$extract_dir/$rel" "$stage_dir/$binary_name" || {
    rm -rf "$stage_dir"
    return 1
  }
  chmod +x "$stage_dir/$binary_name" || {
    rm -rf "$stage_dir"
    return 1
  }

  release_dir="$(choose_release_dir "$tool_name" "$version" "$target_dir")" || {
    rm -rf "$stage_dir"
    return 1
  }
  mv "$stage_dir" "$release_dir" || {
    rm -rf "$stage_dir"
    return 1
  }

  atomic_symlink "$release_dir/$binary_name" "$INSTALL_BIN_DIR/$tool_name" || return 1

  log_info "Installed: $release_dir"
  log_info "Symlink:   $INSTALL_BIN_DIR/$tool_name"

  for alias_name in "${binary_aliases[@]}"; do
    atomic_symlink "$release_dir/$binary_name" "$INSTALL_BIN_DIR/$alias_name" || return 1
    log_info "Alias:     $INSTALL_BIN_DIR/$alias_name"
  done
}
