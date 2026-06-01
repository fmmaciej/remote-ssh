# shellcheck shell=bash

remote_ssh_welcome_green() {
  if remote_ssh_welcome_color_enabled; then
    printf '\033[32m%s\033[0m\n' "$1"
  else
    printf '%s\n' "$1"
  fi
}

remote_ssh_welcome_print_full_banner() {
  if remote_ssh_welcome_color_enabled; then
    printf '\033[32m'
  fi
  cat <<'EOF'
 ____  _____ __  __  ___ _____ _____      ____ ____  _   _
|  _ \| ____|  \/  |/ _ \_   _| ____|    / ___/ ___|| | | |
| |_) |  _| | |\/| | | | || | |  _| _____\___ \___ \| |_| |
|  _ <| |___| |  | | |_| || | | |__|_____|___) |__) |  _  |
|_| \_\_____|_|  |_|\___/ |_| |_____|    |____/____/|_| |_|

EOF
  if remote_ssh_welcome_color_enabled; then
    printf '\033[0m'
  fi
}

remote_ssh_welcome_print_banner() {
  local columns

  remote_ssh_welcome_banner_enabled || return 0
  case "${COLUMNS:-80}" in
    '' | *[!0-9]*) columns=80 ;;
    *) columns="${COLUMNS:-80}" ;;
  esac

  if ((columns >= 72)); then
    remote_ssh_welcome_print_full_banner
  elif ((columns >= 40)); then
    remote_ssh_welcome_green "R-SSH"
  else
    remote_ssh_welcome_green "R-S"
  fi
  printf 'Remote-SSH\n\n'
}
