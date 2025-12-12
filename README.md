# Remote-ssh

Remote-ssh is a lightweight, shell-first framework for building predictable and repeatable SSH sessions across machines.
It focuses on explicit configuration, modular session setup, and clean separation between runtime, installation, and development tooling—without hidden magic or heavy dependencies.

## Quick start

The `runme.sh` script is a **remote bootstrap installer**.
It is intended to be executed directly (e.g. via `curl | bash`) and **not**
from a local repository checkout.

### Download and run

You can download and execute the script directly:

```bash
curl -fsSL https://raw.githubusercontent.com/fmmaciej/remote-ssh/main/runme.sh | bash
```

## Notes

- `runme.sh` is not meant to be run locally from a cloned repository.
- No developer tooling from `dev/` is required to use `runme.sh`.
- The working copy used for development may differ from the installed copy.
- Review the script before running it, especially on production or remote systems.

## Files

| File                        | Role                       |
| --------------------------- | -------------------------- |
| `runme.sh`                  | Remote installer / updater |
| `bootstrap.sh`              | Environment configuration  |
| `~/.local/share/remote-ssh` | Installation destination   |
| Remote-ssh repository       | Development                |

## Todo

**runme.sh:**

- Install
- Uninstall
- Update
- Check

**tmux:**

- Launch automatically if present
- Session name "user@host"

**rc.d:**

- Use it as plugin system
- Each plugin should handle its dependencies
- `rc.d/host.d/<hostname>.sh`
- `rc.d/os.d/linux.sh`, `darwin.sh`
- `rc.d/roles.d/db.sh`, `web.sh`

**atuin:**

- Use as a history manager?
