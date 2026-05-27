# shellcheck shell=bash

remote_ssh_config_load() {
  local key _default value

  if ! remote_ssh_config_enabled; then
    while IFS='|' read -r key _default; do
      if remote_ssh_config_value_is_owned "$key"; then
        unset "$key"
      fi
      remote_ssh_config_clear_source "$key"
    done < <(remote_ssh_config_entries)
    return 0
  fi

  while IFS='|' read -r key _default; do
    if ! value="$(remote_ssh_config_file_value_raw "$key" 2>/dev/null)"; then
      if remote_ssh_config_value_is_owned "$key"; then
        unset "$key"
      fi
      remote_ssh_config_clear_source "$key"
      continue
    fi

    if [[ -z "${!key+x}" ]] || remote_ssh_config_value_is_owned "$key"; then
      export "$key=$value"
      remote_ssh_config_mark_owned "$key" "$value"
    else
      remote_ssh_config_clear_source "$key"
    fi
  done < <(remote_ssh_config_entries)
}
