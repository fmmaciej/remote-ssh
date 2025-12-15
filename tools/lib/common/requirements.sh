# shellcheck shell=bash

ensure_this_file_sourced

# ustawia globalnie ZIP_SUPPORTED=0/1 (to jest OK jako "capability")
check_req_tools() {
  local required=(curl grep sed find tar uname mktemp)
  local missing=()

  for cmd in "${required[@]}"; do
    have "$cmd" || missing+=("$cmd")
  done

  if have unzip; then
    ZIP_SUPPORTED=1;
  else
    # shellcheck disable=SC2034
    ZIP_SUPPORTED=0;
  fi

  if ((${#missing[@]} > 0)); then
    printf 'Missing required tools:\n' >&2
    printf '  - %s\n' "${missing[@]}" >&2

    return 1
  fi

  return 0
}
