# shellcheck shell=bash

remote_ssh_config_trim() {
  local value="$1"

  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf '%s\n' "$value"
}

remote_ssh_config_unquote() {
  local value="$1"

  case "$value" in
    \"*\")
      value="${value#\"}"
      value="${value%\"}"
      ;;
    \'*\')
      value="${value#\'}"
      value="${value%\'}"
      ;;
  esac
  printf '%s\n' "$value"
}

remote_ssh_config_file_value_raw() {
  local wanted="$1" file line key value found=0

  file="$(remote_ssh_config_file 2>/dev/null)" || return 1
  [[ -r "$file" ]] || return 1

  while IFS= read -r line || [[ -n "$line" ]]; do
    line="$(remote_ssh_config_trim "$line")"
    case "$line" in
      '' | \#*) continue ;;
      *=*) ;;
      *) continue ;;
    esac

    key="$(remote_ssh_config_trim "${line%%=*}")"
    remote_ssh_config_key_allowed "$key" || continue
    [[ "$key" == "$wanted" ]] || continue

    value="$(remote_ssh_config_trim "${line#*=}")"
    value="$(remote_ssh_config_unquote "$value")"
    found=1
  done <"$file"

  if ((found == 1)); then
    printf '%s\n' "$value"
    return 0
  fi

  return 1
}

remote_ssh_config_file_value() {
  remote_ssh_config_enabled || return 1
  remote_ssh_config_file_value_raw "$@"
}
