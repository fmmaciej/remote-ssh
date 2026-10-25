# shellcheck shell=bash
# shellcheck disable=SC2034

ensure_this_file_sourced

remote_ssh_relative_path_valid() {
  case "$1" in
    ''|/*|*'|'*|*$'\n'*|*$'\r'*|*$'\t'*|*\\*) return 1 ;;
  esac
  case "/$1/" in
    *'/../'*|*'/./'*|*'//'*) return 1 ;;
  esac
}

remote_ssh_release_write() {
  local dir="$1" tool="$2" version="$3" layout="$4" executable="$5"
  printf 'format=1\ntool=%s\nversion=%s\nlayout=%s\nexecutable=%s\n' \
    "$tool" "$version" "$layout" "$executable" >"$dir/.remote-ssh-release"
}

# The fixed-order record is data, not shell code. Deletion requires a complete,
# valid record and an executable contained in a direct child of INSTALL_PREFIX.
remote_ssh_release_validate() {
  local dir="$1" expected_tool="${2:-}" file line count=0 prefix canonical parent
  local tool="" version="" layout="" executable=""
  [[ -d "$dir" && ! -L "$dir" ]] || return 1
  file="$dir/.remote-ssh-release"
  [[ -f "$file" && ! -L "$file" && -r "$file" ]] || return 1
  while IFS= read -r line || [[ -n "$line" ]]; do
    count=$((count + 1))
    case "$count:$line" in
      1:format=1) ;;
      2:tool=*) tool="${line#*=}" ;;
      3:version=*) version="${line#*=}" ;;
      4:layout=binary|4:layout=bundle) layout="${line#*=}" ;;
      5:executable=*) executable="${line#*=}" ;;
      *) return 1 ;;
    esac
  done <"$file"
  [[ $count == 5 && -n "$tool" && -n "$version" ]] || return 1
  case "$tool:$version" in *[!a-zA-Z0-9_.:+-]*) return 1 ;; esac
  [[ -f "$TOOLS_DIR/defs/$tool.sh" ]] || return 1
  [[ -z "$expected_tool" || "$tool" == "$expected_tool" ]] || return 1
  remote_ssh_relative_path_valid "$executable" || return 1
  prefix="$(cd -- "$INSTALL_PREFIX" && pwd -P)" || return 1
  canonical="$(cd -- "$dir" && pwd -P)" || return 1
  [[ "${canonical%/*}" == "$prefix" ]] || return 1
  case "${canonical##*/}" in
    "$tool-$version"|"$tool-$version".[0-9]*-[0-9]*) ;;
    *) return 1 ;;
  esac
  [[ -f "$canonical/$executable" && ! -L "$canonical/$executable" ]] || return 1
  parent="${executable%/*}"
  [[ "$parent" != "$executable" ]] || parent=.
  parent="$(cd -- "$canonical/$parent" && pwd -P)" || return 1
  case "$parent/" in "$canonical/"*) ;; *) return 1 ;; esac
  REMOTE_SSH_RELEASE_TOOL="$tool"
  REMOTE_SSH_RELEASE_VERSION="$version"
  REMOTE_SSH_RELEASE_LAYOUT="$layout"
  REMOTE_SSH_RELEASE_EXECUTABLE="$executable"
}

remote_ssh_release_for_link() {
  local link="$1" expected_tool="${2:-}" target parent prefix relative root
  [[ -L "$link" ]] || return 1
  target="$(readlink "$link")" || return 1
  case "$target" in /*) ;; *) target="${link%/*}/$target" ;; esac
  parent="$(cd -- "${target%/*}" 2>/dev/null && pwd -P)" || return 1
  prefix="$(cd -- "$INSTALL_PREFIX" 2>/dev/null && pwd -P)" || return 1
  case "$parent/" in "$prefix/"*) ;; *) return 1 ;; esac
  relative="${parent#"$prefix"/}"
  root="$prefix/${relative%%/*}"
  remote_ssh_release_validate "$root" "$expected_tool" || return 1
  [[ "$parent/${target##*/}" == "$root/$REMOTE_SSH_RELEASE_EXECUTABLE" ]] || return 1
  printf '%s\n' "$root"
}

remote_ssh_bundle_install_valid() {
  local link="$1" tool="$2" executable="$3" root
  root="$(remote_ssh_release_for_link "$link" "$tool")" || return 1
  remote_ssh_release_validate "$root" "$tool" || return 1
  [[ "$REMOTE_SSH_RELEASE_LAYOUT" == bundle && "$REMOTE_SSH_RELEASE_EXECUTABLE" == "$executable" ]]
}
