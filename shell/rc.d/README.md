# rc.d flow

`rc.sh` loads shell customizations in this order:

1. `shell/env.sh`
2. `shell/aliases.sh`
3. `shell/rc.d/*.sh`
4. `shell/rc.d/os.d/<os>.sh`
5. `shell/rc.d/host.d/<hostname>.sh`

`<os>` is detected from `uname -s` and normalized to `linux` or `darwin`
for the common cases.

`<hostname>` comes from `hostname -s` with a fallback to `hostname`.

Missing directories and missing files are ignored. This keeps the default
runtime small while allowing local overrides on specific operating systems or
hosts.

## Plugin files

Each file should be safe to source more than once and should handle its own
dependencies:

```bash
# shellcheck shell=bash

ensure_this_file_sourced

have atuin || return 0
eval "$(atuin init bash)"
```

Do not install dependencies from `rc.d` files. Installation belongs to
`install.sh` and `tools/defs`.

## OS files

Use `os.d` for platform-specific runtime behavior:

```text
shell/rc.d/os.d/linux.sh
shell/rc.d/os.d/darwin.sh
```

Example files are provided as `.example` files and are not loaded until copied
to `.sh`.

## Host files

Use `host.d` for one machine only:

```text
shell/rc.d/host.d/<hostname -s>.sh
```

Example files are provided as `.example` files and are not loaded until copied
to `.sh`.
