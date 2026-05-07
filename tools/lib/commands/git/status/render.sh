# shellcheck shell=bash
# shellcheck disable=SC2153

ensure_this_file_sourced

remote_ssh_cmd_git_status_print_git_config_value() {
  local key="$1" value origin

  value="$(git config --get "$key" 2>/dev/null || true)"
  origin="$(git config --show-origin --get "$key" 2>/dev/null | sed 's/[[:space:]].*$//' || true)"

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

remote_ssh_cmd_git_status_render_agent() {
  printf '\nSSH agent\n'
  if [[ -n "$REMOTE_SSH_GIT_STATUS_SSH_AUTH_SOCK" ]]; then
    printf '  %-18s %s\n' 'SSH_AUTH_SOCK:' "$REMOTE_SSH_GIT_STATUS_SSH_AUTH_SOCK"
  else
    printf '  %-18s [missing]\n' 'SSH_AUTH_SOCK:'
  fi

  if [[ "$REMOTE_SSH_GIT_STATUS_SSH_ADD_FOUND" -eq 1 ]]; then
    if [[ "$REMOTE_SSH_GIT_STATUS_SSH_ADD_EXIT" -eq 0 ]]; then
      while IFS= read -r line; do
        [[ -n "$line" ]] && printf '  key:              %s\n' "$line"
      done <<<"$REMOTE_SSH_GIT_STATUS_SSH_ADD_OUTPUT"
    else
      printf '  %-18s %s\n' 'keys:' "$REMOTE_SSH_GIT_STATUS_SSH_ADD_OUTPUT"
    fi
  else
    printf '  %-18s [ssh-add not found]\n' 'keys:'
  fi
}

remote_ssh_cmd_git_status_render_auth() {
  if [[ -z "$REMOTE_SSH_GIT_STATUS_SSH_HOST" ]]; then
    printf '\nSSH auth\n'
    printf '  %-18s [skipped]\n' 'status:'
    return 0
  fi

  printf '\nSSH auth\n'
  printf '  %-18s ssh -T git@%s\n' 'command:' "$REMOTE_SSH_GIT_STATUS_SSH_HOST"

  if [[ "$REMOTE_SSH_GIT_STATUS_AUTH_STATUS" == "ok" ]]; then
    printf '  %-18s ok\n' 'status:'
  else
    printf '  %-18s exit %s\n' 'status:' "$REMOTE_SSH_GIT_STATUS_SSH_EXIT"
  fi

  while IFS= read -r line; do
    [[ -n "$line" ]] && printf '  output:           %s\n' "$line"
  done <<<"$REMOTE_SSH_GIT_STATUS_SSH_OUTPUT"
}

remote_ssh_cmd_git_status_render_diagnosis() {
  printf '\nDiagnosis\n'
  printf '  %-18s %s\n' 'ssh agent:' "$REMOTE_SSH_GIT_STATUS_AGENT_STATUS"
  printf '  %-18s %s\n' 'ssh auth:' "$REMOTE_SSH_GIT_STATUS_AUTH_STATUS"
}

remote_ssh_cmd_git_status_render() {
  printf 'remote-ssh git status\n\n'

  printf 'Git config\n'
  remote_ssh_cmd_git_status_print_git_config_value user.name
  remote_ssh_cmd_git_status_print_git_config_value user.email
  remote_ssh_cmd_git_status_print_git_config_value user.useConfigOnly

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

  if [[ -n "$REMOTE_SSH_GIT_STATUS_SSH_HOST" ]]; then
    printf '  %-18s %s\n' 'ssh host:' "$REMOTE_SSH_GIT_STATUS_SSH_HOST"
  else
    printf '  %-18s [missing; pass one, e.g. github.com-myuser]\n' 'ssh host:'
  fi

  remote_ssh_cmd_git_status_render_agent
  remote_ssh_cmd_git_status_render_auth
  remote_ssh_cmd_git_status_render_diagnosis
  remote_ssh_cmd_git_status_print_hints
}
