# shellcheck shell=bash

ensure_this_file_sourced

# echo: "<asset_template>|<arch_kind>|<os_kind>"
select_variant() {
  local raw_os="$1" raw_arch="$2" libc="$3"
  shift 3

  local wanted rec key

  # 1) exact match
  wanted="${raw_os}:${raw_arch}:${libc}"
  for rec in "$@"; do
    key="${rec%%|*}"
    [[ "$key" == "$wanted" ]] || continue
    echo "${rec#*|}"

    return 0
  done

  # 2) libc=any fallback
  wanted="${raw_os}:${raw_arch}:any"
  for rec in "$@"; do
    key="${rec%%|*}"
    [[ "$key" == "$wanted" ]] || continue
    echo "${rec#*|}"

    return 0
  done

  # 3) Linux: gnu -> musl fallback (musl build is often static and works on glibc)
  if [[ "$raw_os" == "linux" && "$libc" == "gnu" ]]; then
    wanted="${raw_os}:${raw_arch}:musl"
    for rec in "$@"; do
      key="${rec%%|*}"
      [[ "$key" == "$wanted" ]] || continue
      echo "${rec#*|}"

      return 0
    done
  fi

  return 1
}

# sets globals: ASSET_TEMPLATE ARCH_KIND OS_KIND
apply_selected_variant() {
  local selected="$1"
  # shellcheck disable=SC2034
  IFS='|' read -r ASSET_TEMPLATE ARCH_KIND OS_KIND <<<"$selected"
}
