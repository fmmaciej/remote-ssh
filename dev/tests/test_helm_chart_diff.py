from __future__ import annotations

import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path

from conftest import IsolatedEnv, assert_failed, assert_ok, run_cmd, write_executable


def run_helm_chart_diff(
    repo_dir: Path,
    args: Sequence[str],
    *,
    env: Mapping[str, str],
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    return run_cmd(["bash", repo_dir / "bin" / "helm-chart-diff", *args], cwd=cwd, env=env)


def run_helm_chart_diff_script(
    repo_dir: Path,
    args: Sequence[str],
    *,
    env: Mapping[str, str],
) -> subprocess.CompletedProcess[str]:
    return run_cmd(["/bin/bash", repo_dir / "scripts" / "helm_chart_diff.sh", *args], env=env)


def write_chart(path: Path, files: Mapping[str, str]) -> None:
    for relative_path, content in files.items():
        file_path = path / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")


def write_fake_helm(bin_dir: Path) -> None:
    write_executable(
        bin_dir / "helm",
        r"""
        #!/usr/bin/env bash

        if [[ "${1:-}" != "pull" ]]; then
          printf 'unexpected helm args: %s\n' "$*" >&2
          exit 99
        fi

        shift
        destination=""
        version="0.0.0"

        while (($# > 0)); do
          case "$1" in
            --destination)
              destination="$2"
              shift 2
              ;;
            --version)
              version="$2"
              shift 2
              ;;
            *)
              shift
              ;;
          esac
        done

        mkdir -p "$destination"
        tar -czf "$destination/${FAKE_OCI_NAME}-${version}.tgz" \
          -C "$FAKE_OCI_PARENT" \
          "$FAKE_OCI_NAME"
        """,
    )


def write_fake_curl(bin_dir: Path) -> None:
    write_executable(
        bin_dir / "curl",
        r"""
        #!/usr/bin/env bash

        if [[ -n "${FAKE_CURL_LOG:-}" ]]; then
          printf '%s\n' "$*" >>"${FAKE_CURL_LOG}"
        fi

        output=""
        while (($# > 0)); do
          case "$1" in
            -o)
              output="$2"
              shift 2
              ;;
            *)
              shift
              ;;
          esac
        done

        if [[ -z "$output" ]]; then
          printf 'missing curl -o target\n' >&2
          exit 99
        fi

        tar -czf "$output" -C "$FAKE_GITHUB_PARENT" "$FAKE_GITHUB_NAME"
        """,
    )


def chart_files(*, value: str = "one") -> dict[str, str]:
    return {
        "Chart.yaml": "apiVersion: v2\nname: app\nversion: 1.2.3\n",
        "values.yaml": f"value: {value}\n",
        "templates/deployment.yaml": "kind: Deployment\n",
    }


def test_helm_chart_diff_help(repo_dir: Path, isolated_env: IsolatedEnv) -> None:
    result = run_helm_chart_diff(repo_dir, ["--help"], env=isolated_env.env)

    assert_ok(result)
    assert "Usage:" in result.stdout
    assert "--local-chart <path>" in result.stdout
    assert "--github-chart <owner/repo:path>" in result.stdout
    assert "--raw" in result.stdout


def test_helm_chart_diff_requires_source(repo_dir: Path, isolated_env: IsolatedEnv) -> None:
    result = run_helm_chart_diff(
        repo_dir,
        ["--oci", "oci://registry-1.docker.io/owner/app", "--version", "1.2.3"],
        env=isolated_env.env,
    )

    assert_failed(result)
    assert result.returncode == 64
    assert "one of --local-chart or --github-chart is required" in result.stderr


def test_helm_chart_diff_rejects_multiple_sources(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    result = run_helm_chart_diff(
        repo_dir,
        [
            "--oci",
            "oci://registry-1.docker.io/owner/app",
            "--version",
            "1.2.3",
            "--local-chart",
            "charts/app",
            "--github-chart",
            "owner/repo:charts/app",
            "--ref",
            "v1.2.3",
        ],
        env=isolated_env.env,
    )

    assert_failed(result)
    assert result.returncode == 64
    assert "use exactly one of --local-chart or --github-chart" in result.stderr


def test_helm_chart_diff_requires_ref_with_github_chart(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    result = run_helm_chart_diff(
        repo_dir,
        [
            "--oci",
            "oci://registry-1.docker.io/owner/app",
            "--version",
            "1.2.3",
            "--github-chart",
            "owner/repo:charts/app",
        ],
        env=isolated_env.env,
    )

    assert_failed(result)
    assert result.returncode == 64
    assert "--ref is required with --github-chart" in result.stderr


def test_helm_chart_diff_local_chart_passes_when_contents_match(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    tmp_path: Path,
) -> None:
    oci_parent = tmp_path / "oci-parent"
    oci_chart = oci_parent / "app"
    local_chart = tmp_path / "local-chart"
    write_chart(oci_chart, chart_files())
    write_chart(local_chart, chart_files())
    write_fake_helm(isolated_env.bin_dir)

    env = isolated_env.env | {
        "FAKE_OCI_PARENT": str(oci_parent),
        "FAKE_OCI_NAME": "app",
    }
    result = run_helm_chart_diff(
        repo_dir,
        [
            "--oci",
            "oci://registry-1.docker.io/owner/app",
            "--version",
            "1.2.3",
            "--local-chart",
            str(local_chart),
        ],
        env=env,
    )

    assert_ok(result)
    assert "Commands\n" in result.stdout
    assert (
        'helm pull oci://registry-1.docker.io/owner/app --version 1.2.3 '
        '--destination "$tmp/oci-pull"'
    ) in result.stdout
    assert "diff -ruN --exclude '.git' --exclude '.DS_Store'" in result.stdout
    assert str(local_chart) in result.stdout
    assert "Normalized mode filters YAML files before diffing" in result.stdout
    assert "file='values.yaml'" in result.stdout
    assert f'cat {local_chart}/"$file" | sed ' in result.stdout
    assert 'cat "$(find "$tmp/oci-extract" -mindepth 1 -maxdepth 1 -type d)"/"$file" | sed ' in (
        result.stdout
    )
    assert "LC_ALL=C sort" in result.stdout
    assert "Normalized diff" in result.stdout
    assert "OK: normalized chart contents are the same" in result.stdout


def test_helm_chart_diff_normalized_yaml_ignores_order_and_comments(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    tmp_path: Path,
) -> None:
    oci_parent = tmp_path / "oci-parent"
    oci_chart = oci_parent / "app"
    local_chart = tmp_path / "local-chart"
    write_chart(
        oci_chart,
        {
            "Chart.yaml": "name: app\n# chart comment\napiVersion: v2\nversion: 1.2.3\n",
            "values.yaml": "# heading\nb: 2\na: 1 # inline comment\n",
        },
    )
    write_chart(
        local_chart,
        {
            "Chart.yaml": "version: 1.2.3\napiVersion: v2\nname: app\n",
            "values.yaml": "a: 1\n# local heading\nb: 2\n",
        },
    )
    write_fake_helm(isolated_env.bin_dir)

    env = isolated_env.env | {
        "FAKE_OCI_PARENT": str(oci_parent),
        "FAKE_OCI_NAME": "app",
    }
    result = run_helm_chart_diff(
        repo_dir,
        [
            "--oci",
            "oci://registry-1.docker.io/owner/app",
            "--version",
            "1.2.3",
            "--local-chart",
            str(local_chart),
        ],
        env=env,
    )

    assert_ok(result)
    assert "OK: normalized chart contents are the same" in result.stdout


def test_helm_chart_diff_normalized_yaml_reports_value_differences_without_comments(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    tmp_path: Path,
) -> None:
    oci_parent = tmp_path / "oci-parent"
    oci_chart = oci_parent / "app"
    local_chart = tmp_path / "local-chart"
    write_chart(oci_chart, chart_files(value="oci # hidden"))
    write_chart(local_chart, chart_files(value="local # hidden"))
    write_fake_helm(isolated_env.bin_dir)

    env = isolated_env.env | {
        "FAKE_OCI_PARENT": str(oci_parent),
        "FAKE_OCI_NAME": "app",
    }
    result = run_helm_chart_diff(
        repo_dir,
        [
            "--oci",
            "oci://registry-1.docker.io/owner/app",
            "--version",
            "1.2.3",
            "--local-chart",
            str(local_chart),
        ],
        env=env,
    )

    assert_failed(result)
    assert result.returncode == 1
    assert "Normalized diff" in result.stdout
    assert "values.yaml" in result.stdout
    assert "value: local" in result.stdout
    assert "value: oci" in result.stdout
    assert "hidden" not in result.stdout


def test_helm_chart_diff_raw_mode_reports_order_and_comment_differences(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    tmp_path: Path,
) -> None:
    oci_parent = tmp_path / "oci-parent"
    oci_chart = oci_parent / "app"
    local_chart = tmp_path / "local-chart"
    write_chart(
        oci_chart,
        {
            "Chart.yaml": "name: app\napiVersion: v2\nversion: 1.2.3\n",
            "values.yaml": "# oci comment\nb: 2\na: 1\n",
        },
    )
    write_chart(
        local_chart,
        {
            "Chart.yaml": "version: 1.2.3\napiVersion: v2\nname: app\n",
            "values.yaml": "a: 1\n# local comment\nb: 2\n",
        },
    )
    write_fake_helm(isolated_env.bin_dir)

    env = isolated_env.env | {
        "FAKE_OCI_PARENT": str(oci_parent),
        "FAKE_OCI_NAME": "app",
    }
    result = run_helm_chart_diff(
        repo_dir,
        [
            "--raw",
            "--oci",
            "oci://registry-1.docker.io/owner/app",
            "--version",
            "1.2.3",
            "--local-chart",
            str(local_chart),
        ],
        env=env,
    )

    assert_failed(result)
    assert result.returncode == 1
    assert "\nDiff\n" in result.stdout
    assert "Normalized diff" not in result.stdout
    assert "# local comment" in result.stdout
    assert "# oci comment" in result.stdout


def test_helm_chart_diff_non_yaml_files_remain_raw_in_normalized_mode(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    tmp_path: Path,
) -> None:
    oci_parent = tmp_path / "oci-parent"
    oci_chart = oci_parent / "app"
    local_chart = tmp_path / "local-chart"
    write_chart(oci_chart, chart_files() | {"README.txt": "second\nfirst\n"})
    write_chart(local_chart, chart_files() | {"README.txt": "first\nsecond\n"})
    write_fake_helm(isolated_env.bin_dir)

    env = isolated_env.env | {
        "FAKE_OCI_PARENT": str(oci_parent),
        "FAKE_OCI_NAME": "app",
    }
    result = run_helm_chart_diff(
        repo_dir,
        [
            "--oci",
            "oci://registry-1.docker.io/owner/app",
            "--version",
            "1.2.3",
            "--local-chart",
            str(local_chart),
        ],
        env=env,
    )

    assert_failed(result)
    assert result.returncode == 1
    assert "README.txt" in result.stdout
    assert "first" in result.stdout
    assert "second" in result.stdout


def test_helm_chart_diff_local_chart_accepts_chart_yaml_file(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    tmp_path: Path,
) -> None:
    oci_parent = tmp_path / "oci-parent"
    oci_chart = oci_parent / "app"
    local_chart = tmp_path / "local-chart"
    write_chart(oci_chart, chart_files())
    write_chart(local_chart, chart_files())
    write_fake_helm(isolated_env.bin_dir)

    env = isolated_env.env | {
        "FAKE_OCI_PARENT": str(oci_parent),
        "FAKE_OCI_NAME": "app",
    }
    result = run_helm_chart_diff(
        repo_dir,
        [
            "--oci",
            "oci://registry-1.docker.io/owner/app",
            "--version",
            "1.2.3",
            "--local-chart",
            str(local_chart / "Chart.yaml"),
        ],
        env=env,
    )

    assert_ok(result)
    assert f"Source chart: {local_chart}" in result.stdout


def test_helm_chart_diff_local_chart_expands_home(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    tmp_path: Path,
) -> None:
    oci_parent = tmp_path / "oci-parent"
    oci_chart = oci_parent / "app"
    local_chart = isolated_env.home / "charts" / "app"
    write_chart(oci_chart, chart_files())
    write_chart(local_chart, chart_files())
    write_fake_helm(isolated_env.bin_dir)

    env = isolated_env.env | {
        "FAKE_OCI_PARENT": str(oci_parent),
        "FAKE_OCI_NAME": "app",
    }
    result = run_helm_chart_diff(
        repo_dir,
        [
            "--oci",
            "oci://registry-1.docker.io/owner/app",
            "--version",
            "1.2.3",
            "--local-chart",
            "~/charts/app",
        ],
        env=env,
    )

    assert_ok(result)
    assert f"Source chart: {local_chart}" in result.stdout


def test_helm_chart_diff_local_chart_reports_existing_non_chart_path(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    tmp_path: Path,
) -> None:
    oci_parent = tmp_path / "oci-parent"
    oci_chart = oci_parent / "app"
    local_file = tmp_path / "not-a-chart.txt"
    write_chart(oci_chart, chart_files())
    local_file.write_text("not a chart\n", encoding="utf-8")
    write_fake_helm(isolated_env.bin_dir)

    env = isolated_env.env | {
        "FAKE_OCI_PARENT": str(oci_parent),
        "FAKE_OCI_NAME": "app",
    }
    result = run_helm_chart_diff(
        repo_dir,
        [
            "--oci",
            "oci://registry-1.docker.io/owner/app",
            "--version",
            "1.2.3",
            "--local-chart",
            str(local_file),
        ],
        env=env,
    )

    assert_failed(result)
    assert result.returncode == 2
    assert "exists but is not a chart directory" in result.stderr
    assert "pass the chart directory, or its Chart.yaml file" in result.stderr


def test_helm_chart_diff_local_chart_missing_path_reports_cwd(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    result = run_helm_chart_diff(
        repo_dir,
        [
            "--oci",
            "oci://registry-1.docker.io/owner/app",
            "--version",
            "1.2.3",
            "--local-chart",
            "missing-chart",
        ],
        env=isolated_env.env,
    )

    assert_failed(result)
    assert result.returncode == 2
    assert "local chart directory does not exist: missing-chart" in result.stderr
    assert "current directory:" in result.stderr


def test_helm_chart_diff_github_chart_passes_with_fake_curl(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    tmp_path: Path,
) -> None:
    oci_parent = tmp_path / "oci-parent"
    oci_chart = oci_parent / "app"
    github_parent = tmp_path / "github-parent"
    github_repo = github_parent / "repo-root"
    github_chart = github_repo / "charts" / "app"
    write_chart(oci_chart, chart_files())
    write_chart(github_chart, chart_files())
    write_fake_helm(isolated_env.bin_dir)
    write_fake_curl(isolated_env.bin_dir)

    env = isolated_env.env | {
        "FAKE_OCI_PARENT": str(oci_parent),
        "FAKE_OCI_NAME": "app",
        "FAKE_GITHUB_PARENT": str(github_parent),
        "FAKE_GITHUB_NAME": "repo-root",
    }
    result = run_helm_chart_diff(
        repo_dir,
        [
            "--oci",
            "oci://registry-1.docker.io/owner/app",
            "--version",
            "1.2.3",
            "--github-chart",
            "owner/repo:charts/app",
            "--ref",
            "v1.2.3",
        ],
        env=env,
    )

    assert_ok(result)
    assert "Commands\n" in result.stdout
    assert "curl -L -fsS https://api.github.com/repos/owner/repo/tarball/v1.2.3" in (
        result.stdout
    )
    assert '"$(find "$tmp/github-extract" -mindepth 1 -maxdepth 1 -type d)/charts/app"' in (
        result.stdout
    )
    assert "file='values.yaml'" in result.stdout
    assert (
        'cat "$(find "$tmp/github-extract" -mindepth 1 -maxdepth 1 -type d)/charts/app"/"$file" | sed '
        in result.stdout
    )
    assert 'cat "$(find "$tmp/oci-extract" -mindepth 1 -maxdepth 1 -type d)"/"$file" | sed ' in (
        result.stdout
    )
    assert "LC_ALL=C sort" in result.stdout
    assert "OK: normalized chart contents are the same" in result.stdout


def test_helm_chart_diff_github_chart_uses_github_token(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    tmp_path: Path,
) -> None:
    oci_parent = tmp_path / "oci-parent"
    oci_chart = oci_parent / "app"
    github_parent = tmp_path / "github-parent"
    github_repo = github_parent / "repo-root"
    github_chart = github_repo / "charts" / "app"
    curl_log = tmp_path / "curl.log"
    write_chart(oci_chart, chart_files())
    write_chart(github_chart, chart_files())
    write_fake_helm(isolated_env.bin_dir)
    write_fake_curl(isolated_env.bin_dir)

    env = isolated_env.env | {
        "FAKE_OCI_PARENT": str(oci_parent),
        "FAKE_OCI_NAME": "app",
        "FAKE_GITHUB_PARENT": str(github_parent),
        "FAKE_GITHUB_NAME": "repo-root",
        "FAKE_CURL_LOG": str(curl_log),
        "GITHUB_TOKEN": "secret-token",
    }
    result = run_helm_chart_diff(
        repo_dir,
        [
            "--oci",
            "oci://registry-1.docker.io/owner/app",
            "--version",
            "1.2.3",
            "--github-chart",
            "owner/repo:charts/app",
            "--ref",
            "v1.2.3",
        ],
        env=env,
    )

    assert_ok(result)
    assert "secret-token" not in result.stdout
    assert 'curl -L -fsS -H "Authorization: Bearer ${GITHUB_TOKEN}"' in result.stdout
    assert "Authorization: Bearer secret-token" in curl_log.read_text(encoding="utf-8")


def test_helm_chart_diff_reports_missing_github_chart_dir(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    tmp_path: Path,
) -> None:
    oci_parent = tmp_path / "oci-parent"
    oci_chart = oci_parent / "app"
    github_parent = tmp_path / "github-parent"
    github_repo = github_parent / "repo-root"
    write_chart(oci_chart, chart_files())
    write_chart(github_repo / "other", chart_files())
    write_fake_helm(isolated_env.bin_dir)
    write_fake_curl(isolated_env.bin_dir)

    env = isolated_env.env | {
        "FAKE_OCI_PARENT": str(oci_parent),
        "FAKE_OCI_NAME": "app",
        "FAKE_GITHUB_PARENT": str(github_parent),
        "FAKE_GITHUB_NAME": "repo-root",
    }
    result = run_helm_chart_diff(
        repo_dir,
        [
            "--oci",
            "oci://registry-1.docker.io/owner/app",
            "--version",
            "1.2.3",
            "--github-chart",
            "owner/repo:charts/app",
            "--ref",
            "v1.2.3",
        ],
        env=env,
    )

    assert_failed(result)
    assert result.returncode == 2
    assert "GitHub chart directory does not exist: charts/app" in result.stderr


def test_helm_chart_diff_missing_helm_returns_127(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    tmp_path: Path,
) -> None:
    local_chart = tmp_path / "local-chart"
    write_chart(local_chart, chart_files())
    env = isolated_env.env | {"PATH": str(isolated_env.bin_dir)}

    result = run_helm_chart_diff_script(
        repo_dir,
        [
            "--oci",
            "oci://registry-1.docker.io/owner/app",
            "--version",
            "1.2.3",
            "--local-chart",
            str(local_chart),
        ],
        env=env,
    )

    assert_failed(result)
    assert result.returncode == 127
    assert "helm is required" in result.stderr
