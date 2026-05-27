# Runtime Hooks

Back: [Shell Runtime](../shell.md)

`shell/rc.sh` loads shell customizations from `shell/rc.d/`, then optional
platform and host-specific files from:

```text
shell/rc.d/os.d/<os>.sh
shell/rc.d/host.d/<hostname>.sh
```

See `../../shell/rc.d/README.md` for the load order and plugin conventions.

The hook files should stay cheap to load. Network-capable hooks should be
throttled, cache local state, and support an environment toggle before `rc.sh`
is loaded.
