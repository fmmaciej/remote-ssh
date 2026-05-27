# shellcheck shell=bash

remote_ssh_welcome_ssh_agent_status() {
  local output status

  if [[ -z "${SSH_AUTH_SOCK:-}" ]]; then
    printf 'unavailable\n'
    return 0
  fi

  command -v ssh-add >/dev/null 2>&1 || {
    printf 'unavailable\n'
    return 0
  }

  output="$(ssh-add -l 2>&1)"
  status=$?
  if [[ "$status" -eq 0 ]]; then
    printf 'ok\n'
  elif grep -qi 'no identities' <<<"$output"; then
    printf 'empty\n'
  else
    printf 'unavailable\n'
  fi
}

remote_ssh_welcome_git_user_config_status() {
  local repo_dir user_config name email

  if [[ "${REMOTE_SSH_ENABLE_GIT_SESSION_IDENTITY:-1}" != "1" ]]; then
    printf 'disabled\n'
    return 0
  fi

  command -v git >/dev/null 2>&1 || {
    printf 'unavailable\n'
    return 0
  }

  if [[ "${REMOTE_SSH_GIT_SESSION_IDENTITY:-0}" == "1" ]]; then
    printf 'ok\n'
    return 0
  fi

  repo_dir="${REMOTE_ENV_DIR:-$(remote_ssh_welcome_repo_dir)}"
  user_config="${repo_dir}/dots/git/user.local"
  [[ -r "$user_config" ]] || {
    printf 'missing\n'
    return 0
  }

  name="$(git config --file "$user_config" --get user.name 2>/dev/null || true)"
  email="$(git config --file "$user_config" --get user.email 2>/dev/null || true)"
  if [[ -z "$name" || -z "$email" ||
    "$name" == "Your Name" ||
    "$email" == "your.email@example.com" ]]; then
    printf 'invalid\n'
    return 0
  fi

  printf 'inactive\n'
}

remote_ssh_welcome_print_sw() {
  local agent_status git_status issue

  agent_status="$(remote_ssh_welcome_ssh_agent_status)"
  git_status="$(remote_ssh_welcome_git_user_config_status)"

  printf 'sw:      ssh-agent %s / git config %s\n' "$agent_status" "$git_status"

  case "$git_status" in
    ok | disabled) issue="" ;;
    unavailable) issue="doctor" ;;
    *) issue="sw" ;;
  esac

  if [[ -n "$issue" ]]; then
    remote_ssh_welcome_issue "$issue"
  fi
  return 0
}
