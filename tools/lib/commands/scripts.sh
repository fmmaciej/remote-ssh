# shellcheck shell=bash

ensure_this_file_sourced

remote_ssh_cmd_scripts_usage() {
  cat <<'EOF'
Usage:
  remote-ssh scripts --list
  remote-ssh scripts list

For helper details:
  remote-ssh guide scripts [helper]
EOF
}

remote_ssh_cmd_scripts_guide_usage() {
  cat <<'EOF'
Usage:
  remote-ssh guide scripts [helper]

Helpers:
  ci-run
  helm-chart-diff
  ssh-pick
EOF
}

remote_ssh_cmd_scripts_entries() {
  cat <<'EOF'
ci-run|command|gh|Inspect GitHub Actions jobs and print log commands.|ci-run status <run-id> <app-filter> [--repo owner/repo] [--attempt n] [--all]|bin/ci-run|scripts/ci_run.sh|docs/ci-run.md|one workflow run contains several app-specific job variants.
helm-chart-diff|command|helm|Compare an OCI Helm chart package with a local or GitHub chart directory.|helm-chart-diff --oci <oci-chart> --version <version> --local-chart <path>|bin/helm-chart-diff|scripts/helm_chart_diff.sh|docs/helm-chart-diff.md|you need to compare packaged chart contents with source chart files.
ssh-pick|shell function|python3, fzf|Pick an SSH config host with fzf and connect with ssh.|ssh-pick [ssh-args...]|shell/rc.d/30-ssh-pick.sh|scripts/ssh_hosts.py|docs/shell/helpers.md#ssh-pick|you want an interactive host picker for entries in ~/.ssh/config.
EOF
}

remote_ssh_cmd_scripts_is_known() {
  local wanted="${1:?helper required}"
  local name

  while IFS='|' read -r name _rest; do
    [[ "$name" == "$wanted" ]] && return 0
  done < <(remote_ssh_cmd_scripts_entries)

  return 1
}

remote_ssh_cmd_scripts_print_list() {
  local name kind requirements purpose _entrypoint _backend _docs _use_when

  printf 'remote-ssh scripts\n\n'
  printf '  %-16s %-15s %-13s %s\n' "Name" "Kind" "Requires" "Purpose"
  printf '  %-16s %-15s %-13s %s\n' "----------------" "---------------" "-------------" "-------"

  while IFS='|' read -r name kind requirements purpose _entrypoint _backend _docs _use_when; do
    printf '  %-16s %-15s %-13s %s\n' "$name" "$kind" "$requirements" "$purpose"
  done < <(remote_ssh_cmd_scripts_entries)
}

remote_ssh_cmd_scripts_print_guide_entry() {
  local wanted="${1:-}"
  local name kind requirements purpose example entrypoint backend docs use_when

  while IFS='|' read -r name kind requirements purpose example entrypoint backend docs use_when; do
    [[ -n "$wanted" && "$name" != "$wanted" ]] && continue

    cat <<EOF
$name
  Use when: $use_when
  Run:
    $example
  Requires: $requirements
  Type: $kind
  Entry point: $entrypoint
  Backend: $backend
  Docs: $docs

EOF
  done < <(remote_ssh_cmd_scripts_entries)
}

remote_ssh_cmd_scripts_print_guide() {
  local helper="${1:-}"

  if [[ -n "$helper" ]] && ! remote_ssh_cmd_scripts_is_known "$helper"; then
    printf 'Unknown remote-ssh script helper: %s\n' "$helper" >&2
    remote_ssh_cmd_scripts_guide_usage >&2
    return 1
  fi

  printf 'Scripts\n'
  remote_ssh_cmd_scripts_print_guide_entry "$helper"
}

remote_ssh_cmd_scripts_main() {
  local subcommand="${1:-}"

  case "$subcommand" in
    ''|list|--list)
      [[ -z "$subcommand" ]] || shift
      (($# == 0)) || {
        remote_ssh_cmd_scripts_usage >&2
        return 1
      }
      remote_ssh_cmd_scripts_print_list
      ;;
    -h|--help)
      remote_ssh_cmd_scripts_usage
      ;;
    guide)
      printf 'remote-ssh scripts guide moved to remote-ssh guide scripts.\n' >&2
      printf 'Use: remote-ssh guide scripts [helper]\n' >&2
      return 1
      ;;
    *)
      printf 'Unknown remote-ssh scripts command: %s\n' "$subcommand" >&2
      remote_ssh_cmd_scripts_usage >&2
      return 1
      ;;
  esac
}
