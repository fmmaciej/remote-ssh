# shellcheck shell=bash

ensure_this_file_sourced

# args: <archive_name>
# uses: ZIP_SUPPORTED
extract_archive_in_pwd() {
  local archive_name="$1"

  case "$archive_name" in
  *.tar.gz | *.tgz)
    tar xzf "$archive_name"
    ;;
  *.zip)
    [[ ${ZIP_SUPPORTED:-0} -eq 1 ]] || {
      echo "unzip not available" >&2
      return 1
    }
    unzip -q "$archive_name"
    ;;
  *)
    echo "Unknown archive format: $archive_name" >&2
    return 1
    ;;
  esac
}

# Bundle archives have an explicitly declared root and contain only ordinary
# files/directories. Reject links and special files before any extraction.
extract_bundle_archive() {
  local archive="$1" root="$2" names details name line
  case "$archive" in *.tar.gz|*.tgz) ;; *) log_error "Bundle requires a tar.gz or tgz archive"; return 1 ;; esac
  remote_ssh_relative_path_valid "$root" || return 1
  names="$(LC_ALL=C tar -tzf "$archive")" || return 1
  details="$(LC_ALL=C tar -tvzf "$archive")" || return 1
  [[ -n "$names" && -n "$details" ]] || return 1
  while IFS= read -r name; do
    while [[ "$name" == ./* ]]; do name="${name#./}"; done
    name="${name%/}"
    remote_ssh_relative_path_valid "$name" || {
      log_error "Unsafe bundle member: $name"
      return 1
    }
    case "$name" in "$root"|"$root/"*) ;; *) log_error "Bundle member outside declared root: $name"; return 1 ;; esac
  done <<<"$names"
  while IFS= read -r line; do
    case "${line:0:1}" in -|d) ;; *) log_error "Bundle contains a link or special file"; return 1 ;; esac
  done <<<"$details"
  mkdir payload || return 1
  tar -xzf "$archive" -C payload
}
