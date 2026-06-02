# shellcheck shell=bash

ensure_this_file_sourced

_ssh_pick_config() {
  if [[ -n "${SSH_PICK_CONFIG:-}" ]]; then
    printf '%s\n' "$SSH_PICK_CONFIG"
    return 0
  fi

  if [[ -n "${SSH_CONFIG:-}" ]]; then
    printf '%s\n' "$SSH_CONFIG"
    return 0
  fi

  if [[ -f "$HOME/.ssh/config" ]]; then
    printf '%s\n' "$HOME/.ssh/config"
    return 0
  fi

  if [[ -n "${BSSH_SSH_CONFIG:-}" && -f "$BSSH_SSH_CONFIG" ]]; then
    printf '%s\n' "$BSSH_SSH_CONFIG"
    return 0
  fi

  return 1
}

_ssh_pick_selected_host() {
  local selected="$1"

  printf '%s\n' "${selected%%$'\t'*}"
}

_ssh_pick_choose() {
  local hosts="$1" query="$2"
  local input="$hosts"
  local matches match_count

  if [[ -n "$query" ]]; then
    matches="$(printf '%s\n' "$hosts" | grep -i -F -- "$query" || true)"
    if [[ -n "$matches" ]]; then
      match_count="$(printf '%s\n' "$matches" | sed -n '$=')"
      if [[ "$match_count" == "1" ]]; then
        printf '%s\n' "$matches"
        return 0
      fi
      input="$matches"
    fi
  fi

  if [[ -n "$query" ]]; then
    printf '%s\n' "$input" | fzf --prompt='ssh host> ' --query="$query"
  else
    printf '%s\n' "$input" | fzf --prompt='ssh host> '
  fi
}

ssh-pick() {
  local ssh_hosts_cmd="${SSH_HOSTS_CMD:-$REMOTE_ENV_DIR/scripts/ssh_hosts.py}"
  local query="${SSH_PICK_QUERY:-}"
  local config
  local ssh_hosts_args=()
  local hosts

  while (($# > 0)); do
    case "$1" in
      -q | --query)
        if (($# < 2)); then
          printf 'usage: ssh-pick [--query QUERY] [remote-command...]\n' >&2
          return 2
        fi
        query="$2"
        shift 2
        ;;
      --query=*)
        query="${1#--query=}"
        shift
        ;;
      *)
        break
        ;;
    esac
  done

  if [[ -z "${SSH_HOSTS_CMD:-}" ]]; then
    ssh_hosts_args=(--format pick)
    if config="$(_ssh_pick_config)"; then
      ssh_hosts_args+=(--config "$config")
    fi
  fi

  local selected selected_host
  hosts="$("$ssh_hosts_cmd" "${ssh_hosts_args[@]}" 2>&1)" || {
    printf '[WARN] ssh-pick could not list SSH hosts.\n' >&2
    printf '[WARN] ssh-pick currently requires python3 for scripts/ssh_hosts.py.\n' >&2
    [[ -n "$hosts" ]] && printf '%s\n' "$hosts" >&2
    return 1
  }

  [[ -n "$hosts" ]] || {
    printf '[WARN] ssh-pick found no SSH hosts.\n' >&2
    return 1
  }

  selected="$(_ssh_pick_choose "$hosts" "$query")" || return 130
  selected_host="$(_ssh_pick_selected_host "$selected")"

  [[ -n "$selected_host" ]] || {
    printf '[WARN] ssh-pick selected an empty SSH host.\n' >&2
    return 1
  }

  # shellcheck disable=SC2029
  ssh "$selected_host" "$@"
}
