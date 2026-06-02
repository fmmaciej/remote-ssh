# shellcheck shell=bash

ensure_this_file_sourced

ssh-pick() {
  local ssh_find_cmd="${SSH_FIND_CMD:-ssh-find}"
  local query="${SSH_PICK_QUERY:-}"
  local selected status
  local alias _address user _source port connect_kind connect_target _rest

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
      --)
        shift
        break
        ;;
      *)
        break
        ;;
    esac
  done

  if [[ -n "$query" ]]; then
    if selected="$("$ssh_find_cmd" "$query")"; then
      :
    else
      status=$?
      return "$status"
    fi
  else
    if selected="$("$ssh_find_cmd")"; then
      :
    else
      status=$?
      return "$status"
    fi
  fi

  IFS=$'\t' read -r alias _address user _source port connect_kind connect_target _rest <<<"$selected"

  if [[ -z "$alias" || -z "$connect_kind" || -z "$connect_target" ]]; then
    printf '[WARN] ssh-pick received an invalid ssh-find record.\n' >&2
    return 1
  fi

  case "$connect_kind" in
    ssh-config)
      # shellcheck disable=SC2029
      ssh "$connect_target" "$@"
      ;;
    direct)
      local ssh_args=()
      local target="$connect_target"

      if [[ -n "$port" ]]; then
        ssh_args=(-p "$port")
      fi
      if [[ -n "$user" ]]; then
        target="$user@$target"
      fi

      # shellcheck disable=SC2029
      ssh "${ssh_args[@]}" "$target" "$@"
      ;;
    *)
      printf '[WARN] ssh-pick received unknown connect kind: %s\n' "$connect_kind" >&2
      return 1
      ;;
  esac
}
