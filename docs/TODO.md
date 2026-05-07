# TODO

**Hardening / install reliability:**

- Complete pinned `CHECKSUMS` coverage for definitions that still lack it:
  `bat`, `eza`, `fd`, `fzf`, `navi`, `nu`, `nvim`, `yazi`, `zoxide`
- Consider signature or artifact attestation validation
- Harden archive extraction before unpacking trusted-but-external assets:
  reject absolute paths, `..` traversal, and unsafe symlink entries
- Consider installing `runme.sh` from an explicit tag/ref instead of always
  cloning the moving `main` branch
- Make `remote-ssh-check --strict` validate `BINARY_ALIASES`, not just the
  primary tool symlink

**sshf:**

- Documented as optional helper requiring `python3` for now
- Decide later whether to keep Python, replace `ssh_hosts.py`, or add a shell fallback

**Entrypoint:**

- Uninstall

**tmux:**

- Launch automatically if present
- Session name "user@host"

**rc.d / platform detection:**

- Unify platform detection used by shell runtime and installer:
  - move shared OS/arch normalization to a lightweight common helper usable by
    both `shell/rc.sh` and installer libraries
  - replace shell-only `remote_os_id` duplication with that shared helper where
    practical
  - keep installer asset selection based on `tools/defs/*` exact `ASSETS`,
    `detect_libc`, and `current_default_tools`
- Keep `shell/rc.d/os.d` and `shell/rc.d/host.d` scoped to shell runtime
  customizations only:
  - examples: aliases, exports, shell hooks, host-specific command wrappers
  - do not use them as source of truth for default tool installation
  - do not install dependencies from `rc.d`
- Document this boundary in `shell/rc.d/README.md` and `AGENTS.md`
- Consider roles later: `rc.d/roles.d/db.sh`, `web.sh`
