# shellcheck shell=bash
# shellcheck disable=SC2034

ensure_this_file_sourced

remote_ssh_cmd_git_status_collect_config_value() {
  local key="$1" value_var="$2" origin_var="$3"
  local value origin

  value="$(git config --get "$key" 2>/dev/null || true)"
  origin="$(git config --show-origin --get "$key" 2>/dev/null | sed 's/[[:space:]].*$//' || true)"

  printf -v "$value_var" '%s' "$value"
  printf -v "$origin_var" '%s' "$origin"
}

remote_ssh_cmd_git_status_collect_git() {
  REMOTE_SSH_GIT_STATUS_USER_NAME=""
  REMOTE_SSH_GIT_STATUS_USER_NAME_ORIGIN=""
  REMOTE_SSH_GIT_STATUS_USER_EMAIL=""
  REMOTE_SSH_GIT_STATUS_USER_EMAIL_ORIGIN=""
  REMOTE_SSH_GIT_STATUS_USER_USE_CONFIG_ONLY=""
  REMOTE_SSH_GIT_STATUS_USER_USE_CONFIG_ONLY_ORIGIN=""
  REMOTE_SSH_GIT_STATUS_AUTHOR_IDENT=""
  REMOTE_SSH_GIT_STATUS_COMMITTER_IDENT=""
  REMOTE_SSH_GIT_STATUS_INSIDE_WORK_TREE=0

  remote_ssh_cmd_git_status_collect_config_value \
    user.name \
    REMOTE_SSH_GIT_STATUS_USER_NAME \
    REMOTE_SSH_GIT_STATUS_USER_NAME_ORIGIN
  remote_ssh_cmd_git_status_collect_config_value \
    user.email \
    REMOTE_SSH_GIT_STATUS_USER_EMAIL \
    REMOTE_SSH_GIT_STATUS_USER_EMAIL_ORIGIN
  remote_ssh_cmd_git_status_collect_config_value \
    user.useConfigOnly \
    REMOTE_SSH_GIT_STATUS_USER_USE_CONFIG_ONLY \
    REMOTE_SSH_GIT_STATUS_USER_USE_CONFIG_ONLY_ORIGIN

  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    REMOTE_SSH_GIT_STATUS_INSIDE_WORK_TREE=1
    REMOTE_SSH_GIT_STATUS_AUTHOR_IDENT="$(git var GIT_AUTHOR_IDENT 2>/dev/null || true)"
    REMOTE_SSH_GIT_STATUS_COMMITTER_IDENT="$(git var GIT_COMMITTER_IDENT 2>/dev/null || true)"
  fi

  REMOTE_SSH_GIT_STATUS_ORIGIN_URL="$(git remote get-url origin 2>/dev/null || true)"
}

remote_ssh_cmd_git_status_collect() {
  remote_ssh_cmd_git_status_collect_git
}
