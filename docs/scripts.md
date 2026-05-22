# Helper Scripts

Remote-ssh includes a small set of public helper commands and shell functions.
Use the CLI to list them from an installed checkout:

```bash
remote-ssh scripts --list
remote-ssh guide scripts
```

The current public helpers are:

- `ci-run`: inspect GitHub Actions jobs. See [ci-run](ci-run.md).
- `helm-chart-diff`: compare OCI Helm chart packages with chart source. See
  [helm-chart-diff](helm-chart-diff.md).
- `ssh-pick`: pick an SSH config host with `fzf`. See
  [Shell helpers](shell.md#ssh-pick).

Files under `scripts/` are implementation details unless they are exposed by a
public helper listed above.
