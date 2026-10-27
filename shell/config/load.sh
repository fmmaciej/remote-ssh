# shellcheck shell=bash

remote_ssh_config_load() {
  local -a __remote_ssh_config_snapshot_keys=() __remote_ssh_config_snapshot_values=()
  local -a __remote_ssh_config_snapshot_present=()
  local __remote_ssh_config_snapshot_count=0 __remote_ssh_config_load_index=0
  local __remote_ssh_config_load_key __remote_ssh_config_load_value __remote_ssh_config_load_status

  remote_ssh_config_snapshot_init || {
    __remote_ssh_config_load_status=$?
    remote_ssh_config_enabled || return 0
    return "$__remote_ssh_config_load_status"
  }
  if remote_ssh_config_enabled; then
    remote_ssh_config_snapshot_read
  fi

  while ((__remote_ssh_config_load_index < __remote_ssh_config_snapshot_count)); do
    __remote_ssh_config_load_key="${__remote_ssh_config_snapshot_keys[__remote_ssh_config_load_index]}"
    if [[ "${__remote_ssh_config_snapshot_present[__remote_ssh_config_load_index]}" == 0 ]]; then
      if remote_ssh_config_value_is_owned "$__remote_ssh_config_load_key"; then
        unset "$__remote_ssh_config_load_key"
      fi
      remote_ssh_config_clear_source "$__remote_ssh_config_load_key"
    elif [[ -z "${!__remote_ssh_config_load_key+x}" ]] || remote_ssh_config_value_is_owned "$__remote_ssh_config_load_key"; then
      __remote_ssh_config_load_value="${__remote_ssh_config_snapshot_values[__remote_ssh_config_load_index]}"
      export "$__remote_ssh_config_load_key=$__remote_ssh_config_load_value"
      remote_ssh_config_mark_owned "$__remote_ssh_config_load_key" "$__remote_ssh_config_load_value"
    else
      remote_ssh_config_clear_source "$__remote_ssh_config_load_key"
    fi
    __remote_ssh_config_load_index=$((__remote_ssh_config_load_index + 1))
  done
  return 0
}
