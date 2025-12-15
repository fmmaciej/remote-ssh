# shellcheck shell=bash

ensure_this_file_sourced

# args: <archive_name>
# uses: ZIP_SUPPORTED
extract_archive_in_pwd() {
  local archive_name="$1"

  case "$archive_name" in
    *.tar.gz|*.tgz)
      tar xzf "$archive_name"
      ;;
    *.zip)
      [[ "${ZIP_SUPPORTED:-0}" -eq 1 ]] || { echo "unzip not available" >&2; return 1; }
      unzip -q "$archive_name"
      ;;
    *)
      echo "Unknown archive format: $archive_name" >&2
      return 1
      ;;
  esac
}
