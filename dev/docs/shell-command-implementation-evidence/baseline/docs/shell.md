# Shell Runtime

Remote-ssh shells are Bash-first runtime environments for SSH sessions. Start
one with:

```bash
bash --rcfile "$HOME/.local/share/remote-ssh/shell/rc.sh" -i
```

Do not source `shell/rc.sh` from Zsh; use the `bash --rcfile ... -i` form
instead.

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
