# shellcheck shell=bash

ensure_this_file_sourced

remote_ssh_cmd_prune_canonical_dir() {
  local dir="$1"

  [[ -d "$dir" ]] || return 1
  cd "$dir" && pwd -P
}

remote_ssh_cmd_prune_symlink_target_dir() {
  local link="$1"
  local target target_dir

  [[ -L "$link" ]] || return 1
  target="$(readlink "$link")"
  case "$target" in
    /*) target_dir="$(dirname "$target")" ;;
    *) target_dir="$(dirname "$link")/$(dirname "$target")" ;;
  esac

  remote_ssh_cmd_prune_canonical_dir "$target_dir"
}

remote_ssh_cmd_prune_protected_release_dirs() {
  local def_dir="$TOOLS_DIR/defs"
  local def_file tool alias_name link protected_dir
  local -a aliases

  for def_file in "$def_dir"/*.sh; do
    tool="$(basename "$def_file" .sh)"
    load_defs "$def_dir" "$tool"

    link="$INSTALL_BIN_DIR/$TOOL_NAME"
    if protected_dir="$(remote_ssh_cmd_prune_symlink_target_dir "$link")"; then
      printf '%s\n' "$protected_dir"
    fi

    set +u
    aliases=("${BINARY_ALIASES[@]}")
    for alias_name in "${aliases[@]}"; do
      link="$INSTALL_BIN_DIR/$alias_name"
      if protected_dir="$(remote_ssh_cmd_prune_symlink_target_dir "$link")"; then
        printf '%s\n' "$protected_dir"
      fi
    done
    set -u
  done
}

remote_ssh_cmd_prune_is_protected_release_dir() {
  local dir="$1" protected="$2"

  grep -Fx -- "$dir" <<<"$protected" >/dev/null
}

remote_ssh_cmd_prune_is_known_release_dir_name() {
  local name="$1" def_dir="$TOOLS_DIR/defs" def_file tool

  for def_file in "$def_dir"/*.sh; do
    tool="$(basename "$def_file" .sh)"
    load_defs "$def_dir" "$tool"
    case "$name" in
      "$TOOL_NAME"-*) return 0 ;;
    esac
  done

  return 1
}

remote_ssh_cmd_prune_is_direct_child_of_prefix() {
  local candidate="$1" prefix="$2"

  [[ "$(dirname "$candidate")" == "$prefix" ]]
}

remote_ssh_cmd_prune_main() {
  remote_ssh_cmd_require_install_libs

  local apply=0 arg protected dir name found=0
  local prefix_canon dir_canon

  for arg in "$@"; do
    case "$arg" in
      --apply) apply=1 ;;
      -h|--help)
        printf 'Usage: remote-ssh prune [--apply]\n' >&2
        return 0
        ;;
      *) printf 'Unknown prune argument: %s\n' "$arg" >&2; return 1 ;;
    esac
  done

  mkdir -p "$INSTALL_PREFIX"
  prefix_canon="$(remote_ssh_cmd_prune_canonical_dir "$INSTALL_PREFIX")" || {
    printf 'Cannot resolve INSTALL_PREFIX: %s\n' "$INSTALL_PREFIX" >&2
    return 1
  }
  protected="$(remote_ssh_cmd_prune_protected_release_dirs | sort -u)"

  if ((apply == 1)); then
    printf 'remote-ssh prune --apply\n'
  else
    printf 'remote-ssh prune (dry-run)\n'
  fi

  while IFS= read -r dir; do
    [[ -n "$dir" ]] || continue
    dir_canon="$(remote_ssh_cmd_prune_canonical_dir "$dir")" || continue
    remote_ssh_cmd_prune_is_direct_child_of_prefix "$dir_canon" "$prefix_canon" || continue
    name="$(basename "$dir")"
    remote_ssh_cmd_prune_is_known_release_dir_name "$name" || continue
    remote_ssh_cmd_prune_is_protected_release_dir "$dir_canon" "$protected" && continue

    found=1
    if ((apply == 1)); then
      rm -rf "$dir"
      printf 'removed: %s\n' "$dir"
    else
      printf 'candidate: %s\n' "$dir"
    fi
  done < <(find "$INSTALL_PREFIX" -mindepth 1 -maxdepth 1 -type d -print | sort)

  ((found == 1)) || printf 'No prune candidates.\n'
}
