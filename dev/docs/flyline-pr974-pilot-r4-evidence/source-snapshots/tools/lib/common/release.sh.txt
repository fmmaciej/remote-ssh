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

remote_ssh_library_release_write() {
  printf 'format=2\ntool=%s\nversion=%s\nlayout=bash-builtin\nlibrary=%s\n' \
    "$2" "$3" "$4" >"$1/.remote-ssh-release"
}

# The active library directory is owned by the prefix, never a redirected path.
remote_ssh_active_dir_valid() {
  [[ -d "$INSTALL_PREFIX/.active" && ! -L "$INSTALL_PREFIX/.active" &&
    -r "$INSTALL_PREFIX/.active" && -x "$INSTALL_PREFIX/.active" ]]
}

remote_ssh_tool_link() {
  if [[ "${INSTALL_LAYOUT:-binary}" == bash-builtin ]]; then
    printf '%s/.active/%s\n' "${INSTALL_PREFIX%/}" "$1"
  else
    printf '%s/%s\n' "${INSTALL_BIN_DIR%/}" "$1"
  fi
}

remote_ssh_library_member_declared() {
  local record
  for record in ${LIBRARY_MEMBERS[@]+"${LIBRARY_MEMBERS[@]}"}; do
    [[ "${record#*|}" != "$1" ]] || return 0
  done
  return 1
}

remote_ssh_library_install_valid() {
  local link="$1" tool="$2" version="${3:-}"
  remote_ssh_active_dir_valid || return 1
  # Keep validated metadata in this process instead of losing it in a command
  # substitution and validating the same record a second time at shell startup.
  remote_ssh_release_for_link "$link" "$tool" >/dev/null || return 1
  [[ "$REMOTE_SSH_RELEASE_LAYOUT" == bash-builtin &&
    ( -z "$version" || "$REMOTE_SSH_RELEASE_VERSION" == "$version" ) ]] || return 1
  remote_ssh_library_member_declared "$REMOTE_SSH_RELEASE_LIBRARY"
}

# Resolve directory symlinks before '..', just as filesystem path lookup does.
remote_ssh_link_target_path() {
  local link="$1" target parent link_dir
  [[ -L "$link" ]] || return 1
  # Keep an I/O failure distinct from an ordinary unresolved/unmanaged link.
  target="$(readlink "$link")" || return 2
  case "$target" in
    /*) ;;
    *)
      link_dir="${link%/*}"
      [[ "$link_dir" != "$link" ]] || link_dir=.
      target="$link_dir/$target"
      ;;
  esac
  parent="$(cd -P -- "${target%/*}" 2>/dev/null && pwd -P)" || return 1
  printf '%s/%s\n' "${parent%/}" "${target##*/}"
}

remote_ssh_release_name_matches_version() {
  local name="$1" tool="$2" version="$3" suffix

  [[ "$name" == "$tool-$version" ]] && return 0
  case "$name" in
    "$tool-$version".*)
      suffix="${name#"$tool-$version."}"
      [[ "$suffix" =~ ^[0-9]+-[0-9]+$ ]]
      ;;
    *) return 1 ;;
  esac
}

# Marked releases use their recorded version. Only absent records allow legacy
# matching against the exact release name or the installer's numeric suffix.
remote_ssh_link_matches_version() {
  local link="$1" tool="$2" version="$3" target prefix relative root record

  target="$(remote_ssh_link_target_path "$link")" || return 1
  [[ -f "$target" && ! -L "$target" ]] || return 1
  prefix="$(cd -P -- "$INSTALL_PREFIX" 2>/dev/null && pwd -P)" || return 1
  prefix="${prefix%/}"
  case "$target" in "$prefix/"*) ;; *) return 1 ;; esac
  relative="${target#"$prefix"/}"
  root="$prefix/${relative%%/*}"
  record="$root/.remote-ssh-release"

  if [[ -e "$record" || -L "$record" ]]; then
    remote_ssh_release_for_link "$link" "$tool" >/dev/null || return 1
    [[ "$REMOTE_SSH_RELEASE_VERSION" == "$version" ]]
  else
    remote_ssh_release_name_matches_version "${root##*/}" "$tool" "$version"
  fi
}

# The fixed-order record is data, not shell code. Deletion requires a complete,
# valid record and an executable contained in a direct child of INSTALL_PREFIX.
remote_ssh_release_validate() {
  local dir="$1" expected_tool="${2:-}" file line count=0 prefix canonical parent
  local tool="" version="" layout="" executable="" format="" kind="" member current
  [[ -d "$dir" && ! -L "$dir" ]] || return 1
  file="$dir/.remote-ssh-release"
  [[ -f "$file" && ! -L "$file" && -r "$file" ]] || return 1
  while IFS= read -r line || [[ -n "$line" ]]; do
    count=$((count + 1))
    case "$count:$line" in
      1:format=1|1:format=2) format="${line#*=}" ;;
      2:tool=*) tool="${line#*=}" ;;
      3:version=*) version="${line#*=}" ;;
      4:layout=binary|4:layout=bundle) layout="${line#*=}" ;;
      4:layout=bash-builtin) layout=bash-builtin ;;
      5:executable=*) executable="${line#*=}"; kind=executable ;;
      5:library=*) executable="${line#*=}"; kind=library ;;
      *) return 1 ;;
    esac
  done <"$file"
  [[ $count == 5 && -n "$tool" && -n "$version" ]] || return 1
  case "$format:$layout:$kind" in 1:binary:executable|1:bundle:executable|2:bash-builtin:library) ;; *) return 1 ;; esac
  case "$tool:$version" in *[!a-zA-Z0-9_.:+-]*) return 1 ;; esac
  [[ -f "$TOOLS_DIR/defs/$tool.sh" ]] || return 1
  [[ -z "$expected_tool" || "$tool" == "$expected_tool" ]] || return 1
  remote_ssh_relative_path_valid "$executable" || return 1
  prefix="$(cd -P -- "$INSTALL_PREFIX" && pwd -P)" || return 1
  prefix="${prefix%/}"
  canonical="$(cd -P -- "$dir" && pwd -P)" || return 1
  [[ "${canonical%/*}" == "$prefix" ]] || return 1
  remote_ssh_release_name_matches_version "${canonical##*/}" "$tool" "$version" || return 1
  [[ -f "$canonical/$executable" && ! -L "$canonical/$executable" ]] || return 1
  if [[ "$layout" == bash-builtin ]]; then
    [[ -r "$canonical/$executable" ]] || return 1
    member="$executable" current="$canonical"
    while :; do
      current="$current/${member%%/*}"
      [[ ! -L "$current" ]] || return 1
      [[ "$member" == */* ]] || break
      member="${member#*/}"
    done
  fi
  parent="${executable%/*}"
  [[ "$parent" != "$executable" ]] || parent=.
  parent="$(cd -P -- "$canonical/$parent" && pwd -P)" || return 1
  case "$parent/" in "$canonical/"*) ;; *) return 1 ;; esac
  REMOTE_SSH_RELEASE_TOOL="$tool"
  REMOTE_SSH_RELEASE_DIR="$canonical"
  REMOTE_SSH_RELEASE_VERSION="$version"
  REMOTE_SSH_RELEASE_LAYOUT="$layout"
  REMOTE_SSH_RELEASE_FILE="$executable"
  REMOTE_SSH_RELEASE_EXECUTABLE=""
  REMOTE_SSH_RELEASE_LIBRARY=""
  if [[ "$layout" == bash-builtin ]]; then
    REMOTE_SSH_RELEASE_LIBRARY="$executable"
  else
    REMOTE_SSH_RELEASE_EXECUTABLE="$executable"
  fi
}

remote_ssh_release_for_link() {
  local link="$1" expected_tool="${2:-}" target prefix relative root
  target="$(remote_ssh_link_target_path "$link")" || return "$?"
  prefix="$(cd -P -- "$INSTALL_PREFIX" 2>/dev/null && pwd -P)" || return 1
  prefix="${prefix%/}"
  case "$target" in "$prefix/"*) ;; *) return 1 ;; esac
  relative="${target#"$prefix"/}"
  root="$prefix/${relative%%/*}"
  remote_ssh_release_validate "$root" "$expected_tool" || return 1
  [[ "$target" == "$root/$REMOTE_SSH_RELEASE_FILE" ]] || return 1
  printf '%s\n' "$root"
}

remote_ssh_bundle_install_valid() {
  local link="$1" tool="$2" executable="$3" root
  root="$(remote_ssh_release_for_link "$link" "$tool")" || return 1
  remote_ssh_release_validate "$root" "$tool" || return 1
  [[ "$REMOTE_SSH_RELEASE_LAYOUT" == bundle && "$REMOTE_SSH_RELEASE_EXECUTABLE" == "$executable" ]]
}
