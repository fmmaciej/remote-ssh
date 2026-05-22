# Shell Helpers

After installation, start a shell with the remote-ssh environment:

```bash
bash --rcfile "$HOME/.local/share/remote-ssh/shell/rc.sh" -i
```

`shell/rc.sh` is Bash-first and must be loaded by Bash. Do not source it from
Zsh; use the `bash --rcfile ... -i` form above instead.

The post-install output points to the full setup guide:

```bash
remote-ssh guide post-install
```

That guide includes SSH, VS Code Remote-SSH, Git, and interactive shell setup,
including an SSH `RemoteCommand` example using `bash --rcfile ... -i`.

## VS Code Remote-SSH Terminal

VS Code Remote-SSH does not need `RemoteCommand` to start its own server. For
VS Code, prefer a remote terminal profile that starts Bash with remote-ssh's
`rc.sh`. Add this to the VS Code `settings.json` used for the remote host:

```json
{
  "terminal.integrated.profiles.linux": {
    "bash + remote-ssh": {
      "path": "bash",
      "icon": "terminal-bash",
      "args": [
        "--rcfile",
        "${env:HOME}/.local/share/remote-ssh/shell/rc.sh",
        "-i"
      ],
      "overrideName": true
    }
  },
  "terminal.integrated.defaultProfile.linux": "bash + remote-ssh"
}
```

If remote-ssh is installed somewhere other than
`~/.local/share/remote-ssh`, replace the `rc.sh` path with the actual install
path.

## Loaded Helpers

The remote-ssh shell loads a few small helpers:

- `remote-ssh`: main entrypoint for install, uninstall, check, git, update, doctor, and prune.
- `remote-ssh guide`: show loaded aliases, functions, paths, tools, and Git SSH notes.
- `remote-ssh guide starship`: explain the bundled Starship prompt symbols.
- `ci-run`: inspect app-specific GitHub Actions jobs with user-provided `gh`.
- `helm-chart-diff`: compare an OCI chart package with a local or GitHub chart directory.
- `sshf`: pick a host from your SSH config with `fzf`, then run `ssh`.
- `cheats`: open private `navi` cheatsheets from `dots/navi/cheats`.
- `log` and `logrun`: capture command output to a file while still streaming it.

`remote-ssh --help` and `remote-ssh help` are intentionally short CLI usage
outputs. Use `remote-ssh guide` for the longer, dynamic guide generated from
the currently loaded shell configuration.

To reprint the post-install setup instructions later, run:

```bash
remote-ssh guide post-install
```

## Update Check

Interactive remote-ssh shells run a throttled background update check by
default. The check only compares the current checkout with its configured
upstream and prints a short hint when an update is available; it never pulls or
modifies files during login.

Disable it with:

```bash
export REMOTE_SSH_UPDATE_CHECK=0
```

The default interval is one day. Override it with:

```bash
export REMOTE_SSH_UPDATE_CHECK_INTERVAL=<seconds>
```

To check manually:

```bash
remote-ssh update check
```

## Cheatsheets

Private cheatsheets are stored in:

```text
dots/navi/cheats
```

Remote-ssh shells prepend that directory to `NAVI_PATH`, so `navi` and the
`cheats` alias can search project-local snippets without copying them into a
global user directory.

## sshf

`sshf` reads host aliases from `$HOME/.ssh/config`, including `Include` files,
and ignores wildcard entries such as `Host *`. It currently uses
`scripts/ssh_hosts.py`, so this helper requires `python3`.

The dependency is intentional for now because the parser is more reliable than
a shell-only version; a future version may replace it or add a fallback.

## Runtime Plugin Files

`shell/rc.sh` loads shell customizations from `shell/rc.d/`, then optional
platform and host-specific files from:

```text
shell/rc.d/os.d/<os>.sh
shell/rc.d/host.d/<hostname>.sh
```

See `shell/rc.d/README.md` for the load order and plugin conventions.
