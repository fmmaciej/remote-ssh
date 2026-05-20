# ci-run

`ci-run` is a small GitHub Actions helper for checking app-specific jobs inside
one workflow run. It is useful when one run contains several variants of the
same app job.

The helper is a thin wrapper around GitHub CLI. Remote-ssh does not install or
manage `gh`; provide it on the host and authenticate it before using `ci-run`.

## Usage

```bash
ci-run status <run-id> <app-filter> [--repo owner/repo] [--attempt n] [--all]
```

Examples:

```bash
ci-run status 1234567890 <app>
ci-run status 1234567890 <app> --repo owner/repo
ci-run status 1234567890 <app> --repo owner/repo --attempt 2
ci-run status 1234567890 <app> --all
```

`<app-filter>` is a case-insensitive literal substring of the job name. It is
not a regular expression. For example, `<app>` matches:

```text
<app> | docker
<app> | helm
<app> smoke
```

## Output

`ci-run status` prints the matched jobs with:

- aggregate class: `pass`, `fail`, or `pending`
- GitHub result, status, and conclusion
- job database ID
- full job name

It also prints manual `gh` commands for job logs:

```bash
gh run view 1234567890 --job 987654321 --log-failed
gh run view 1234567890 --job 987654321 --log
```

By default, log commands are shown only for non-passing jobs. Use `--all` to
also print log commands for successful jobs.

## Exit Codes

```text
0    all matched jobs passed
1    at least one matched job failed, was cancelled, or timed out
2    jobs are still running, skipped, unknown, or no jobs matched
3    gh run view failed
64   usage error
127  gh or another required command is missing
```

## GitHub CLI

`ci-run` calls:

```bash
gh run view <run-id> --json jobs --jq '<job projection>'
```

If the current directory is not inside the target repository, pass the
repository explicitly:

```bash
ci-run status 1234567890 <app> --repo owner/repo
```

For a retry attempt, pass the attempt number:

```bash
ci-run status 1234567890 <app> --attempt 2
```
