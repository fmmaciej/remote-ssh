# shellcheck shell=bash

remote_ssh_welcome_cpu_count() {
  local count

  if [[ -r /proc/cpuinfo ]]; then
    count="$(grep -c '^processor[[:space:]]*:' /proc/cpuinfo 2>/dev/null || true)"
    if [[ "$count" =~ ^[0-9]+$ && "$count" -gt 0 ]]; then
      printf '%s\n' "$count"
      return 0
    fi
  fi

  if command -v sysctl >/dev/null 2>&1; then
    count="$(sysctl -n hw.ncpu 2>/dev/null || true)"
    if [[ "$count" =~ ^[0-9]+$ && "$count" -gt 0 ]]; then
      printf '%s\n' "$count"
      return 0
    fi
  fi

  if command -v getconf >/dev/null 2>&1; then
    count="$(getconf _NPROCESSORS_ONLN 2>/dev/null || true)"
    if [[ "$count" =~ ^[0-9]+$ && "$count" -gt 0 ]]; then
      printf '%s\n' "$count"
      return 0
    fi
  fi

  printf 'unknown\n'
}

remote_ssh_welcome_ram_gib() {
  local key value _unit bytes gib

  if [[ -r /proc/meminfo ]]; then
    while read -r key value _unit; do
      if [[ "$key" == "MemTotal:" && "$value" =~ ^[0-9]+$ ]]; then
        gib=$((value / 1048576))
        ((gib > 0)) || gib=1
        printf '%s GiB\n' "$gib"
        return 0
      fi
    done </proc/meminfo
  fi

  if command -v sysctl >/dev/null 2>&1; then
    bytes="$(sysctl -n hw.memsize 2>/dev/null || true)"
    if [[ "$bytes" =~ ^[0-9]+$ && "$bytes" -gt 0 ]]; then
      gib=$((bytes / 1073741824))
      ((gib > 0)) || gib=1
      printf '%s GiB\n' "$gib"
      return 0
    fi
  fi

  printf 'unknown\n'
}

remote_ssh_welcome_print_hw() {
  local cpu ram

  cpu="$(remote_ssh_welcome_cpu_count)"
  ram="$(remote_ssh_welcome_ram_gib)"
  printf 'hw:      %s cpu / %s ram\n' "$cpu" "$ram"
}
