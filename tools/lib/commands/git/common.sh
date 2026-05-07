# shellcheck shell=bash

ensure_this_file_sourced

remote_ssh_cmd_git_repo_dir() {
  cd "${REMOTE_ENV_DIR:-$REPO_DIR}" && pwd
}
