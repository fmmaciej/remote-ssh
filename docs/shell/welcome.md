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

The three bundled executables share renderers in the welcome library.
For the standard files, one fresh Bash worker loads that library once and
captures each renderer separately before displaying it. Each executable also
remains directly runnable. The panel still reads the same current status data
and keeps its full content and order.

The runner uses the existing external execution path for the whole bundled
group if it finds an extra, modified, or symlinked executable, selects a different
library tree, cannot use the worker, or inherits a nonempty `BASH_ENV` or exported
`SHELLOPTS`/`BASHOPTS`. This keeps local replacements and shell startup hooks
working through their own executable files.

User-local executable modules are loaded after bundled modules from:

```text
${XDG_CONFIG_HOME:-$HOME/.config}/remote-ssh/welcome.d
```

Use `shell/welcome.d/user-module.sh.example` as a starting point for custom
welcome lines. Copy it to the user-local directory with a numbered name such as
`10-example.sh`, make it executable, and keep it fast, local-only, and
noninteractive.

User-local modules should stay fast, local-only, and noninteractive; they run
during shell startup. They always run as external executables with their own
shebang, including files whose names match bundled modules. Each receives empty
stdin; its completed stdout is replayed before the next module starts. Stderr is
hidden unless welcome debug mode is enabled, and a failed module does not stop
later modules. Their shell state cannot change another module or the calling
shell. Module output has no special issue-message syntax.

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
