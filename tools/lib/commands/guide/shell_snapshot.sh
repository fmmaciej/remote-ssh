# shellcheck shell=bash

ensure_this_file_sourced

remote_ssh_cmd_guide_remote_shell_snapshot() {
  local mode="$1"
  local repo_dir

  repo_dir="$(remote_ssh_cmd_guide_repo_dir)"

  REMOTE_ENV_DIR="$repo_dir" \
    REMOTE_SSH_UPDATE_CHECK=0 \
    REMOTE_SSH_ENABLE_ATUIN=0 \
    REMOTE_SSH_ENABLE_ATUIN_AUTO_IMPORT=0 \
    bash --noprofile --norc -c '
      mode="$1"
      rc_file="$2"

      # shellcheck source=/dev/null
      source "$rc_file"

      case "$mode" in
        aliases)
          alias -p | sort
          ;;
        functions)
          for fn in log logrun sshf remote_atuin_debug; do
            if declare -F "$fn" >/dev/null 2>&1; then
              printf "%s\n" "$fn"
            fi
          done
          ;;
      esac
    ' _ "$mode" "$repo_dir/shell/rc.sh"
}
