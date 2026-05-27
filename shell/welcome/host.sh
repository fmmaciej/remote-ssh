# shellcheck shell=bash

remote_ssh_welcome_host_ip_from_hostname() {
  local output ip

  output="$(hostname -I 2>/dev/null || true)"
  for ip in $output; do
    case "$ip" in
      127.* | ::1) continue ;;
      *) printf '%s\n' "$ip"; return 0 ;;
    esac
  done
  return 1
}

remote_ssh_welcome_host_ip_from_ip_route() {
  local word previous output

  command -v ip >/dev/null 2>&1 || return 1
  output="$(ip route get 1.1.1.1 2>/dev/null || true)"
  previous=""
  for word in $output; do
    if [[ "$previous" == "src" ]]; then
      printf '%s\n' "$word"
      return 0
    fi
    previous="$word"
  done
  return 1
}

remote_ssh_welcome_host_ip_from_ifconfig() {
  local ip

  command -v ifconfig >/dev/null 2>&1 || return 1
  while IFS= read -r ip; do
    case "$ip" in
      127.* | '') continue ;;
      *) printf '%s\n' "$ip"; return 0 ;;
    esac
  done < <(ifconfig 2>/dev/null | sed -n 's/.*inet \([0-9][0-9.]*\).*/\1/p')
  return 1
}

remote_ssh_welcome_host_ip() {
  remote_ssh_welcome_host_ip_from_hostname ||
    remote_ssh_welcome_host_ip_from_ip_route ||
    remote_ssh_welcome_host_ip_from_ifconfig ||
    printf 'unknown\n'
}

remote_ssh_welcome_print_host() {
  local host ip

  host="$(hostname -s 2>/dev/null || hostname 2>/dev/null || printf 'unknown')"
  ip="$(remote_ssh_welcome_host_ip)"
  printf 'host:    %s / %s\n' "${host:-unknown}" "$ip"
}
