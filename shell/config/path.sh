# shellcheck shell=bash

remote_ssh_config_enabled() {
  case "${REMOTE_SSH_CONFIG:-1}" in
    0 | false | no | off) return 1 ;;
    *) return 0 ;;
  esac
}

remote_ssh_config_file() {
  if [[ -n "${XDG_CONFIG_HOME:-}" ]]; then
    printf '%s/remote-ssh/config\n' "$XDG_CONFIG_HOME"
  elif [[ -n "${HOME:-}" ]]; then
    printf '%s/.config/remote-ssh/config\n' "$HOME"
  else
    return 1
  fi
}
