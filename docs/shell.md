# Shell Runtime

Remote-ssh shells are Bash-first runtime environments for SSH sessions. Start
one with:

```bash
remote-ssh shell
```

From a checkout before installation, use `./bin/remote-ssh shell`. The command
preserves your current directory and starts a new interactive Bash; use `exit`
to return to the calling shell. Installation never edits startup files or changes
the default shell. The installed command requires its bin directory in PATH;
the install footer prints a full-path command that works without a PATH change.

The equivalent manual fallback is:

```bash
bash --rcfile "$HOME/.local/share/remote-ssh/shell/rc.sh" -i
```

Do not source `shell/rc.sh` from Zsh; use `remote-ssh shell` or the manual Bash
launch instead.

## Sections

- [Start and VS Code](shell/start.md): interactive startup, post-install setup,
  and VS Code Remote-SSH terminal profiles.
- [Runtime config](shell/config.md): config file format, precedence, supported
  toggles, and `remote-ssh guide config`.
- [Welcome panel](shell/welcome.md): login status, update cache, custom welcome
  modules, colors, and debug toggles.
- [Helpers](shell/helpers.md): loaded helper commands, `cheats`, `log`,
  `logrun`, `bssh`, `bssh-ip`, `ssh-find`, and `ssh-pick`.
- [Runtime hooks](shell/hooks.md): `shell/rc.sh`, `shell/rc.d/`, and platform or
  host-specific hook files.

The dynamic shell guide is available from an installed checkout:

```bash
remote-ssh guide
remote-ssh guide post-install
```
