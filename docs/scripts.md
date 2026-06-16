# Helper Scripts

Remote-ssh includes a small set of public helper commands and shell functions.
Use the CLI to list them from an installed checkout:

```bash
remote-ssh scripts --list
remote-ssh guide scripts [helper]
```

The current public helpers are:

- `bssh`: run `bssh` with stream output and the shared SSH config. See
  [Shell helpers](shell/helpers.md#bssh).
- `bssh-ip`: print the resolved SSH hostname, user, and port. See
  [Shell helpers](shell/helpers.md#bssh).
- `ssh-find`: find an SSH host by alias, hostname, or IP address. See
  [Shell helpers](shell/helpers.md#ssh-find).
- `ssh-pick`: pick an SSH host by alias, hostname, or IP address. See
  [Shell helpers](shell/helpers.md#ssh-pick).

Files under `scripts/` are implementation details unless they are exposed by a
public helper listed above.
