# shellcheck shell=bash

ensure_this_file_sourced

remote_git_session_identity_set_status() {
  export REMOTE_SSH_GIT_SESSION_IDENTITY_STATUS="$1"
}

remote_git_session_identity_add_config() {
  local key="$1" value="$2" count

  case "${GIT_CONFIG_COUNT:-0}" in
    ''|*[!0-9]*) count=0 ;;
    *) count="${GIT_CONFIG_COUNT:-0}" ;;
  esac

  export "GIT_CONFIG_KEY_${count}=$key"
  export "GIT_CONFIG_VALUE_${count}=$value"
  count=$((count + 1))
  export GIT_CONFIG_COUNT="$count"
}

remote_git_session_identity_init() {
  local user_config name email

  if [[ "${REMOTE_SSH_ENABLE_GIT_SESSION_IDENTITY:-1}" != "1" ]]; then
    remote_git_session_identity_set_status disabled
    return 0
  fi
  if [[ "${REMOTE_SSH_GIT_SESSION_IDENTITY:-0}" == "1" ]]; then
    remote_git_session_identity_set_status ok
    return 0
  fi

  if ! have git; then
    remote_git_session_identity_set_status unavailable
    return 0
  fi

  user_config="${REMOTE_DOTS_DIR}/git/user.local"
  if [[ ! -r "$user_config" ]]; then
    remote_git_session_identity_set_status missing
    return 0
  fi

  name="$(git config --file "$user_config" --get user.name 2>/dev/null || true)"
  email="$(git config --file "$user_config" --get user.email 2>/dev/null || true)"

  if [[ -z "$name" || -z "$email" ||
    "$name" == "Your Name" ||
    "$email" == "your.email@example.com" ]]; then
    remote_git_session_identity_set_status invalid
    return 0
  fi

  remote_git_session_identity_add_config user.name "$name"
  remote_git_session_identity_add_config user.email "$email"
  remote_git_session_identity_add_config user.useConfigOnly true

  export REMOTE_SSH_GIT_SESSION_IDENTITY=1
  remote_git_session_identity_set_status ok
}

remote_git_session_identity_init
