#!/usr/bin/env bash

set -euo pipefail

HELM_CHART_DIFF_TMP=""

helm_chart_diff_usage() {
  cat <<'EOF'
Usage:
  helm-chart-diff --oci <oci-chart> --version <version> --local-chart <path>
  helm-chart-diff --oci <oci-chart> --version <version> --github-chart <owner/repo:path> --ref <ref>

Compare a Helm chart package pulled from an OCI registry with a local chart
directory or a chart directory from a GitHub repository tarball.

Options:
  --oci <oci-chart>              OCI chart reference, for example oci://registry-1.docker.io/org/chart
  --version <version>            Chart version to pull with helm
  --local-chart <path>           Local chart directory to compare
  --github-chart <owner/repo:path>
                                 GitHub repository and chart path inside it
  --ref <ref>                    GitHub branch, tag, or commit for --github-chart
  -h, --help                     Show this help

Set GITHUB_TOKEN to access private GitHub repositories.
EOF
}

helm_chart_diff_require_command() {
  local command="$1"

  if ! command -v "$command" >/dev/null 2>&1; then
    printf 'helm-chart-diff: %s is required.\n' "$command" >&2
    return 127
  fi
}

helm_chart_diff_find_one() {
  local dir="$1" pattern="$2"
  local found="" count=0 path

  while IFS= read -r path; do
    found="$path"
    count=$((count + 1))
  done < <(find "$dir" -maxdepth 1 -name "$pattern" -type f)

  if ((count != 1)); then
    return 1
  fi

  printf '%s\n' "$found"
}

helm_chart_diff_find_one_dir() {
  local dir="$1"
  local found="" count=0 path

  while IFS= read -r path; do
    found="$path"
    count=$((count + 1))
  done < <(find "$dir" -mindepth 1 -maxdepth 1 -type d)

  if ((count != 1)); then
    return 1
  fi

  printf '%s\n' "$found"
}

helm_chart_diff_parse_github_chart() {
  local spec="$1"

  GITHUB_CHART_REPO="${spec%%:*}"
  GITHUB_CHART_PATH="${spec#*:}"

  if [[ "$spec" != *:* || -z "$GITHUB_CHART_REPO" || -z "$GITHUB_CHART_PATH" ]]; then
    return 1
  fi
  if [[ "$GITHUB_CHART_REPO" != */* || "$GITHUB_CHART_REPO" == */*/* ]]; then
    return 1
  fi
  if [[ "$GITHUB_CHART_PATH" == /* ]]; then
    return 1
  fi
}

helm_chart_diff_expand_local_path() {
  local path="$1"

  case "$path" in
    \~)
      printf '%s\n' "$HOME"
      ;;
    \~/*)
      printf '%s/%s\n' "$HOME" "${path:2}"
      ;;
    *)
      printf '%s\n' "$path"
      ;;
  esac
}

helm_chart_diff_resolve_local_chart() {
  local input_path="$1"
  local expanded_path

  expanded_path="$(helm_chart_diff_expand_local_path "$input_path")"

  if [[ -d "$expanded_path" ]]; then
    printf '%s\n' "$expanded_path"
    return 0
  fi

  if [[ -f "$expanded_path" && "${expanded_path##*/}" == "Chart.yaml" ]]; then
    local chart_dir="."
    if [[ "$expanded_path" == */* ]]; then
      chart_dir="${expanded_path%/*}"
      [[ -n "$chart_dir" ]] || chart_dir="/"
    fi
    printf '%s\n' "$chart_dir"
    return 0
  fi

  if [[ -e "$expanded_path" ]]; then
    printf 'helm-chart-diff: local chart path exists but is not a chart directory: %s\n' "$input_path" >&2
    printf 'helm-chart-diff: pass the chart directory, or its Chart.yaml file.\n' >&2
    return 2
  fi

  printf 'helm-chart-diff: local chart directory does not exist: %s\n' "$input_path" >&2
  if [[ "$expanded_path" != "$input_path" ]]; then
    printf 'helm-chart-diff: expanded path: %s\n' "$expanded_path" >&2
  fi
  printf 'helm-chart-diff: current directory: %s\n' "$PWD" >&2
  return 2
}

helm_chart_diff_pull_oci() {
  local oci="$1" version="$2" tmp="$3"
  local pull_dir="$tmp/oci-pull"
  local extract_dir="$tmp/oci-extract"
  local package chart_root helm_output

  mkdir -p "$pull_dir" "$extract_dir"

  if ! helm_output="$(helm pull "$oci" --version "$version" --destination "$pull_dir" 2>&1)"; then
    printf 'helm-chart-diff: helm pull failed.\n' >&2
    [[ -n "$helm_output" ]] && printf '%s\n' "$helm_output" >&2
    return 2
  fi

  if ! package="$(helm_chart_diff_find_one "$pull_dir" '*.tgz')"; then
    printf 'helm-chart-diff: expected exactly one .tgz from helm pull.\n' >&2
    return 2
  fi

  if ! tar -xzf "$package" -C "$extract_dir"; then
    printf 'helm-chart-diff: failed to extract OCI chart package: %s\n' "$package" >&2
    return 2
  fi

  if ! chart_root="$(helm_chart_diff_find_one_dir "$extract_dir")"; then
    printf 'helm-chart-diff: expected exactly one chart directory in OCI package.\n' >&2
    return 2
  fi

  printf '%s\n' "$chart_root"
}

helm_chart_diff_fetch_github_chart() {
  local spec="$1" ref="$2" tmp="$3"
  local tarball="$tmp/github.tar.gz"
  local extract_dir="$tmp/github-extract"
  local repo_root chart_dir url curl_output
  local -a curl_args=(-L -fsS)

  GITHUB_CHART_REPO=""
  GITHUB_CHART_PATH=""
  if ! helm_chart_diff_parse_github_chart "$spec"; then
    printf 'helm-chart-diff: unsupported --github-chart format: %s\n' "$spec" >&2
    printf 'helm-chart-diff: expected owner/repo:path/to/chart.\n' >&2
    return 64
  fi

  mkdir -p "$extract_dir"
  url="https://api.github.com/repos/${GITHUB_CHART_REPO}/tarball/${ref}"

  if [[ -n "${GITHUB_TOKEN:-}" ]]; then
    curl_args+=(-H "Authorization: Bearer ${GITHUB_TOKEN}")
  fi

  if ! curl_output="$(curl "${curl_args[@]}" "$url" -o "$tarball" 2>&1)"; then
    printf 'helm-chart-diff: failed to download GitHub chart archive.\n' >&2
    [[ -n "$curl_output" ]] && printf '%s\n' "$curl_output" >&2
    return 2
  fi

  if ! tar -xzf "$tarball" -C "$extract_dir"; then
    printf 'helm-chart-diff: failed to extract GitHub chart archive.\n' >&2
    return 2
  fi

  if ! repo_root="$(helm_chart_diff_find_one_dir "$extract_dir")"; then
    printf 'helm-chart-diff: expected exactly one top-level directory in GitHub archive.\n' >&2
    return 2
  fi

  chart_dir="$repo_root/$GITHUB_CHART_PATH"
  if [[ ! -d "$chart_dir" ]]; then
    printf 'helm-chart-diff: GitHub chart directory does not exist: %s\n' "$GITHUB_CHART_PATH" >&2
    return 2
  fi

  printf '%s\n' "$chart_dir"
}

helm_chart_diff_main() {
  local oci="" version="" local_chart="" github_chart="" ref=""
  local arg

  while (($# > 0)); do
    arg="$1"
    case "$arg" in
      --oci)
        (($# >= 2)) || {
          printf 'helm-chart-diff: --oci requires a value\n' >&2
          return 64
        }
        oci="$2"
        shift 2
        ;;
      --version)
        (($# >= 2)) || {
          printf 'helm-chart-diff: --version requires a value\n' >&2
          return 64
        }
        version="$2"
        shift 2
        ;;
      --local-chart)
        (($# >= 2)) || {
          printf 'helm-chart-diff: --local-chart requires a path\n' >&2
          return 64
        }
        local_chart="$2"
        shift 2
        ;;
      --github-chart)
        (($# >= 2)) || {
          printf 'helm-chart-diff: --github-chart requires owner/repo:path\n' >&2
          return 64
        }
        github_chart="$2"
        shift 2
        ;;
      --ref)
        (($# >= 2)) || {
          printf 'helm-chart-diff: --ref requires a value\n' >&2
          return 64
        }
        ref="$2"
        shift 2
        ;;
      -h | --help)
        helm_chart_diff_usage
        return 0
        ;;
      -*)
        printf 'helm-chart-diff: unknown option: %s\n' "$arg" >&2
        helm_chart_diff_usage >&2
        return 64
        ;;
      *)
        printf 'helm-chart-diff: unexpected argument: %s\n' "$arg" >&2
        helm_chart_diff_usage >&2
        return 64
        ;;
    esac
  done

  if [[ -z "$oci" || -z "$version" ]]; then
    helm_chart_diff_usage >&2
    return 64
  fi
  if [[ -n "$local_chart" && -n "$github_chart" ]]; then
    printf 'helm-chart-diff: use exactly one of --local-chart or --github-chart\n' >&2
    return 64
  fi
  if [[ -z "$local_chart" && -z "$github_chart" ]]; then
    printf 'helm-chart-diff: one of --local-chart or --github-chart is required\n' >&2
    return 64
  fi
  if [[ -n "$github_chart" && -z "$ref" ]]; then
    printf 'helm-chart-diff: --ref is required with --github-chart\n' >&2
    return 64
  fi
  if [[ -n "$local_chart" && -n "$ref" ]]; then
    printf 'helm-chart-diff: --ref is only valid with --github-chart\n' >&2
    return 64
  fi

  local source_chart=""
  if [[ -n "$local_chart" ]]; then
    if source_chart="$(helm_chart_diff_resolve_local_chart "$local_chart")"; then
      :
    else
      return $?
    fi
  fi

  helm_chart_diff_require_command helm || return 127
  helm_chart_diff_require_command tar || return 127
  helm_chart_diff_require_command find || return 127
  helm_chart_diff_require_command diff || return 127
  if [[ -n "$github_chart" ]]; then
    helm_chart_diff_require_command curl || return 127
  fi

  local tmp oci_chart diff_status
  tmp="$(mktemp -d)"
  HELM_CHART_DIFF_TMP="$tmp"
  trap 'rm -rf "$HELM_CHART_DIFF_TMP"' EXIT

  if oci_chart="$(helm_chart_diff_pull_oci "$oci" "$version" "$tmp")"; then
    :
  else
    return $?
  fi

  if [[ -n "$github_chart" ]]; then
    if source_chart="$(helm_chart_diff_fetch_github_chart "$github_chart" "$ref" "$tmp")"; then
      :
    else
      return $?
    fi
  fi

  printf 'helm-chart-diff\n\n'
  printf 'OCI chart:    %s @ %s\n' "$oci" "$version"
  printf 'Source chart: %s\n\n' "$source_chart"

  if diff -ruN --exclude '.git' --exclude '.DS_Store' "$source_chart" "$oci_chart"; then
    printf 'OK: chart contents are the same\n'
    return 0
  else
    diff_status=$?
  fi

  if ((diff_status == 1)); then
    return 1
  fi

  printf 'helm-chart-diff: diff failed.\n' >&2
  return 2
}

helm_chart_diff_main "$@"
