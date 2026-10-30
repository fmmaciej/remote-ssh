# shellcheck shell=bash

ensure_this_file_sourced

remote_ssh_cmd_tool_usage() {
  cat <<'EOF' >&2
Usage:
  remote-ssh tool install <tool ...>
  remote-ssh tool list [--installed | --all]
EOF
}

remote_ssh_cmd_tool_list_usage() {
  cat <<'EOF'
Usage: remote-ssh tool list [--installed | --all]

Lists tools supported on this platform and managed installations.

Options:
  --installed  Show only managed installations
  --all        Include tools unsupported on this platform
  -h, --help   Show this help

Status:
  installed    Managed installation; use remote-ssh check for diagnostics
  available    Supported on this platform, without a managed installation
  unsupported  No matching asset for this platform
EOF
}

remote_ssh_cmd_tool_list() {
  local mode=default show_help=0 arg platform raw_os raw_arch libc tool status
  local -a rows=()

  for arg in "$@"; do
    case "$arg" in
      --installed|--all)
        if [[ "$mode" != default && "$mode" != "${arg#--}" ]]; then
          printf 'remote-ssh tool list: --installed and --all cannot be combined.\n' >&2
          return 1
        fi
        mode="${arg#--}"
        ;;
      -h|--help)
        show_help=1
        ;;
      *)
        printf 'remote-ssh tool list: unexpected argument: %s\n' "$arg" >&2
        remote_ssh_cmd_tool_list_usage >&2
        return 1
        ;;
    esac
  done

  if ((show_help == 1)); then
    remote_ssh_cmd_tool_list_usage
    return 0
  fi

  platform="$(default_platform)"
  IFS=: read -r raw_os raw_arch libc <<<"$platform"

  while IFS= read -r tool; do
    if managed_tool_installed "$tool"; then
      status=installed
    elif [[ "$mode" == installed ]]; then
      continue
    elif default_tool_supported_on_platform "$tool" "$raw_os" "$raw_arch" "$libc"; then
      status=available
    elif [[ "$mode" == all ]]; then
      status=unsupported
    else
      continue
    fi
    rows+=("$tool" "$status")
  done < <(LC_ALL=C all_known_tools)

  if ((${#rows[@]} == 0)); then
    printf 'No tools found.\n'
    return 0
  fi
  printf '%-16s %s\n' TOOL STATUS "${rows[@]}"
}

remote_ssh_cmd_tool_main() {
  remote_ssh_cmd_require_install_libs

  local subcommand="${1:-}"
  shift || true

  case "$subcommand" in
    install)
      (($# > 0)) || {
        printf 'Usage: remote-ssh tool install <tool ...>\n' >&2
        return 1
      }
      install_check_requirements
      install_tools "$@"
      ;;
    list)
      remote_ssh_cmd_tool_list "$@"
      ;;
    -h|--help)
      remote_ssh_cmd_tool_usage
      ;;
    *)
      remote_ssh_cmd_tool_usage
      return 1
      ;;
  esac
}
