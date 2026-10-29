# Start And VS Code

Back: [Shell Runtime](../shell.md)

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
