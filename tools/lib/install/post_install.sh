# shellcheck shell=bash

ensure_this_file_sourced

install_render_post_install() {
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

  local interactive_command
  printf -v interactive_command 'bash --rcfile %q -i' "$install_dir/shell/rc.sh"

  sed \
    -e "s|@INTERACTIVE_COMMAND@|$(_sed_escape "$interactive_command")|g" \
    -e "s|@INSTALL_DIR@|$(_sed_escape "$install_dir")|g" \
    -e "s|@HOSTNAME@|$(_sed_escape "${hostname:-<hostname>}")|g" \
    -e "s|@IP_ADDRESS@|$(_sed_escape "${ip:-<ip-address>}")|g" \
    -e "s|@WHO_AM_I@|$(_sed_escape "${who:-<user>}")|g" \
    ${templates[@]+"${templates[@]}"}
}

install_post_install_bin_in_path() {
  local bin_dir="$1" entry path_rest="${PATH}:" canonical
  canonical="$(cd -- "$bin_dir" 2>/dev/null && pwd -P)" || canonical="$bin_dir"
  while [[ "$path_rest" == *:* ]]; do
    entry="${path_rest%%:*}"
    path_rest="${path_rest#*:}"
    [[ -n "$entry" ]] || entry=.
    if [[ "$entry" == "$bin_dir" ]] ||
      [[ "$(cd -- "$entry" 2>/dev/null && pwd -P)" == "$canonical" ]]; then
      return 0
    fi
  done
  return 1
}

install_print_post_install() {
  local install_dir="${1:?install_dir required}"
  local bin_dir="${INSTALL_BIN_DIR:-$HOME/.local/bin}"

  printf '\nInstalled CLI: %s/remote-ssh\n' "$bin_dir"
  printf 'Post-install setup:\n  run: %q guide post-install\n' "$bin_dir/remote-ssh"
  printf 'Start a local remote-ssh shell (also works from Zsh):\n'
  printf '  bash --rcfile %q -i\n' "$install_dir/shell/rc.sh"
  if ! install_post_install_bin_in_path "$bin_dir"; then
    printf 'To use remote-ssh by name in this terminal:\n'
    # Keep PATH literal so the printed command expands it in the user's shell.
    # shellcheck disable=SC2016
    printf '  export PATH=%q:"$PATH"\n' "$bin_dir"
    printf 'Configure this directory in PATH for new terminals too; startup files were not modified.\n'
  fi
}
