# Runtime Config

Back: [Shell Runtime](../shell.md)

Remote-ssh reads an optional config file before loading shell hooks:

```text
${XDG_CONFIG_HOME:-$HOME/.config}/remote-ssh/config
```

The file accepts allowlisted `KEY=value` settings. Blank lines and `#` comments
are ignored, and if a key appears more than once, the last allowlisted line
wins. The file is not executed as shell, and existing environment variables win
over config file values.

After `REMOTE_SSH_CONFIG=0; rcrc`, values previously loaded only from this
config return to defaults while manually exported values remain environment
values. Disable config loading with:

```bash
export REMOTE_SSH_CONFIG=0
```

Supported keys:

```text
REMOTE_SSH_WELCOME
REMOTE_SSH_WELCOME_BANNER
REMOTE_SSH_WELCOME_COLOR
REMOTE_SSH_WELCOME_DEBUG
REMOTE_SSH_WELCOME_USER
REMOTE_SSH_UPDATE_CHECK
REMOTE_SSH_UPDATE_CHECK_INTERVAL
REMOTE_SSH_ENABLE_GIT_SESSION_IDENTITY
NO_COLOR
```

`NO_COLOR` is a standard environment convention and may affect tools outside
remote-ssh.

To inspect effective values and whether they came from the environment, config
file, or defaults, run:

```bash
remote-ssh guide config
```
