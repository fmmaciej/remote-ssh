# shellcheck shell=bash

ensure_this_file_sourced

remote_ssh_cmd_prune_canonical_dir() {
  local dir="$1"

  [[ -d "$dir" ]] || return 1
  cd -P -- "$dir" && pwd -P
}

remote_ssh_cmd_prune_symlink_target_dir() {
  local target prefix relative root

  target="$(remote_ssh_link_target_path "$1")" || return "$?"
  [[ -f "$target" ]] || return 1
  prefix="$(remote_ssh_cmd_prune_canonical_dir "$INSTALL_PREFIX" 2>/dev/null)" || return 1
  prefix="${prefix%/}"
  case "$target" in "$prefix/"*) ;; *) return 1 ;; esac
  relative="${target#"$prefix"/}"
  root="$prefix/${relative%%/*}"
  [[ -d "$root" ]] || return 1
  # Any referenced payload file protects its root. Ownership is checked separately
  # before deletion, without requiring this link to point at the main executable.
  printf '%s\n' "$root"
}

remote_ssh_cmd_prune_protected_release_dirs() (
  local bin_canon inventory link protected_dir resolve_status active

  if ! bin_canon="$(remote_ssh_cmd_prune_canonical_dir "$INSTALL_BIN_DIR" 2>/dev/null)"; then
    printf 'Cannot inspect INSTALL_BIN_DIR: %s\n' "$INSTALL_BIN_DIR" >&2
    return 1
  fi
  if ! [[ -r "$bin_canon" && -x "$bin_canon" ]]; then
    printf 'Cannot read/search INSTALL_BIN_DIR: %s\n' "$INSTALL_BIN_DIR" >&2
    return 1
  fi

  inventory="$(mktemp "${TMPDIR:-/tmp}/remote-ssh-prune-links.XXXXXX")" || {
    printf 'Cannot create active-link inventory for INSTALL_BIN_DIR: %s\n' "$INSTALL_BIN_DIR" >&2
    return 1
  }
  trap 'rm -f -- "$inventory"' EXIT
  # Capture the whole inventory successfully before interpreting any entries.
  # NUL delimiters preserve custom alias names, including embedded newlines.
  if ! find "$bin_canon" -mindepth 1 -maxdepth 1 -type l -print0 >"$inventory"; then
    printf 'Cannot enumerate INSTALL_BIN_DIR: %s\n' "$INSTALL_BIN_DIR" >&2
    return 1
  fi

  active="$INSTALL_PREFIX/.active"
  if [[ -e "$active" || -L "$active" ]]; then
    if ! remote_ssh_active_dir_valid ||
      ! find "$active" -mindepth 1 -maxdepth 1 -type l -print0 >>"$inventory"; then
      printf 'Cannot enumerate active libraries: %s; prune aborted.\n' "$active" >&2
      return 1
    fi
  fi

  # Protect custom and older alias names too, not just aliases in today's defs.
  while IFS= read -r -d '' link; do
    if protected_dir="$(remote_ssh_cmd_prune_symlink_target_dir "$link")"; then
      printf '%s\n' "$protected_dir"
    else
      resolve_status=$?
      if ((resolve_status != 1)); then
        printf 'Cannot read symlink while checking active releases: %s\n' "$link" >&2
        return 1
      fi
    fi
  done <"$inventory"
  return 0
)

remote_ssh_cmd_prune_is_protected_release_dir() {
  local dir="$1" protected="$2"

  [[ -n "$dir" ]] || return 1
  # Newline boundaries give exact entries; quoted data stays literal in the pattern.
  case $'\n'"$protected"$'\n' in
    *$'\n'"$dir"$'\n'*) return 0 ;;
  esac
  return 1
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

  if ! protected="$(remote_ssh_cmd_prune_protected_release_dirs)"; then
    printf 'Cannot determine active tool releases; prune aborted.\n' >&2
    return 1
  fi

  mkdir -p "$INSTALL_PREFIX" || return 1
  prefix_canon="$(remote_ssh_cmd_prune_canonical_dir "$INSTALL_PREFIX")" || {
    printf 'Cannot resolve INSTALL_PREFIX: %s\n' "$INSTALL_PREFIX" >&2
    return 1
  }
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
    if ! remote_ssh_release_validate "$dir"; then
      printf 'protected: %s (legacy or invalid ownership record)\n' "$dir"
      continue
    fi
    remote_ssh_cmd_prune_is_protected_release_dir "$dir_canon" "$protected" && continue

    found=1
    if ((apply == 1)); then
      remote_ssh_release_validate "$dir" || return 1
      rm -rf "$dir" || return 1
      printf 'removed: %s\n' "$dir"
    else
      printf 'candidate: %s\n' "$dir"
    fi
  done < <(find "$prefix_canon" -mindepth 1 -maxdepth 1 -type d -print | sort)

  ((found == 1)) || printf 'No prune candidates.\n'
}
