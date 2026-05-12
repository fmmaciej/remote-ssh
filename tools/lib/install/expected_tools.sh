# shellcheck shell=bash

ensure_this_file_sourced

trim_tool_line() {
  local line="$1"

  line="${line%%#*}"
  line="${line#"${line%%[![:space:]]*}"}"
  line="${line%"${line##*[![:space:]]}"}"
  printf '%s\n' "$line"
}

expected_tools_file() {
  local config_home

  config_home="${XDG_CONFIG_HOME:-$HOME/.config}"
  printf '%s/remote-ssh/expected-tools\n' "$config_home"
}

expected_tools_exists() {
  [[ -f "$(expected_tools_file)" ]]
}

read_expected_tools() {
  local file line tool

  file="$(expected_tools_file)"
  [[ -r "$file" ]] || return 1

  while IFS= read -r line || [[ -n "$line" ]]; do
    tool="$(trim_tool_line "$line")"
    [[ -n "$tool" ]] && printf '%s\n' "$tool"
  done <"$file"
}

write_expected_tools() {
  local file tmp tool
  local -a tools=("$@")

  file="$(expected_tools_file)"
  mkdir -p "${file%/*}"
  tmp="${file}.$$"

  {
    printf '# remote-ssh expected tools\n'
    printf '# One tool per line. Blank lines and # comments are ignored.\n'
    for tool in "${tools[@]}"; do
      printf '%s\n' "$tool"
    done
  } >"$tmp" && mv "$tmp" "$file"
}
