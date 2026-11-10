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
  prefix="$(cd -P -- "$INSTALL_PREFIX" 2>/dev/null && pwd -P && printf '\001')" || return 1
  prefix="${prefix%$'\001'}" prefix="${prefix%$'\n'}"
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

# A: parse identity independently of payload health. A saved, explicitly named
# tool can outlive its definition; this never authorizes recursive deletion.
remote_ssh_release_identify() {
  local dir="$1" expected_tool="${2:-}" saved="${3:-}" file line count=0 prefix canonical body status extra
  local tool="" version="" layout="" executable="" format="" kind=""
  [[ -d "$dir" && ! -L "$dir" && -O "$dir" ]] || return 1
  file="$dir/.remote-ssh-release"
  [[ -f "$file" && ! -L "$file" && -r "$file" && -O "$file" ]] || return 1
  # Capture a complete producer result before accepting any marker field.
  {
    IFS= read -r -d '' body && IFS= read -r -d '' status || return 1
    [[ "$status" == 0 ]] || return 1
    extra=""
    if IFS= read -r -d '' extra || [[ -n "$extra" ]]; then return 1; fi
  } < <(command -p cat "$file"; status=$?; printf '\0%s\0' "$status")
  body="${body%$'\n'}"
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
  done <<<"$body"
  [[ $count == 5 && -n "$tool" && -n "$version" ]] || return 1
  case "$format:$layout:$kind" in 1:binary:executable|1:bundle:executable|2:bash-builtin:library) ;; *) return 1 ;; esac
  case "$tool:$version" in *[!a-zA-Z0-9_.:+-]*) return 1 ;; esac
  [[ -f "$TOOLS_DIR/defs/$tool.sh" || ( "$saved" == saved && "$expected_tool" == "$tool" ) ]] || return 1
  [[ -z "$expected_tool" || "$tool" == "$expected_tool" ]] || return 1
  remote_ssh_relative_path_valid "$executable" || return 1
  prefix="$(cd -P -- "$INSTALL_PREFIX" && pwd -P && printf '\001')" || return 1
  prefix="${prefix%$'\001'}" prefix="${prefix%$'\n'}"
  prefix="${prefix%/}"
  canonical="$(cd -P -- "$dir" && pwd -P)" || return 1
  [[ "${canonical%/*}" == "$prefix" ]] || return 1
  remote_ssh_release_name_matches_version "${canonical##*/}" "$tool" "$version" || return 1
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


# Check every component without traversing a symlink, even one that resolves
# back inside the release. B permits a missing leaf, never a missing parent.
remote_ssh_release_member_valid() {
  local root="$1" member="$2" missing="${3:-0}" current="$1" part
  remote_ssh_relative_path_valid "$member" || return 1
  while [[ "$member" == */* ]]; do
    part="${member%%/*}" member="${member#*/}"
    current="$current/$part"
    [[ -d "$current" && ! -L "$current" && -x "$current" ]] || return 1
  done
  current="$current/$member"
  if [[ ! -e "$current" && ! -L "$current" ]]; then
    [[ "$missing" == 1 ]]
  else
    [[ -f "$current" && ! -L "$current" ]]
  fi
}

# C: the old deletion API retains its known-definition restriction. The saved
# variant is only for explicit retired receipts and has exactly the same live
# filesystem proof. Receipts cannot replace a missing payload or parent.
remote_ssh_release_delete_valid() {
  remote_ssh_release_identify "$1" "${2:-}" "${3:-}" || return 1
  remote_ssh_release_member_valid "$REMOTE_SSH_RELEASE_DIR" "$REMOTE_SSH_RELEASE_FILE" || return 1
  [[ "$REMOTE_SSH_RELEASE_LAYOUT" != bash-builtin || -r "$REMOTE_SSH_RELEASE_DIR/$REMOTE_SSH_RELEASE_FILE" ]]
}

remote_ssh_release_validate() {
  remote_ssh_release_delete_valid "$1" "${2:-}"
}

# Preserve literal trailing newlines and distinguish an I/O failure (2).
remote_ssh_readlink_literal() {
  local value
  [[ -L "$1" ]] || return 1
  value="$(readlink "$1" && printf '\001')" || return 2
  REMOTE_SSH_LITERAL_TARGET="${value%$'\001'}"
  # readlink adds one newline, which is not part of the target.
  REMOTE_SSH_LITERAL_TARGET="${REMOTE_SSH_LITERAL_TARGET%$'\n'}"
}

# B: only the exact selector and receipt target may be replaced. A missing
# payload is repairable, but a replaced parent, leaf, marker or selector is not.
remote_ssh_selector_repair_valid() {
  local link="$1" root="$2" tool="$3" version="$4" layout="$5" member="$6" literal="$7" parent bin value prefix
  value="$(cd -P -- "$INSTALL_PREFIX" && pwd -P && printf '\001')" || return 1
  prefix="${value%$'\001'}" prefix="${prefix%$'\n'}"
  if [[ "${link%/*}" == "$prefix/.active" || "${link%/*}" == "$INSTALL_PREFIX/.active" ]]; then
    remote_ssh_active_dir_valid || return 1
  else
    value="$(cd -P -- "${link%/*}" && pwd -P && printf '\001')" || return 1
    parent="${value%$'\001'}" parent="${parent%$'\n'}"
    value="$(cd -P -- "$INSTALL_BIN_DIR" && pwd -P && printf '\001')" || return 1
    bin="${value%$'\001'}" bin="${bin%$'\n'}"
    [[ "$parent" == "$bin" ]] || return 1
  fi
  remote_ssh_readlink_literal "$link" || return "$?"
  [[ "$REMOTE_SSH_LITERAL_TARGET" == "$literal" ]] || return 1
  remote_ssh_release_identify "$root" "$tool" saved || return 1
  [[ "$REMOTE_SSH_RELEASE_VERSION" == "$version" && "$REMOTE_SSH_RELEASE_LAYOUT" == "$layout" &&
     "$REMOTE_SSH_RELEASE_FILE" == "$member" ]] || return 1
  remote_ssh_release_member_valid "$REMOTE_SSH_RELEASE_DIR" "$member" 1 || return 1
  # Resolve only after proving all parents. A missing leaf remains resolvable.
  [[ "$(remote_ssh_link_target_path "$link")" == "$REMOTE_SSH_RELEASE_DIR/$member" ]]
}

# Structural health never runs the executable or loads a library. Extra bundle
# data paths come from trusted definitions or validated saved manifest records.
remote_ssh_release_health() {
  local root="$1" tool="$2" layout="$3" member="$4" required
  shift 4
  remote_ssh_release_identify "$root" "$tool" saved || return 1
  [[ "$REMOTE_SSH_RELEASE_LAYOUT" == "$layout" && "$REMOTE_SSH_RELEASE_FILE" == "$member" ]] || return 1
  remote_ssh_release_member_valid "$root" "$member" || return 1
  if [[ "$layout" == bash-builtin ]]; then
    [[ -r "$root/$member" ]] || return 1
  else
    [[ -x "$root/$member" ]] || return 1
  fi
  for required in "$@"; do
    remote_ssh_relative_path_valid "$required" || return 1
    remote_ssh_release_data_valid "$root" "$required" || return 1
  done
}

remote_ssh_release_data_valid() {
  local current="$1" remaining="$2"
  remote_ssh_relative_path_valid "$remaining" || return 1
  while :; do
    current="$current/${remaining%%/*}"
    [[ ! -L "$current" && -r "$current" ]] || return 1
    if [[ "$remaining" != */* ]]; then
      [[ -f "$current" || ( -d "$current" && -x "$current" ) ]]
      return "$?"
    fi
    [[ -d "$current" && -x "$current" ]] || return 1
    remaining="${remaining#*/}"
  done
}

remote_ssh_release_for_link() {
  local link="$1" expected_tool="${2:-}" target prefix relative root
  target="$(remote_ssh_link_target_path "$link")" || return "$?"
  prefix="$(cd -P -- "$INSTALL_PREFIX" 2>/dev/null && pwd -P && printf '\001')" || return 1
  prefix="${prefix%$'\001'}" prefix="${prefix%$'\n'}"
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
