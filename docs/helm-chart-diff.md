# helm-chart-diff

`helm-chart-diff` compares a Helm chart package pulled from an OCI registry
with a chart directory from either the local filesystem or GitHub.

The helper is intentionally small. It shells out to `helm pull`, extracts the
downloaded chart package, normalizes YAML files, then runs `diff -ruN` against
the normalized view. It does not interpret `.helmignore`; the comparison is
package contents versus raw directory contents after local normalization.

## Usage

Compare against a local chart directory:

```bash
helm-chart-diff \
  --oci oci://registry-1.docker.io/<namespace>/<chart> \
  --version <chart-version> \
  --local-chart ./charts/<chart>
```

`--local-chart` may point to the chart directory or to that directory's
`Chart.yaml` file. Relative paths are resolved from the current directory, and
`~/...` is expanded against `$HOME`.

By default, YAML files (`*.yaml` and `*.yml`) are compared through a text
normalizer that removes blank lines, full-line comments, simple inline comments
like `value # note`, and then sorts the remaining lines. Other files are
compared raw. This is not a YAML parser; quoted values that intentionally
contain ` #` can be affected by the inline-comment rule.

Use `--raw` to compare the chart directories exactly as extracted:

```bash
helm-chart-diff --raw \
  --oci oci://registry-1.docker.io/<namespace>/<chart> \
  --version <chart-version> \
  --local-chart ./charts/<chart>
```

Each run prints a `Commands` section with the equivalent `helm`, `curl`, `tar`,
`diff`, and paired `cat` commands needed to reproduce the check manually. In
normalized mode, the `cat` commands use a `file='values.yaml'` placeholder and
apply the same `sed | LC_ALL=C sort` filter to both copies. In `--raw` mode,
the printed `cat` commands show the files unchanged. When `GITHUB_TOKEN` is
set, the printed `curl` command references `${GITHUB_TOKEN}` instead of
printing the token value.

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
- `sed`, `sort`, and `cp` for normalized mode

Remote-ssh does not install or manage `helm`; provide it on the host before
using `helm-chart-diff`.

## Exit Codes

```text
0    chart contents are the same after the selected comparison mode
1    chart contents differ after the selected comparison mode
2    pull, download, extraction, or chart path error
64   usage error
127  helm or another required command is missing
```
