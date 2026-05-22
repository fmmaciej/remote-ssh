# helm-chart-diff

`helm-chart-diff` compares a Helm chart package pulled from an OCI registry
with a chart directory from either the local filesystem or GitHub.

The helper is intentionally small. It shells out to `helm pull`, extracts the
downloaded chart package, then runs `diff -ruN` against the selected chart
directory. It does not interpret `.helmignore`; the comparison is package
contents versus raw directory contents.

## Usage

Compare against a local chart directory:

```bash
helm-chart-diff \
  --oci oci://registry-1.docker.io/<namespace>/<chart> \
  --version <chart-version> \
  --local-chart ./charts/<chart>
```

Compare against a chart directory from GitHub:

```bash
helm-chart-diff \
  --oci oci://registry-1.docker.io/<namespace>/<chart> \
  --version <chart-version> \
  --github-chart owner/repo:charts/<chart> \
  --ref <tag-or-sha-or-branch>
```

For private GitHub repositories, export `GITHUB_TOKEN` before running the
helper:

```bash
export GITHUB_TOKEN=<token>
```

## Requirements

- `helm`
- `curl` for `--github-chart`
- `tar`
- `find`
- `diff`

Remote-ssh does not install or manage `helm`; provide it on the host before
using `helm-chart-diff`.

## Exit Codes

```text
0    chart contents are the same
1    chart contents differ
2    pull, download, extraction, or chart path error
64   usage error
127  helm or another required command is missing
```
