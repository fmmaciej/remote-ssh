# shellcheck shell=bash

ensure_this_file_sourced

install_print_post_install() {
  local template_file="$REPO_DIR/docs/POST_INSTALL.in"
  local install_dir="${1:?install_dir required}"
  local ssh_conn ip hostname who

  [[ -f "$template_file" ]] || return 0

  # SSH_CONNECTION: "<client_ip> <client_port> <server_ip> <server_port>"
  ssh_conn="${SSH_CONNECTION:-}"
  ip=""
  if [[ -n "$ssh_conn" ]]; then
    set -- "$ssh_conn"
    ip="${3:-}"
  fi

  hostname="$(hostname -f 2>/dev/null || hostname 2>/dev/null || true)"
  who="$(whoami 2>/dev/null || true)"

  # escape for sed replacement: \ & and delimiter |
  _sed_escape() {
    printf '%s' "$1" | sed -e 's/[\/&|\\]/\\&/g'
  }

  sed \
    -e "s|@INSTALL_DIR@|$(_sed_escape "$install_dir")|g" \
    -e "s|@HOSTNAME@|$(_sed_escape "${hostname:-<hostname>}")|g" \
    -e "s|@IP_ADDRESS@|$(_sed_escape "${ip:-<ip-address>}")|g" \
    -e "s|@WHO_AM_I@|$(_sed_escape "${who:-<user>}")|g" \
    "$template_file"
}

