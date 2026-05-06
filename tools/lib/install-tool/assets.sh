# shellcheck shell=bash

ensure_this_file_sourced

select_asset() {
  local raw_os="$1" raw_arch="$2" libc="$3"
  shift 3

  local -a wanted=()
  local key rec candidate

  case "${raw_os}:${libc}" in
  linux:gnu | linux:glibc)
    wanted=(
      "linux:${raw_arch}:musl"
      "linux:${raw_arch}:glibc"
      "linux:${raw_arch}:gnu"
      "linux:${raw_arch}:any"
    )
    ;;
  linux:musl)
    wanted=(
      "linux:${raw_arch}:musl"
      "linux:${raw_arch}:any"
    )
    ;;
  darwin:*)
    wanted=("darwin:${raw_arch}:any")
    ;;
  *)
    wanted=(
      "${raw_os}:${raw_arch}:${libc}"
      "${raw_os}:${raw_arch}:any"
    )
    ;;
  esac

  for candidate in "${wanted[@]}"; do
    for rec in "$@"; do
      key="${rec%%|*}"
      [[ $key == "$candidate" ]] || continue
      echo "${rec#*|}"
      return 0
    done
  done

  return 1
}
