# Welcome Panel

Back: [Shell Runtime](../shell.md)

Interactive shells render a small remote-ssh welcome panel by default. It shows
host, update, tool, script, hardware, SSH agent, and Git session config status.
The optional `next` line is shown only for actionable problems. A disabled or
never-cached update check is informational, and `ssh-agent` status alone does
not trigger `next`.

## Update Check

Interactive remote-ssh shells run a throttled background update check by
default. The check refreshes local state silently in the background; the welcome
panel renders the cached update status during login. The check only compares the
current checkout with its configured upstream; it never pulls or modifies files
during login.

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

## Modules

`shell/welcome/` contains internal library modules used by `welcome.lib.sh`; do
not copy files from that directory for customization. Bundled executable status
modules live in:

```text
shell/welcome.d
```

User-local executable modules are loaded after bundled modules from:

```text
${XDG_CONFIG_HOME:-$HOME/.config}/remote-ssh/welcome.d
```

Use `shell/welcome.d/user-module.sh.example` as a starting point for custom
welcome lines. Copy it to the user-local directory with a numbered name such as
`10-example.sh`, make it executable, and keep it fast, local-only, and
noninteractive.

User-local modules should stay fast, local-only, and noninteractive; they run
during shell startup.

## Toggles

Disable the whole panel, user-local modules, banner, colors, or enable debug
before loading `rc.sh`:

```bash
export REMOTE_SSH_WELCOME=0
export REMOTE_SSH_WELCOME_USER=0
export REMOTE_SSH_WELCOME_BANNER=0
export REMOTE_SSH_WELCOME_COLOR=0
export REMOTE_SSH_WELCOME_DEBUG=1
# or use the standard:
export NO_COLOR=1
```
