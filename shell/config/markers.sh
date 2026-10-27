# shellcheck shell=bash

remote_ssh_config_marker_key() {
  printf '%s\n' "${1#REMOTE_SSH_}"
}

remote_ssh_config_source_var() {
  printf 'REMOTE_SSH_CONFIG_SOURCE_%s\n' "${1#REMOTE_SSH_}"
}

remote_ssh_config_loaded_value_var() {
  printf 'REMOTE_SSH_CONFIG_LOADED_VALUE_%s\n' "${1#REMOTE_SSH_}"
}

remote_ssh_config_mark_owned() {
  local __remote_ssh_config_mark_suffix="${1#REMOTE_SSH_}"
  local __remote_ssh_config_mark_source_var __remote_ssh_config_mark_loaded_var

  __remote_ssh_config_mark_source_var="REMOTE_SSH_CONFIG_SOURCE_$__remote_ssh_config_mark_suffix"
  __remote_ssh_config_mark_loaded_var="REMOTE_SSH_CONFIG_LOADED_VALUE_$__remote_ssh_config_mark_suffix"
  export "$__remote_ssh_config_mark_source_var=config"
  export "$__remote_ssh_config_mark_loaded_var=$2"
}

remote_ssh_config_clear_source() {
  local __remote_ssh_config_clear_suffix="${1#REMOTE_SSH_}"
  local __remote_ssh_config_clear_source_var __remote_ssh_config_clear_loaded_var

  __remote_ssh_config_clear_source_var="REMOTE_SSH_CONFIG_SOURCE_$__remote_ssh_config_clear_suffix"
  __remote_ssh_config_clear_loaded_var="REMOTE_SSH_CONFIG_LOADED_VALUE_$__remote_ssh_config_clear_suffix"
  unset "$__remote_ssh_config_clear_source_var"
  unset "$__remote_ssh_config_clear_loaded_var"
}

remote_ssh_config_source() {
  local __remote_ssh_config_source_suffix="${1#REMOTE_SSH_}" __remote_ssh_config_source_name

  __remote_ssh_config_source_name="REMOTE_SSH_CONFIG_SOURCE_$__remote_ssh_config_source_suffix"
  printf '%s\n' "${!__remote_ssh_config_source_name:-}"
}

remote_ssh_config_loaded_value() {
  local __remote_ssh_config_loaded_suffix="${1#REMOTE_SSH_}" __remote_ssh_config_loaded_name

  __remote_ssh_config_loaded_name="REMOTE_SSH_CONFIG_LOADED_VALUE_$__remote_ssh_config_loaded_suffix"
  [[ -n "${!__remote_ssh_config_loaded_name+x}" ]] || return 1
  printf '%s\n' "${!__remote_ssh_config_loaded_name}"
}

remote_ssh_config_value_is_current_owned() {
  local __remote_ssh_config_owned_key="$1" __remote_ssh_config_owned_suffix="${1#REMOTE_SSH_}"
  local __remote_ssh_config_owned_source_var __remote_ssh_config_owned_loaded_var

  [[ -n "${!__remote_ssh_config_owned_key+x}" ]] || return 1
  __remote_ssh_config_owned_source_var="REMOTE_SSH_CONFIG_SOURCE_$__remote_ssh_config_owned_suffix"
  __remote_ssh_config_owned_loaded_var="REMOTE_SSH_CONFIG_LOADED_VALUE_$__remote_ssh_config_owned_suffix"

  [[ "${!__remote_ssh_config_owned_source_var:-}" == "config" ]] || return 1
  [[ -n "${!__remote_ssh_config_owned_loaded_var+x}" ]] || return 1
  [[ "${!__remote_ssh_config_owned_key}" == "${!__remote_ssh_config_owned_loaded_var}" ]]
}

remote_ssh_config_value_is_owned() {
  remote_ssh_config_value_is_current_owned "$1"
}
