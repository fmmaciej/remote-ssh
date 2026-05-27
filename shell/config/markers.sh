# shellcheck shell=bash

remote_ssh_config_marker_key() {
  local key="$1"

  case "$key" in
    REMOTE_SSH_*) printf '%s\n' "${key#REMOTE_SSH_}" ;;
    *) printf '%s\n' "$key" ;;
  esac
}

remote_ssh_config_source_var() {
  printf 'REMOTE_SSH_CONFIG_SOURCE_%s\n' "$(remote_ssh_config_marker_key "$1")"
}

remote_ssh_config_loaded_value_var() {
  printf 'REMOTE_SSH_CONFIG_LOADED_VALUE_%s\n' "$(remote_ssh_config_marker_key "$1")"
}

remote_ssh_config_mark_owned() {
  local key="$1" value="$2" source_var loaded_var

  source_var="$(remote_ssh_config_source_var "$key")"
  loaded_var="$(remote_ssh_config_loaded_value_var "$key")"
  export "$source_var=config"
  export "$loaded_var=$value"
}

remote_ssh_config_clear_source() {
  local key="$1" source_var loaded_var

  source_var="$(remote_ssh_config_source_var "$key")"
  loaded_var="$(remote_ssh_config_loaded_value_var "$key")"
  unset "$source_var"
  unset "$loaded_var"
}

remote_ssh_config_source() {
  local key="$1" source_var

  source_var="$(remote_ssh_config_source_var "$key")"
  printf '%s\n' "${!source_var:-}"
}

remote_ssh_config_loaded_value() {
  local key="$1" loaded_var

  loaded_var="$(remote_ssh_config_loaded_value_var "$key")"
  [[ -n "${!loaded_var+x}" ]] || return 1
  printf '%s\n' "${!loaded_var}"
}

remote_ssh_config_value_is_current_owned() {
  local key="$1" source_var loaded_var

  [[ -n "${!key+x}" ]] || return 1
  source_var="$(remote_ssh_config_source_var "$key")"
  loaded_var="$(remote_ssh_config_loaded_value_var "$key")"

  [[ "${!source_var:-}" == "config" ]] || return 1
  [[ -n "${!loaded_var+x}" ]] || return 1
  [[ "${!key}" == "${!loaded_var}" ]]
}

remote_ssh_config_value_is_owned() {
  remote_ssh_config_value_is_current_owned "$1"
}
