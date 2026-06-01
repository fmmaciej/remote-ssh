# shellcheck shell=bash

ensure_this_file_sourced

: "${BSSH_SSH_CONFIG:=$HOME/.ssh/config.d/00-all.conf}"
export BSSH_SSH_CONFIG

bssh() {
  command bssh --stream --ssh-config "$BSSH_SSH_CONFIG" "$@"
}

bssh-ip() {
  local host

  if (($# == 0)); then
    printf 'usage: bssh-ip HOST\n' >&2
    return 2
  fi

  host="$1"
  ssh -G -F "$BSSH_SSH_CONFIG" "$host" 2>/dev/null |
    awk '
      $1 == "hostname" { hostname = $2 }
      $1 == "user" { user = $2 }
      $1 == "port" { port = $2 }
      END {
        if (hostname == "") exit 1
        printf "%s", hostname
        if (user != "" || port != "") {
          printf "  #"
          if (user != "") printf " user=%s", user
          if (port != "") printf " port=%s", port
        }
        printf "\n"
      }
    '
}
