# shellcheck shell=bash
# shellcheck disable=SC2034

ensure_this_file_sourced

remote_ssh_cmd_git_status_infer_ssh_host_from_remote() {
  local remote_url="$1"

  case "$remote_url" in
    git@*:*)
      printf '%s\n' "${remote_url#git@}" | sed 's/:.*$//'
      ;;
    ssh://git@*)
      printf '%s\n' "${remote_url#ssh://git@}" | sed 's/[/:].*$//'
      ;;
  esac
}

remote_ssh_cmd_git_status_collect_git() {
  REMOTE_SSH_GIT_STATUS_AUTHOR_IDENT=""
  REMOTE_SSH_GIT_STATUS_COMMITTER_IDENT=""
  REMOTE_SSH_GIT_STATUS_INSIDE_WORK_TREE=0

  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    REMOTE_SSH_GIT_STATUS_INSIDE_WORK_TREE=1
    REMOTE_SSH_GIT_STATUS_AUTHOR_IDENT="$(git var GIT_AUTHOR_IDENT 2>/dev/null || true)"
    REMOTE_SSH_GIT_STATUS_COMMITTER_IDENT="$(git var GIT_COMMITTER_IDENT 2>/dev/null || true)"
  fi

  REMOTE_SSH_GIT_STATUS_ORIGIN_URL="$(git remote get-url origin 2>/dev/null || true)"
}

remote_ssh_cmd_git_status_collect_agent() {
  remote_ssh_cmd_ssh_status_collect_agent

  REMOTE_SSH_GIT_STATUS_SSH_AUTH_SOCK="$REMOTE_SSH_STATUS_SSH_AUTH_SOCK"
  REMOTE_SSH_GIT_STATUS_SSH_ADD_FOUND="$REMOTE_SSH_STATUS_SSH_ADD_FOUND"
  REMOTE_SSH_GIT_STATUS_SSH_ADD_OUTPUT="$REMOTE_SSH_STATUS_SSH_ADD_OUTPUT"
  REMOTE_SSH_GIT_STATUS_SSH_ADD_EXIT="$REMOTE_SSH_STATUS_SSH_ADD_EXIT"
}

remote_ssh_cmd_git_status_collect_auth() {
  REMOTE_SSH_GIT_STATUS_SSH_OUTPUT=""
  REMOTE_SSH_GIT_STATUS_SSH_EXIT=0

  [[ -n "$REMOTE_SSH_GIT_STATUS_SSH_HOST" ]] || return 0

  set +e
  REMOTE_SSH_GIT_STATUS_SSH_OUTPUT="$(
    ssh -o BatchMode=yes -o ConnectTimeout=10 -T "git@${REMOTE_SSH_GIT_STATUS_SSH_HOST}" 2>&1
  )"
  REMOTE_SSH_GIT_STATUS_SSH_EXIT=$?
  set -e
}

remote_ssh_cmd_git_status_collect() {
  local requested_ssh_host="$1"

  remote_ssh_cmd_git_status_collect_git

  REMOTE_SSH_GIT_STATUS_SSH_HOST="$requested_ssh_host"
  if [[ -z "$REMOTE_SSH_GIT_STATUS_SSH_HOST" && -n "$REMOTE_SSH_GIT_STATUS_ORIGIN_URL" ]]; then
    REMOTE_SSH_GIT_STATUS_SSH_HOST="$(
      remote_ssh_cmd_git_status_infer_ssh_host_from_remote "$REMOTE_SSH_GIT_STATUS_ORIGIN_URL"
    )"
  fi

  remote_ssh_cmd_git_status_collect_agent
  remote_ssh_cmd_git_status_collect_auth
  remote_ssh_cmd_git_status_diagnose
}
