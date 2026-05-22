# shellcheck shell=bash

ensure_this_file_sourced

remote_ssh_cmd_uninstall_usage() {
  cat <<'EOF'
Usage:
  remote-ssh uninstall [--yes] [tool ...]

Uninstalls managed remote-ssh tools. Without tool arguments, uninstalls all
managed tools detected from symlinks in INSTALL_BIN_DIR.

Options:
  --yes       Skip confirmation prompt
  -h, --help  Show this help
EOF
}

remote_ssh_cmd_uninstall_print_list() {
  local title="$1"
  shift

  printf '%s\n' "$title"
  if (($# == 0)); then
    printf '  [none]\n'
    return 0
  fi

  printf '  %s\n' "$@"
}

remote_ssh_cmd_uninstall_append_unique() {
  local value="$1"
  shift
  local item

  for item in "$@"; do
    [[ "$item" == "$value" ]] && return 1
  done

  printf '%s\n' "$value"
}

remote_ssh_cmd_uninstall_confirm() {
  local answer

  if ! [[ -t 0 ]]; then
    printf 'remote-ssh uninstall requires confirmation. Use --yes for non-interactive uninstall.\n' >&2
    return 1
  fi

  printf '\nUninstall selected managed tools? [y/N] '
  read -r answer
  case "$answer" in
    y | Y | yes | YES) return 0 ;;
    *) printf 'Aborted.\n' >&2; return 1 ;;
  esac
}

remote_ssh_cmd_uninstall_canonical_dir() {
  local dir="$1"

  [[ -d "$dir" ]] || return 1
  (cd "$dir" && pwd -P)
}

remote_ssh_cmd_uninstall_link_target_path() {
  local link="$1" target

  [[ -L "$link" ]] || return 1
  target="$(readlink "$link")"
  case "$target" in
    /*) printf '%s\n' "$target" ;;
    *) printf '%s/%s\n' "$(dirname "$link")" "$target" ;;
  esac
}

remote_ssh_cmd_uninstall_managed_link_target() {
  local link="$1" prefix_canon="$2"
  local target target_dir target_dir_canon target_path

  target="$(remote_ssh_cmd_uninstall_link_target_path "$link")" || return 1
  target_dir="$(dirname "$target")"

  if target_dir_canon="$(remote_ssh_cmd_uninstall_canonical_dir "$target_dir")"; then
    target_path="${target_dir_canon}/$(basename "$target")"
    case "$target_path" in
      "$prefix_canon"/*)
        printf '%s\n' "$target_path"
        return 0
        ;;
    esac
  fi

  case "$target" in
    "$INSTALL_PREFIX"/*)
      printf '%s\n' "$target"
      return 0
      ;;
  esac

  return 1
}

remote_ssh_cmd_uninstall_collect_links_for_tool() {
  local tool="$1" prefix_canon="$2"
  local link_path target alias_name
  local -a link_names

  load_defs "$TOOLS_DIR/defs" "$tool"
  link_names=("$TOOL_NAME")
  for alias_name in ${BINARY_ALIASES[@]+"${BINARY_ALIASES[@]}"}; do
    link_names+=("$alias_name")
  done

  for alias_name in ${link_names[@]+"${link_names[@]}"}; do
    link_path="$INSTALL_BIN_DIR/$alias_name"
    if [[ -L "$link_path" ]]; then
      if target="$(remote_ssh_cmd_uninstall_managed_link_target "$link_path" "$prefix_canon")"; then
        printf 'remove|%s\n' "$link_path"
      else
        printf 'protect|%s -> %s\n' "$link_path" "$(readlink "$link_path")"
      fi
    elif [[ -e "$link_path" ]]; then
      printf 'protect|%s (not a symlink)\n' "$link_path"
    fi
  done
}

remote_ssh_cmd_uninstall_collect_release_dirs_for_tool() {
  local tool="$1" prefix_canon="$2"
  local dir dir_canon name

  load_defs "$TOOLS_DIR/defs" "$tool"

  [[ -d "$INSTALL_PREFIX" ]] || return 0
  while IFS= read -r dir; do
    [[ -n "$dir" ]] || continue
    name="$(basename "$dir")"
    case "$name" in
      "$TOOL_NAME"-*) ;;
      *) continue ;;
    esac

    dir_canon="$(remote_ssh_cmd_uninstall_canonical_dir "$dir")" || continue
    [[ "$(dirname "$dir_canon")" == "$prefix_canon" ]] || continue
    printf '%s\n' "$dir"
  done < <(find "$INSTALL_PREFIX" -mindepth 1 -maxdepth 1 -type d -print | sort)
}

remote_ssh_cmd_uninstall_managed_tools() {
  local prefix_canon="$1"
  local tool link_path

  for tool in $(all_known_tools); do
    load_defs "$TOOLS_DIR/defs" "$tool"
    link_path="$INSTALL_BIN_DIR/$TOOL_NAME"
    [[ -L "$link_path" ]] || continue
    remote_ssh_cmd_uninstall_managed_link_target "$link_path" "$prefix_canon" >/dev/null || continue
    printf '%s\n' "$tool"
  done
}

remote_ssh_cmd_uninstall_expected_plan() {
  local tool expected changed=0
  local -a selected=("$@") kept=()

  REMOTE_SSH_UNINSTALL_EXPECTED_ACTION="none"
  REMOTE_SSH_UNINSTALL_EXPECTED_FILE="$(expected_tools_file)"
  REMOTE_SSH_UNINSTALL_EXPECTED_KEEP=()

  expected_tools_exists || return 0

  while IFS= read -r expected; do
    [[ -n "$expected" ]] || continue
    for tool in ${selected[@]+"${selected[@]}"}; do
      if [[ "$expected" == "$tool" ]]; then
        changed=1
        continue 2
      fi
    done
    kept+=("$expected")
  done < <(read_expected_tools)

  ((changed == 1)) || return 0

  REMOTE_SSH_UNINSTALL_EXPECTED_KEEP=()
  for tool in ${kept[@]+"${kept[@]}"}; do
    REMOTE_SSH_UNINSTALL_EXPECTED_KEEP+=("$tool")
  done
  if ((${#kept[@]} == 0)); then
    REMOTE_SSH_UNINSTALL_EXPECTED_ACTION="remove"
  else
    REMOTE_SSH_UNINSTALL_EXPECTED_ACTION="rewrite"
  fi
}

remote_ssh_cmd_uninstall_print_expected_action() {
  case "$REMOTE_SSH_UNINSTALL_EXPECTED_ACTION" in
    remove)
      printf 'Expected tools action:\n'
      printf '  remove %s\n' "$REMOTE_SSH_UNINSTALL_EXPECTED_FILE"
      ;;
    rewrite)
      printf 'Expected tools action:\n'
      printf '  rewrite %s\n' "$REMOTE_SSH_UNINSTALL_EXPECTED_FILE"
      remote_ssh_cmd_uninstall_print_list "  remaining expected tools:" ${REMOTE_SSH_UNINSTALL_EXPECTED_KEEP[@]+"${REMOTE_SSH_UNINSTALL_EXPECTED_KEEP[@]}"}
      ;;
    *)
      printf 'Expected tools action:\n'
      printf '  [none]\n'
      ;;
  esac
}

remote_ssh_cmd_uninstall_apply_expected_action() {
  case "$REMOTE_SSH_UNINSTALL_EXPECTED_ACTION" in
    remove)
      rm -f "$REMOTE_SSH_UNINSTALL_EXPECTED_FILE"
      printf 'removed expected tools config: %s\n' "$REMOTE_SSH_UNINSTALL_EXPECTED_FILE"
      ;;
    rewrite)
      write_expected_tools ${REMOTE_SSH_UNINSTALL_EXPECTED_KEEP[@]+"${REMOTE_SSH_UNINSTALL_EXPECTED_KEEP[@]}"}
      printf 'updated expected tools config: %s\n' "$REMOTE_SSH_UNINSTALL_EXPECTED_FILE"
      ;;
  esac
}

remote_ssh_cmd_uninstall_main() {
  remote_ssh_cmd_require_install_libs

  local arg yes=0 explicit=0 tool record kind value prefix_canon
  local changes=0
  local -a requested=() selected=() symlinks=() protected=() release_dirs=()

  while (($# > 0)); do
    arg="$1"
    case "$arg" in
      --yes)
        yes=1
        shift
        ;;
      -h | --help)
        remote_ssh_cmd_uninstall_usage
        return 0
        ;;
      -*)
        printf 'Unknown remote-ssh uninstall option: %s\n' "$arg" >&2
        remote_ssh_cmd_uninstall_usage >&2
        return 1
        ;;
      *)
        explicit=1
        requested+=("$arg")
        shift
        ;;
    esac
  done

  if [[ -d "$INSTALL_PREFIX" ]]; then
    prefix_canon="$(remote_ssh_cmd_uninstall_canonical_dir "$INSTALL_PREFIX")" || {
      printf 'Cannot resolve INSTALL_PREFIX: %s\n' "$INSTALL_PREFIX" >&2
      return 1
    }
  else
    prefix_canon="$INSTALL_PREFIX"
  fi

  if ((explicit == 1)); then
    for tool in ${requested[@]+"${requested[@]}"}; do
      if ! known_tool "$tool"; then
        printf 'Unknown tool: %s\n' "$tool" >&2
        return 1
      fi
      if value="$(remote_ssh_cmd_uninstall_append_unique "$tool" ${selected[@]+"${selected[@]}"})"; then
        selected+=("$value")
      fi
    done
  else
    while IFS= read -r tool; do
      [[ -n "$tool" ]] && selected+=("$tool")
    done < <(remote_ssh_cmd_uninstall_managed_tools "$prefix_canon")
  fi

  remote_ssh_cmd_uninstall_expected_plan ${selected[@]+"${selected[@]}"}

  for tool in ${selected[@]+"${selected[@]}"}; do
    while IFS= read -r record; do
      [[ -n "$record" ]] || continue
      kind="${record%%|*}"
      value="${record#*|}"
      case "$kind" in
        remove)
          if value="$(remote_ssh_cmd_uninstall_append_unique "$value" ${symlinks[@]+"${symlinks[@]}"})"; then
            symlinks+=("$value")
          fi
          ;;
        protect)
          if value="$(remote_ssh_cmd_uninstall_append_unique "$value" ${protected[@]+"${protected[@]}"})"; then
            protected+=("$value")
          fi
          ;;
      esac
    done < <(remote_ssh_cmd_uninstall_collect_links_for_tool "$tool" "$prefix_canon")

    while IFS= read -r value; do
      [[ -n "$value" ]] || continue
      if value="$(remote_ssh_cmd_uninstall_append_unique "$value" ${release_dirs[@]+"${release_dirs[@]}"})"; then
        release_dirs+=("$value")
      fi
    done < <(remote_ssh_cmd_uninstall_collect_release_dirs_for_tool "$tool" "$prefix_canon")
  done

  printf 'remote-ssh uninstall\n\n'
  printf 'Install paths\n'
  printf '  %-10s %s\n' 'prefix:' "$INSTALL_PREFIX"
  printf '  %-10s %s\n' 'bin:' "$INSTALL_BIN_DIR"
  printf '\n'
  remote_ssh_cmd_uninstall_print_list "Selected tools:" ${selected[@]+"${selected[@]}"}
  printf '\n'
  remote_ssh_cmd_uninstall_print_list "Symlinks to remove:" ${symlinks[@]+"${symlinks[@]}"}
  printf '\n'
  remote_ssh_cmd_uninstall_print_list "Release dirs to remove:" ${release_dirs[@]+"${release_dirs[@]}"}
  printf '\n'
  remote_ssh_cmd_uninstall_print_list "Protected/skipped paths:" ${protected[@]+"${protected[@]}"}
  printf '\n'
  remote_ssh_cmd_uninstall_print_expected_action

  ((${#symlinks[@]} > 0 || ${#release_dirs[@]} > 0)) && changes=1
  [[ "$REMOTE_SSH_UNINSTALL_EXPECTED_ACTION" != "none" ]] && changes=1

  if ((changes == 0)); then
    printf '\nNo managed tools selected for uninstall.\n'
    return 0
  fi

  if ((yes == 0)); then
    remote_ssh_cmd_uninstall_confirm || return 1
  fi

  printf '\nApplying uninstall\n'
  for value in ${symlinks[@]+"${symlinks[@]}"}; do
    rm -f "$value"
    printf 'removed symlink: %s\n' "$value"
  done

  for value in ${release_dirs[@]+"${release_dirs[@]}"}; do
    rm -rf "$value"
    printf 'removed release dir: %s\n' "$value"
  done

  remote_ssh_cmd_uninstall_apply_expected_action
}
