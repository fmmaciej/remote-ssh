# shellcheck shell=bash
# shellcheck disable=SC2153

ensure_this_file_sourced

remote_ssh_cmd_git_status_print_git_config_value() {
  local key="$1" value="$2" origin="$3"

  if [[ -n "$value" ]]; then
    if [[ -n "$origin" ]]; then
      printf '  %-18s %s (%s)\n' "${key}:" "$value" "$origin"
    else
      printf '  %-18s %s\n' "${key}:" "$value"
    fi
  else
    printf '  %-18s [missing]\n' "${key}:"
  fi
}

remote_ssh_cmd_git_status_print_session_identity() {
  local count="${GIT_CONFIG_COUNT:-0}" i key_var value_var key value found

  printf '\nGit session override\n'
  printf '  %-18s %s\n' 'enabled:' "${REMOTE_SSH_GIT_SESSION_IDENTITY:-0}"
  printf '  %-18s %s\n' 'GIT_CONFIG_COUNT:' "$count"

  case "$count" in
    ''|*[!0-9]*) return 0 ;;
  esac

  found=0
  for ((i = 0; i < count; i++)); do
    key_var="GIT_CONFIG_KEY_${i}"
    value_var="GIT_CONFIG_VALUE_${i}"
    key="${!key_var:-}"
    value="${!value_var:-}"
    case "$key" in
      user.name|user.email|user.useConfigOnly)
        printf '  session %-10s %s\n' "${key#user.}:" "$value"
        found=1
        ;;
    esac
  done

  [[ "$found" -eq 1 ]] || printf '  %-18s [none]\n' 'session keys:'
}

remote_ssh_cmd_git_status_print_next_steps() {
  local printed=0

  printf '\nNext steps\n'

  if [[ "$REMOTE_SSH_GIT_STATUS_INSIDE_WORK_TREE" -ne 1 ]]; then
    printf '  - Run remote-ssh git status from inside a Git work tree.\n'
    printed=1
  fi

  if [[ -z "$REMOTE_SSH_GIT_STATUS_USER_NAME" ||
    -z "$REMOTE_SSH_GIT_STATUS_USER_EMAIL" ||
    -z "$REMOTE_SSH_GIT_STATUS_USER_USE_CONFIG_ONLY" ]]; then
    printf '  - Run remote-ssh git setup to configure bundled Git defaults.\n'
    printed=1
  fi

  if [[ -z "$REMOTE_SSH_GIT_STATUS_ORIGIN_URL" ]]; then
    printf '  - Add an origin remote, or run this from a repository that has one.\n'
    printed=1
  fi

  [[ "$printed" -eq 1 ]] || printf '  [none]\n'
}

remote_ssh_cmd_git_status_render() {
  printf 'remote-ssh git status\n\n'

  printf 'Git config\n'
  remote_ssh_cmd_git_status_print_git_config_value \
    user.name \
    "$REMOTE_SSH_GIT_STATUS_USER_NAME" \
    "$REMOTE_SSH_GIT_STATUS_USER_NAME_ORIGIN"
  remote_ssh_cmd_git_status_print_git_config_value \
    user.email \
    "$REMOTE_SSH_GIT_STATUS_USER_EMAIL" \
    "$REMOTE_SSH_GIT_STATUS_USER_EMAIL_ORIGIN"
  remote_ssh_cmd_git_status_print_git_config_value \
    user.useConfigOnly \
    "$REMOTE_SSH_GIT_STATUS_USER_USE_CONFIG_ONLY" \
    "$REMOTE_SSH_GIT_STATUS_USER_USE_CONFIG_ONLY_ORIGIN"

  if [[ "$REMOTE_SSH_GIT_STATUS_INSIDE_WORK_TREE" -eq 1 ]]; then
    [[ -n "$REMOTE_SSH_GIT_STATUS_AUTHOR_IDENT" ]] &&
      printf '  %-18s %s\n' 'author ident:' "$REMOTE_SSH_GIT_STATUS_AUTHOR_IDENT"
    [[ -n "$REMOTE_SSH_GIT_STATUS_COMMITTER_IDENT" ]] &&
      printf '  %-18s %s\n' 'committer ident:' "$REMOTE_SSH_GIT_STATUS_COMMITTER_IDENT"
  else
    printf '  %-18s [not inside a Git work tree]\n' 'work tree:'
  fi

  remote_ssh_cmd_git_status_print_session_identity

  printf '\nGit remote\n'
  if [[ -n "$REMOTE_SSH_GIT_STATUS_ORIGIN_URL" ]]; then
    printf '  %-18s %s\n' 'origin:' "$REMOTE_SSH_GIT_STATUS_ORIGIN_URL"
  else
    printf '  %-18s [missing]\n' 'origin:'
  fi

  remote_ssh_cmd_git_status_print_next_steps
}
