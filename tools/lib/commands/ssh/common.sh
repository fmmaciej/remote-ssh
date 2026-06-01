# shellcheck shell=bash

ensure_this_file_sourced

remote_ssh_cmd_ssh_repo_dir() {
  cd "${REMOTE_ENV_DIR:-$REPO_DIR}" && pwd
}

remote_ssh_cmd_ssh_config_local() {
  printf '%s/dots/ssh/config.local\n' "$(remote_ssh_cmd_ssh_repo_dir)"
}

remote_ssh_cmd_ssh_config_example() {
  printf '%s/dots/ssh/config.example\n' "$(remote_ssh_cmd_ssh_repo_dir)"
}
