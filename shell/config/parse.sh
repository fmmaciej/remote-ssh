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

# Private output contract: callers declare the three indexed snapshot arrays
# and count locally. These helpers intentionally update those dynamically scoped
# locals; scratch names must not shadow any of the four output names.
remote_ssh_config_snapshot_init() {
  local __remote_ssh_config_init_key __remote_ssh_config_init_default
  local __remote_ssh_config_init_index=0

  __remote_ssh_config_snapshot_keys=()
  __remote_ssh_config_snapshot_values=()
  __remote_ssh_config_snapshot_present=()
  __remote_ssh_config_snapshot_count=0
  while IFS='|' read -r __remote_ssh_config_init_key __remote_ssh_config_init_default; do
    __remote_ssh_config_snapshot_keys[__remote_ssh_config_init_index]="$__remote_ssh_config_init_key"
    __remote_ssh_config_snapshot_values[__remote_ssh_config_init_index]=''
    __remote_ssh_config_snapshot_present[__remote_ssh_config_init_index]=0
    __remote_ssh_config_init_index=$((__remote_ssh_config_init_index + 1))
  done < <(remote_ssh_config_entries) || return $?
  __remote_ssh_config_snapshot_count="$__remote_ssh_config_init_index"
  return 0
}

remote_ssh_config_snapshot_read() {
  local __remote_ssh_config_scan_file __remote_ssh_config_scan_line=''
  local __remote_ssh_config_scan_key __remote_ssh_config_scan_value
  local __remote_ssh_config_scan_index

  __remote_ssh_config_scan_file="$(remote_ssh_config_file 2>/dev/null)" || return 0
  [[ -r "$__remote_ssh_config_scan_file" ]] || return 0

  # Guard open/read errors as absent entries, including strict-mode callers.
  if {
    while IFS= read -r __remote_ssh_config_scan_line || [[ -n "$__remote_ssh_config_scan_line" ]]; do
      __remote_ssh_config_scan_line="${__remote_ssh_config_scan_line#"${__remote_ssh_config_scan_line%%[![:space:]]*}"}"
      __remote_ssh_config_scan_line="${__remote_ssh_config_scan_line%"${__remote_ssh_config_scan_line##*[![:space:]]}"}"
      case "$__remote_ssh_config_scan_line" in
        '' | \#*) continue ;;
        *=*) ;;
        *) continue ;;
      esac

      __remote_ssh_config_scan_key="${__remote_ssh_config_scan_line%%=*}"
      __remote_ssh_config_scan_key="${__remote_ssh_config_scan_key#"${__remote_ssh_config_scan_key%%[![:space:]]*}"}"
      __remote_ssh_config_scan_key="${__remote_ssh_config_scan_key%"${__remote_ssh_config_scan_key##*[![:space:]]}"}"
      __remote_ssh_config_scan_index=0
      while ((__remote_ssh_config_scan_index < __remote_ssh_config_snapshot_count)); do
        if [[ "${__remote_ssh_config_snapshot_keys[__remote_ssh_config_scan_index]}" == "$__remote_ssh_config_scan_key" ]]; then
          __remote_ssh_config_scan_value="${__remote_ssh_config_scan_line#*=}"
          __remote_ssh_config_scan_value="${__remote_ssh_config_scan_value#"${__remote_ssh_config_scan_value%%[![:space:]]*}"}"
          __remote_ssh_config_scan_value="${__remote_ssh_config_scan_value%"${__remote_ssh_config_scan_value##*[![:space:]]}"}"
          case "$__remote_ssh_config_scan_value" in
            \"*\")
              __remote_ssh_config_scan_value="${__remote_ssh_config_scan_value#\"}"
              __remote_ssh_config_scan_value="${__remote_ssh_config_scan_value%\"}"
              ;;
            \'*\')
              __remote_ssh_config_scan_value="${__remote_ssh_config_scan_value#\'}"
              __remote_ssh_config_scan_value="${__remote_ssh_config_scan_value%\'}"
              ;;
          esac
          __remote_ssh_config_snapshot_values[__remote_ssh_config_scan_index]="$__remote_ssh_config_scan_value"
          __remote_ssh_config_snapshot_present[__remote_ssh_config_scan_index]=1
          break
        fi
        __remote_ssh_config_scan_index=$((__remote_ssh_config_scan_index + 1))
      done
    done <"$__remote_ssh_config_scan_file"
  } 2>/dev/null; then
    :
  fi
  return 0
}

remote_ssh_config_file_value_raw() {
  local -a __remote_ssh_config_snapshot_keys=() __remote_ssh_config_snapshot_values=()
  local -a __remote_ssh_config_snapshot_present=()
  local __remote_ssh_config_snapshot_count=0 __remote_ssh_config_lookup_index=0
  local __remote_ssh_config_lookup_key="$1"

  remote_ssh_config_snapshot_init || return $?
  remote_ssh_config_snapshot_read
  while ((__remote_ssh_config_lookup_index < __remote_ssh_config_snapshot_count)); do
    if [[ "${__remote_ssh_config_snapshot_keys[__remote_ssh_config_lookup_index]}" == "$__remote_ssh_config_lookup_key" &&
      "${__remote_ssh_config_snapshot_present[__remote_ssh_config_lookup_index]}" == 1 ]]; then
      printf '%s\n' "${__remote_ssh_config_snapshot_values[__remote_ssh_config_lookup_index]}"
      return 0
    fi
    __remote_ssh_config_lookup_index=$((__remote_ssh_config_lookup_index + 1))
  done
  return 1
}

remote_ssh_config_file_value() {
  remote_ssh_config_enabled || return 1
  remote_ssh_config_file_value_raw "$@"
}
