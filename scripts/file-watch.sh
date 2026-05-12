#!/usr/bin/env bash

set -euo pipefail

if ((BASH_VERSINFO[0] < 4)); then
  printf 'ERROR: file-watch requires Bash 4 or newer for associative arrays.\n' >&2
  exit 2
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DEFAULT_CONFIG="$REPO_DIR/dots/file-watch.json"
FILE_WATCH_TMP_DIR=""

declare -A GIT_REF_SHA=()
declare -A GIT_REF_SOURCE_REF=()
declare -A GIT_REF_SOURCE_KIND=()
declare -A GIT_REF_LOCAL_REF=()
declare -A GIT_REF_BARE_REPO=()
declare -A GIT_REF_FETCHED=()

cleanup() {
  if [[ -n "${FILE_WATCH_TMP_DIR:-}" ]]; then
    rm -rf "$FILE_WATCH_TMP_DIR"
  fi
}

trap cleanup EXIT

usage() {
  cat <<EOF
Usage:
  $0 run [config.json]
  $0 compare <left-file-or-pointer> <right-file-or-pointer> [config.json]

Exit codes:
  0  no differences, already checked, or all configured watches passed
  1  differences detected where fail_on_diff=true, or ad hoc compare differs
  2  configuration/tooling/Git error
  3  target file missing
EOF
}

error() {
  printf 'ERROR: %s\n' "$*" >&2
}

die_config() {
  error "$*"
  exit 2
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || die_config "Required command not found: $1"
}

expand_user_path() {
  local path="$1"

  case "$path" in
    \~)
      [[ -n "${HOME:-}" ]] || die_config "Cannot expand ~ because HOME is not set."
      printf '%s\n' "$HOME"
      ;;
    \~/*)
      [[ -n "${HOME:-}" ]] || die_config "Cannot expand ~ because HOME is not set."
      printf '%s/%s\n' "$HOME" "${path#~/}"
      ;;
    \~*)
      die_config "Unsupported path expansion: $path. Use ~ or ~/path only."
      ;;
    *)
      printf '%s\n' "$path"
      ;;
  esac
}

json_get_required_string() {
  local config="$1" filter="$2" label="$3" value

  if ! value="$(jq -er "$filter | select(type == \"string\" and length > 0)" "$config")"; then
    die_config "Missing required non-empty string config field: $label"
  fi

  printf '%s\n' "$value"
}

json_get_optional_bool() {
  local config="$1" filter="$2" label="$3"

  jq -r "$filter as \$v | if \$v == null then false elif (\$v | type == \"boolean\") then \$v else error(\"${label} must be a boolean\") end" "$config" 2>/dev/null ||
    die_config "Config field $label must be a boolean when present."
}

json_pointer_exists() {
  local config="$1" name="$2"

  jq -e --arg name "$name" '.pointers[$name] and (.pointers[$name] | type == "object")' "$config" >/dev/null 2>&1
}

validate_file_path() {
  local file="$1"

  [[ -n "$file" ]] || die_config "Git pointer file path is empty."

  case "$file" in
    /*)
      die_config "Git pointer file path must be relative: $file"
      ;;
    *"/../"* | "../"* | *"/.." | "..")
      die_config "Git pointer file path must not contain '..': $file"
      ;;
  esac
}

repo_cache_hash() {
  local value="$1"

  printf '%s' "$value" | git hash-object --stdin
}

short_sha() {
  local sha="$1"

  printf '%s\n' "${sha:0:12}"
}

file_fingerprint() {
  local path="$1" meta

  [[ -f "$path" ]] || return 3

  if meta="$(stat -f '%m:%z' "$path" 2>/dev/null)"; then
    :
  elif meta="$(stat -c '%Y:%s' "$path" 2>/dev/null)"; then
    :
  else
    die_config "Could not stat file: $path"
  fi

  printf 'file:%s:%s\n' "$path" "$meta"
}

ensure_bare_cache() {
  local bare_repo="$1"

  if [[ -d "$bare_repo" ]]; then
    git --git-dir "$bare_repo" rev-parse --is-bare-repository >/dev/null 2>&1 ||
      die_config "Cache path exists but is not a bare Git repository: $bare_repo"
    return 0
  fi

  git init --bare "$bare_repo" >/dev/null 2>&1 ||
    die_config "Could not initialize bare cache repository: $bare_repo"
}

resolve_remote_ref() {
  local repo="$1" ref="$2"
  local line sha source_ref source_kind

  if line="$(git ls-remote "$repo" "refs/heads/$ref" 2>/dev/null)" && [[ -n "$line" ]]; then
    sha="${line%%[[:space:]]*}"
    source_ref="refs/heads/$ref"
    source_kind="branch"
  elif line="$(git ls-remote "$repo" "refs/tags/$ref^{}" 2>/dev/null)" && [[ -n "$line" ]]; then
    sha="${line%%[[:space:]]*}"
    source_ref="refs/tags/$ref"
    source_kind="tag"
  elif line="$(git ls-remote "$repo" "refs/tags/$ref" 2>/dev/null)" && [[ -n "$line" ]]; then
    sha="${line%%[[:space:]]*}"
    source_ref="refs/tags/$ref"
    source_kind="tag"
  elif [[ "$ref" =~ ^[0-9a-fA-F]{40}$ ]]; then
    sha="$ref"
    source_ref="$ref"
    source_kind="commit"
  elif line="$(git ls-remote "$repo" "$ref" 2>/dev/null)" && [[ -n "$line" ]]; then
    sha="${line%%[[:space:]]*}"
    source_ref="$ref"
    source_kind="ref"
  else
    die_config "Could not resolve Git ref '$ref' in $repo"
  fi

  printf '%s|%s|%s\n' "$sha" "$source_ref" "$source_kind"
}

git_ref_key() {
  local repo="$1" ref="$2"

  printf '%s|%s\n' "$repo" "$ref"
}

git_ref_local_ref() {
  local repo="$1" ref="$2"

  printf 'refs/file-watch/%s\n' "$(repo_cache_hash "$repo|$ref")"
}

resolve_git_pointer() {
  local repo="$1" ref="$2"
  local key resolved sha source_ref source_kind local_ref

  key="$(git_ref_key "$repo" "$ref")"
  if [[ -n "${GIT_REF_SHA[$key]:-}" ]]; then
    return 0
  fi

  resolved="$(resolve_remote_ref "$repo" "$ref")"
  IFS='|' read -r sha source_ref source_kind <<<"$resolved"
  local_ref="$(git_ref_local_ref "$repo" "$ref")"

  GIT_REF_SHA[$key]="$sha"
  GIT_REF_SOURCE_REF[$key]="$source_ref"
  GIT_REF_SOURCE_KIND[$key]="$source_kind"
  GIT_REF_LOCAL_REF[$key]="$local_ref"
}

fetch_git_pointer() {
  local repo="$1" ref="$2" cache_dir="$3"
  local key repo_hash bare_repo local_ref source_ref source_kind

  key="$(git_ref_key "$repo" "$ref")"
  [[ -n "${GIT_REF_FETCHED[$key]:-}" ]] && return 0

  resolve_git_pointer "$repo" "$ref"
  local_ref="${GIT_REF_LOCAL_REF[$key]}"
  source_ref="${GIT_REF_SOURCE_REF[$key]}"
  source_kind="${GIT_REF_SOURCE_KIND[$key]}"

  mkdir -p "$cache_dir" || die_config "Could not create cache directory: $cache_dir"
  repo_hash="$(repo_cache_hash "$repo")"
  bare_repo="$cache_dir/${repo_hash}.git"
  ensure_bare_cache "$bare_repo"

  case "$source_kind" in
    branch | tag | ref)
      git --git-dir "$bare_repo" fetch --quiet --depth=1 "$repo" "+${source_ref}:${local_ref}" ||
        die_config "Could not fetch Git ref '$ref' from $repo"
      ;;
    commit)
      git --git-dir "$bare_repo" fetch --quiet --depth=1 "$repo" "+${source_ref}:${local_ref}" ||
        die_config "Could not fetch Git commit '$ref' from $repo"
      ;;
    *)
      die_config "Unsupported Git source kind: $source_kind"
      ;;
  esac

  GIT_REF_BARE_REPO[$key]="$bare_repo"
  GIT_REF_FETCHED[$key]=1
}

pointer_type_from_filter() {
  local config="$1" filter="$2" label="$3"

  json_get_required_string "$config" "$filter.type" "$label.type"
}

materialize_pointer_from_filter() {
  local config="$1" filter="$2" label="$3" output="$4" cache_dir="$5"
  local type path repo ref file bare_repo local_ref id

  type="$(pointer_type_from_filter "$config" "$filter" "$label")"
  case "$type" in
    file)
      path="$(expand_user_path "$(json_get_required_string "$config" "$filter.path" "$label.path")")"
      if [[ ! -f "$path" ]]; then
        error "Target file does not exist at $label: $path"
        return 3
      fi
      cp "$path" "$output"
      file_fingerprint "$path"
      ;;
    git)
      repo="$(json_get_required_string "$config" "$filter.repo" "$label.repo")"
      ref="$(json_get_required_string "$config" "$filter.ref" "$label.ref")"
      file="$(json_get_required_string "$config" "$filter.file" "$label.file")"
      validate_file_path "$file"
      fetch_git_pointer "$repo" "$ref" "$cache_dir"
      key="$(git_ref_key "$repo" "$ref")"
      bare_repo="${GIT_REF_BARE_REPO[$key]}"
      local_ref="${GIT_REF_LOCAL_REF[$key]}"
      if ! git --git-dir "$bare_repo" show "${local_ref}:${file}" >"$output" 2>/dev/null; then
        error "Target file does not exist at $label: $file"
        return 3
      fi
      id="git:${repo}:${ref}:${GIT_REF_SHA[$key]}:${file}"
      printf '%s\n' "$id"
      ;;
    *)
      die_config "Unsupported pointer type at $label: $type"
      ;;
  esac
}

materialize_watch_side() {
  local config="$1" filter="$2" label="$3" output="$4" cache_dir="$5"
  local pointer_name quoted_pointer

  pointer_name="$(jq -er "$filter | select(type == \"string\" and length > 0)" "$config" 2>/dev/null || true)"
  if [[ -n "$pointer_name" ]]; then
    json_pointer_exists "$config" "$pointer_name" ||
      die_config "Unknown pointer referenced by $label: $pointer_name"
    quoted_pointer="$(jq -rn --arg value "$pointer_name" '$value | @json')"
    materialize_pointer_from_filter "$config" ".pointers[$quoted_pointer]" "pointers.$pointer_name" "$output" "$cache_dir"
    return
  fi

  jq -e "$filter | type == \"object\"" "$config" >/dev/null 2>&1 ||
    die_config "Config field $label must be a pointer object or pointer name."

  materialize_pointer_from_filter "$config" "$filter" "$label" "$output" "$cache_dir"
}

materialize_operand() {
  local config="$1" operand="$2" output="$3" cache_dir="$4"

  if json_pointer_exists "$config" "$operand"; then
    local quoted_operand
    quoted_operand="$(jq -rn --arg value "$operand" '$value | @json')"
    materialize_pointer_from_filter "$config" ".pointers[$quoted_operand]" "pointers.$operand" "$output" "$cache_dir"
    return
  fi

  local path
  path="$(expand_user_path "$operand")"
  if [[ ! -f "$path" ]]; then
    error "Target file does not exist: $operand"
    return 3
  fi
  cp "$path" "$output"
  file_fingerprint "$path"
}

state_matches() {
  local state_file="$1" name="$2" left_id="$3" right_id="$4"

  [[ -f "$state_file" ]] || return 1
  jq -e 'type == "object"' "$state_file" >/dev/null 2>&1 ||
    die_config "State file is not a JSON object: $state_file"

  jq -e --arg name "$name" --arg left "$left_id" --arg right "$right_id" \
    '.[$name] and .[$name].left_id == $left and .[$name].right_id == $right' \
    "$state_file" >/dev/null 2>&1
}

write_state() {
  local state_file="$1" name="$2" left_id="$3" right_id="$4" result="$5"
  local state_dir tmp checked_at

  state_dir="${state_file%/*}"
  mkdir -p "$state_dir" || die_config "Could not create state directory: $state_dir"
  checked_at="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  tmp="${state_file}.$$"

  if [[ -f "$state_file" ]]; then
    jq --arg name "$name" --arg left "$left_id" --arg right "$right_id" --arg result "$result" --arg checked_at "$checked_at" \
      'if type == "object" then
        .[$name] = {
          left_id: $left,
          right_id: $right,
          last_result: $result,
          last_checked_at: $checked_at
        }
      else
        error("state root must be an object")
      end' "$state_file" >"$tmp" ||
      die_config "Could not update state file: $state_file"
  else
    jq -n --arg name "$name" --arg left "$left_id" --arg right "$right_id" --arg result "$result" --arg checked_at "$checked_at" \
      '{($name): {
        left_id: $left,
        right_id: $right,
        last_result: $result,
        last_checked_at: $checked_at
      }}' >"$tmp" ||
      die_config "Could not create state file: $state_file"
  fi

  mv "$tmp" "$state_file" || die_config "Could not replace state file: $state_file"
}

compare_materialized_files() {
  local left_file="$1" right_file="$2" left_label="$3" right_label="$4"

  : "$left_label" "$right_label"

  diff -u "$left_file" "$right_file"
}

config_cache_dir() {
  local config="$1"

  expand_user_path "$(json_get_required_string "$config" '.cache_dir' cache_dir)"
}

config_state_file() {
  local config="$1"

  expand_user_path "$(json_get_required_string "$config" '.state_file' state_file)"
}

run_watch() {
  local config="$1" index="$2" cache_dir="$3" state_file="$4"
  local name fail_on_diff left_file right_file left_id right_id diff_status materialize_status

  name="$(json_get_required_string "$config" ".watches[$index].name" "watches[$index].name")"
  fail_on_diff="$(json_get_optional_bool "$config" ".watches[$index].fail_on_diff" "watches[$index].fail_on_diff")"

  left_file="$FILE_WATCH_TMP_DIR/${name}.left"
  right_file="$FILE_WATCH_TMP_DIR/${name}.right"

  set +e
  left_id="$(materialize_watch_side "$config" ".watches[$index].left" "watches[$index].left" "$left_file" "$cache_dir")"
  materialize_status=$?
  set -e
  ((materialize_status == 0)) || return "$materialize_status"

  set +e
  right_id="$(materialize_watch_side "$config" ".watches[$index].right" "watches[$index].right" "$right_file" "$cache_dir")"
  materialize_status=$?
  set -e
  ((materialize_status == 0)) || return "$materialize_status"

  if state_matches "$state_file" "$name" "$left_id" "$right_id"; then
    printf 'file-watch: %s already checked; skipping diff.\n' "$name"
    return 0
  fi

  set +e
  compare_materialized_files "$left_file" "$right_file" "$name:left" "$name:right"
  diff_status=$?
  set -e

  if ((diff_status == 0)); then
    printf 'file-watch: no differences for %s.\n' "$name"
    write_state "$state_file" "$name" "$left_id" "$right_id" "no-diff"
    return 0
  fi

  if ((diff_status == 1)); then
    printf 'file-watch: differences found for %s.\n' "$name"
    write_state "$state_file" "$name" "$left_id" "$right_id" "diff"
    if [[ "$fail_on_diff" == "true" ]]; then
      return 1
    fi
    return 0
  fi

  write_state "$state_file" "$name" "$left_id" "$right_id" "error"
  die_config "diff failed for watch: $name"
}

run_all() {
  local config="$1" cache_dir state_file count index failed=0 status

  [[ -r "$config" ]] || die_config "Config file is not readable: $config"
  jq -e 'type == "object" and (.watches | type == "array")' "$config" >/dev/null 2>&1 ||
    die_config "Config must be a JSON object with watches array: $config"

  cache_dir="$(config_cache_dir "$config")"
  state_file="$(config_state_file "$config")"
  count="$(jq -r '.watches | length' "$config")"

  for ((index = 0; index < count; index++)); do
    set +e
    run_watch "$config" "$index" "$cache_dir" "$state_file"
    status=$?
    set -e
    case "$status" in
      0) ;;
      1) failed=1 ;;
      3) return 3 ;;
      *) return "$status" ;;
    esac
  done

  return "$failed"
}

compare_ad_hoc() {
  local left="$1" right="$2" config="$3" cache_dir left_file right_file left_id right_id diff_status materialize_status

  [[ -r "$config" ]] || die_config "Config file is not readable: $config"
  jq -e 'type == "object"' "$config" >/dev/null 2>&1 ||
    die_config "Config must be a JSON object: $config"

  cache_dir="$(config_cache_dir "$config")"
  left_file="$FILE_WATCH_TMP_DIR/compare.left"
  right_file="$FILE_WATCH_TMP_DIR/compare.right"

  set +e
  left_id="$(materialize_operand "$config" "$left" "$left_file" "$cache_dir")"
  materialize_status=$?
  set -e
  ((materialize_status == 0)) || return "$materialize_status"

  set +e
  right_id="$(materialize_operand "$config" "$right" "$right_file" "$cache_dir")"
  materialize_status=$?
  set -e
  ((materialize_status == 0)) || return "$materialize_status"

  set +e
  compare_materialized_files "$left_file" "$right_file" "$left" "$right"
  diff_status=$?
  set -e

  if ((diff_status == 0)); then
    printf 'file-watch: no differences for ad hoc compare.\n'
    return 0
  fi

  if ((diff_status == 1)); then
    printf 'file-watch: differences found for ad hoc compare.\n'
    printf 'file-watch: left=%s\n' "$left_id"
    printf 'file-watch: right=%s\n' "$right_id"
    return 1
  fi

  die_config "diff failed for ad hoc compare."
}

main() {
  if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    return 0
  fi

  require_command git
  require_command jq
  require_command diff
  require_command mktemp
  require_command cp
  require_command stat

  FILE_WATCH_TMP_DIR="$(mktemp -d)"

  local command="${1:-run}"
  case "$command" in
    run)
      shift
      (($# <= 1)) || {
        usage >&2
        return 2
      }
      run_all "${1:-$DEFAULT_CONFIG}"
      ;;
    compare)
      shift
      (($# == 2 || $# == 3)) || {
        usage >&2
        return 2
      }
      compare_ad_hoc "$1" "$2" "${3:-$DEFAULT_CONFIG}"
      ;;
    *)
      # Backward-friendly default: a single config path means run that config.
      if (($# == 1)) && [[ -r "$command" ]]; then
        run_all "$command"
      else
        usage >&2
        return 2
      fi
      ;;
  esac
}

main "$@"
