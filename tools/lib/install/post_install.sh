# shellcheck shell=bash

ensure_this_file_sourced

install_print_post_install() {
  local template_dir="$REPO_DIR/docs/post-install.d"
  local install_dir="${1:?install_dir required}"
  local ssh_conn ip hostname who
  local templates=()
  local restore_nullglob

  [[ -d $template_dir ]] || return 0

  restore_nullglob="$(shopt -p nullglob || true)"
  shopt -s nullglob
  templates=("$template_dir"/*.in)
  eval "$restore_nullglob"

  ((${#templates[@]} > 0)) || return 0

  # SSH_CONNECTION: "<client_ip> <client_port> <server_ip> <server_port>"
  ssh_conn="${SSH_CONNECTION:-}"
  ip=""
  if [[ -n $ssh_conn ]]; then
    read -r _client_ip _client_port ip _server_port <<<"$ssh_conn"
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
    "${templates[@]}"
}
