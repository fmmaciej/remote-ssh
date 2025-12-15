# shellcheck shell=bash

ensure_this_file_sourced

# echo: "<asset_template>|<arch_kind>|<os_kind>"
select_variant() {
  local raw_os="$1" raw_arch="$2" libc="$3"
  shift 3

  local wanted rec key

  # Prefer musl on Linux (portable binaries)
  if [[ "$raw_os" == "linux" ]]; then
    wanted="linux:${raw_arch}:musl"
    for rec in "$@"; do
      key="${rec%%|*}"
      [[ "$key" == "$wanted" ]] || continue
      echo "${rec#*|}"

      return 0
    done
  fi

  # Exact match
  wanted="${raw_os}:${raw_arch}:${libc}"
  for rec in "$@"; do
    key="${rec%%|*}"
    [[ "$key" == "$wanted" ]] || continue
    echo "${rec#*|}"

    return 0
  done

  # Fallback: libc=any
  wanted="${raw_os}:${raw_arch}:any"
  for rec in "$@"; do
    key="${rec%%|*}"
    [[ "$key" == "$wanted" ]] || continue
    echo "${rec#*|}"

    return 0
  done

  return 1
}

# sets globals: ASSET_TEMPLATE ARCH_KIND OS_KIND
apply_selected_variant() {
  local selected="$1"
  # shellcheck disable=SC2034
  IFS='|' read -r ASSET_TEMPLATE ARCH_KIND OS_KIND <<<"$selected"
}
