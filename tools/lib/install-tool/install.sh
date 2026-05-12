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

install_binary_validate_link_path() {
  local link_path="$1"

  if [[ -e "$link_path" && ! -L "$link_path" ]]; then
    log_error "Refusing to replace unmanaged path: $link_path"
    return 1
  fi
}

install_binary_cleanup_tmp_links() {
  local tmp_link

  for tmp_link in "$@"; do
    [[ -n "$tmp_link" ]] && rm -f "$tmp_link"
  done
}

install_binary_rollback_links() {
  local entry link_path old_exists old_target

  for entry in "$@"; do
    link_path="${entry%%|*}"
    entry="${entry#*|}"
    old_exists="${entry%%|*}"
    old_target="${entry#*|}"

    rm -f "$link_path"
    if [[ "$old_exists" == "1" ]]; then
      ln -s "$old_target" "$link_path" 2>/dev/null || true
    fi
  done
}

install_binary_switch_links() {
  local target="$1"
  shift

  local link_path tmp_link old_exists old_target
  local -a link_paths=("$@") tmp_links=() rollback_entries=()

  for link_path in "${link_paths[@]}"; do
    install_binary_validate_link_path "$link_path" || return 1
  done

  for link_path in "${link_paths[@]}"; do
    tmp_link="${link_path}.tmp.$$-${RANDOM}"
    ln -s "$target" "$tmp_link" || {
      install_binary_cleanup_tmp_links "${tmp_links[@]}"
      return 1
    }
    tmp_links+=("$tmp_link")
  done

  local i
  for i in "${!link_paths[@]}"; do
    link_path="${link_paths[$i]}"
    tmp_link="${tmp_links[$i]}"
    old_exists=0
    old_target=""

    if [[ -L "$link_path" ]]; then
      old_exists=1
      old_target="$(readlink "$link_path")"
    fi

    if mv -f "$tmp_link" "$link_path"; then
      rollback_entries+=("${link_path}|${old_exists}|${old_target}")
      tmp_links[i]=""
    else
      install_binary_cleanup_tmp_links "${tmp_links[@]}"
      install_binary_rollback_links "${rollback_entries[@]}"
      return 1
    fi
  done
}

install_binary() {
  local tool_name="$1" binary_name="$2" version="$3" extract_dir="$4"
  local -a binary_aliases=("${@:5}")

  local rel target_dir stage_dir release_dir alias_name
  local -a link_paths
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

  link_paths=("$INSTALL_BIN_DIR/$tool_name")
  for alias_name in "${binary_aliases[@]}"; do
    link_paths+=("$INSTALL_BIN_DIR/$alias_name")
  done

  install_binary_switch_links "$release_dir/$binary_name" "${link_paths[@]}" || return 1

  log_info "Installed: $release_dir"
  log_info "Symlink:   $INSTALL_BIN_DIR/$tool_name"

  for alias_name in "${binary_aliases[@]}"; do
    log_info "Alias:     $INSTALL_BIN_DIR/$alias_name"
  done
}
