# Remote-ssh

Remote-ssh is a lightweight, shell-first framework for building SSH
sessions across machines. It focuses on explicit configuration, modular
session setup, development tooling—without heavy dependencies.

## Quick start

The `runme.sh` script is a **remote install script**.
It is intended to be executed directly (e.g. via `curl | bash`) and **not**
from a local repository checkout.

### Download and run

You can download and execute the script directly:

```bash
curl -fsSL https://raw.githubusercontent.com/fmmaciej/remote-ssh/main/runme.sh | bash
```

## Repository structure

| Path              | Role                       |
| ----------------- | -------------------------- |
| `~/.local/share/` | Installation destination   |
| `dev/`            | Development                |
| `runme.sh`        | Remote installer           |
| `install.sh`      | Local installer            |

## Notes

- `runme.sh` is not meant to be run locally from a cloned repository.
- No developer tooling from `dev/` is required to use `runme.sh`.
- The working copy used for development may differ from the installed copy.
- Review the script before running it, especially on production or remote systems.
- As for now there is no general `remote-ssh` entrypoint.
- For `remote-ssh` update use `git pull` && `./install.sh` method.

## License

Code is licensed under MIT.
Documentation is licensed under CC BY 4.0.
