#!/usr/bin/env bash

set -euo pipefail

ci_run_usage() {
  cat <<'EOF'
Usage:
  ci-run status <run-id> <app-filter> [--repo owner/repo] [--attempt n] [--all]

Commands:
  status  Show matching GitHub Actions jobs and suggested log commands

Options:
  --repo owner/repo  Fetch jobs from this repository
  --attempt n        Fetch jobs from this workflow run attempt
  --all              Print log commands for successful jobs too
  -h, --help         Show this help
EOF
}

ci_run_status_usage() {
  cat <<'EOF'
Usage:
  ci-run status <run-id> <app-filter> [--repo owner/repo] [--attempt n] [--all]

The app filter is a case-insensitive literal substring of the GitHub Actions
job name.
EOF
}

ci_run_shell_quote() {
  printf '%q' "$1"
}

ci_run_print_log_command() {
  local run_id="$1" repo="$2" attempt="$3" job_id="$4" log_flag="$5"

  printf '  gh run view '
  ci_run_shell_quote "$run_id"
  if [[ -n "$repo" ]]; then
    printf ' --repo '
    ci_run_shell_quote "$repo"
  fi
  if [[ -n "$attempt" ]]; then
    printf ' --attempt '
    ci_run_shell_quote "$attempt"
  fi
  printf ' --job '
  ci_run_shell_quote "$job_id"
  printf ' %s\n' "$log_flag"
}

ci_run_repo_from_git_remote() {
  local remote_url

  remote_url="$(git config --get remote.origin.url 2>/dev/null || true)"
  [[ -n "$remote_url" ]] || return 1

  case "$remote_url" in
    https://github.com/*/*.git)
      remote_url="${remote_url#https://github.com/}"
      printf '%s\n' "${remote_url%.git}"
      ;;
    https://github.com/*/*)
      remote_url="${remote_url#https://github.com/}"
      printf '%s\n' "${remote_url%.git}"
      ;;
    git@github.com:*/*.git)
      remote_url="${remote_url#git@github.com:}"
      printf '%s\n' "${remote_url%.git}"
      ;;
    git@github.com:*/*)
      remote_url="${remote_url#git@github.com:}"
      printf '%s\n' "${remote_url%.git}"
      ;;
    *)
      return 1
      ;;
  esac
}

ci_run_repo_api_path() {
  local repo="$1"

  repo="${repo#https://github.com/}"
  repo="${repo#git@github.com:}"
  repo="${repo%.git}"

  case "$repo" in
    github.com/*/*)
      repo="${repo#github.com/}"
      ;;
    */*/*)
      repo="${repo#*/}"
      ;;
  esac

  [[ "$repo" == */* && "$repo" != */*/* ]] || return 1
  printf '%s\n' "$repo"
}

ci_run_jobs_endpoint() {
  local repo_path="$1" run_id="$2" attempt="$3"

  if [[ -n "$attempt" ]]; then
    printf '/repos/%s/actions/runs/%s/attempts/%s/jobs?per_page=30\n' "$repo_path" "$run_id" "$attempt"
  else
    printf '/repos/%s/actions/runs/%s/jobs?per_page=30\n' "$repo_path" "$run_id"
  fi
}

ci_run_classify_job() {
  local status="$1" conclusion="$2"

  case "$conclusion" in
    success)
      printf 'pass\n'
      ;;
    failure | cancelled | timed_out | action_required | startup_failure)
      printf 'fail\n'
      ;;
    *)
      printf 'pending\n'
      ;;
  esac
}

ci_run_status_main() {
  local run_id="" app_filter="" repo="" attempt="" include_all_logs=0
  local arg

  while (($# > 0)); do
    arg="$1"
    case "$arg" in
      --repo)
        (($# >= 2)) || {
          printf 'ci-run: --repo requires owner/repo\n' >&2
          return 64
        }
        repo="$2"
        shift 2
        ;;
      --attempt)
        (($# >= 2)) || {
          printf 'ci-run: --attempt requires a value\n' >&2
          return 64
        }
        attempt="$2"
        shift 2
        ;;
      --all)
        include_all_logs=1
        shift
        ;;
      -h | --help)
        ci_run_status_usage
        return 0
        ;;
      -*)
        printf 'ci-run: unknown status option: %s\n' "$arg" >&2
        ci_run_status_usage >&2
        return 64
        ;;
      *)
        if [[ -z "$run_id" ]]; then
          run_id="$arg"
        elif [[ -z "$app_filter" ]]; then
          app_filter="$arg"
        else
          printf 'ci-run: unexpected argument: %s\n' "$arg" >&2
          ci_run_status_usage >&2
          return 64
        fi
        shift
        ;;
    esac
  done

  if [[ -z "$run_id" || -z "$app_filter" ]]; then
    ci_run_status_usage >&2
    return 64
  fi

  if ! command -v gh >/dev/null 2>&1; then
    printf 'ci-run: gh is required. Install GitHub CLI and authenticate it first.\n' >&2
    return 127
  fi

  if ! command -v grep >/dev/null 2>&1; then
    printf 'ci-run: grep is required.\n' >&2
    return 127
  fi

  local resolved_repo="$repo"
  if [[ -z "$resolved_repo" ]]; then
    if ! resolved_repo="$(ci_run_repo_from_git_remote)"; then
      printf 'ci-run: --repo owner/repo is required outside a github.com Git checkout.\n' >&2
      return 64
    fi
  fi

  local repo_path
  if ! repo_path="$(ci_run_repo_api_path "$resolved_repo")"; then
    printf 'ci-run: unsupported repo format: %s\n' "$resolved_repo" >&2
    printf 'ci-run: expected owner/repo or github.com/owner/repo.\n' >&2
    return 64
  fi

  local jq_filter
  jq_filter='.jobs[] | [(.conclusion // .status // "unknown"), (.status // "unknown"), (.conclusion // "unknown"), (.name // "unknown"), (.id // "unknown" | tostring)] | @tsv'

  local endpoint
  endpoint="$(ci_run_jobs_endpoint "$repo_path" "$run_id" "$attempt")"

  local gh_output
  if ! gh_output="$(gh api "$endpoint" --paginate --jq "$jq_filter" 2>&1)"; then
    printf 'ci-run: gh api failed while fetching workflow run jobs.\n' >&2
    [[ -n "$gh_output" ]] && printf '%s\n' "$gh_output" >&2
    return 3
  fi

  local result status conclusion name database_id class
  local matched=0 passed=0 failed=0 pending=0
  local -a match_results=() match_statuses=() match_conclusions=() match_names=() match_ids=() match_classes=()

  while IFS=$'\t' read -r result status conclusion name database_id; do
    [[ -n "$result$status$conclusion$name$database_id" ]] || continue

    if printf '%s\n' "$name" | grep -qiF -e "$app_filter"; then
      class="$(ci_run_classify_job "$status" "$conclusion")"
      match_results+=("${result:-unknown}")
      match_statuses+=("${status:-unknown}")
      match_conclusions+=("${conclusion:-unknown}")
      match_names+=("${name:-unknown}")
      match_ids+=("${database_id:-unknown}")
      match_classes+=("$class")

      matched=$((matched + 1))
      case "$class" in
        pass) passed=$((passed + 1)) ;;
        fail) failed=$((failed + 1)) ;;
        *) pending=$((pending + 1)) ;;
      esac
    fi
  done <<<"$gh_output"

  printf 'ci-run status\n\n'
  printf 'Run\n'
  printf '  id:      %s\n' "$run_id"
  printf '  repo:    %s\n' "$repo_path"
  [[ -n "$attempt" ]] && printf '  attempt: %s\n' "$attempt"
  printf '  filter:  %s\n' "$app_filter"

  printf '\nJobs\n'
  if ((matched == 0)); then
    printf '  [none]\n'
  else
    printf '  %-10s %-12s %-12s %-12s %-12s %s\n' \
      'class' 'result' 'status' 'conclusion' 'job-id' 'name'
    local i
    for ((i = 0; i < matched; i++)); do
      printf '  %-10s %-12s %-12s %-12s %-12s %s\n' \
        "${match_classes[$i]}" \
        "${match_results[$i]}" \
        "${match_statuses[$i]}" \
        "${match_conclusions[$i]}" \
        "${match_ids[$i]}" \
        "${match_names[$i]}"
    done
  fi

  printf '\nSummary\n'
  printf '  matched: %s\n' "$matched"
  printf '  passed:  %s\n' "$passed"
  printf '  failed:  %s\n' "$failed"
  printf '  pending: %s\n' "$pending"

  printf '\nLogs\n'
  if ((matched == 0)); then
    printf '  No matching jobs; no log commands to show.\n'
  else
    local printed_logs=0
    for ((i = 0; i < matched; i++)); do
      if ((include_all_logs == 0)) && [[ "${match_classes[$i]}" == "pass" ]]; then
        continue
      fi
      if [[ -z "${match_ids[$i]}" || "${match_ids[$i]}" == "null" || "${match_ids[$i]}" == "unknown" ]]; then
        continue
      fi

      printf '  # %s\n' "${match_names[$i]}"
      ci_run_print_log_command "$run_id" "$repo" "$attempt" "${match_ids[$i]}" "--log-failed"
      ci_run_print_log_command "$run_id" "$repo" "$attempt" "${match_ids[$i]}" "--log"
      printed_logs=$((printed_logs + 1))
    done

    if ((printed_logs == 0)); then
      printf '  All matched jobs passed. Re-run with --all to include log commands for successful jobs.\n'
    fi
  fi

  if ((matched == 0)); then
    return 2
  fi
  if ((failed > 0)); then
    return 1
  fi
  if ((pending > 0)); then
    return 2
  fi
  return 0
}

ci_run_main() {
  local command="${1:-}"

  case "$command" in
    '' | -h | --help)
      ci_run_usage
      ;;
    status)
      shift
      ci_run_status_main "$@"
      ;;
    *)
      printf 'ci-run: unknown command: %s\n' "$command" >&2
      ci_run_usage >&2
      return 64
      ;;
  esac
}

ci_run_main "$@"
