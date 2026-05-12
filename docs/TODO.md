# TODO

**Hardening / install reliability:**

- Complete pinned `CHECKSUMS` coverage for definitions that still lack it:
  `bat`, `eza`, `fd`, `fzf`, `navi`, `nu`, `nvim`, `yazi`, `zoxide`
- Consider signature or artifact attestation validation
- Harden archive extraction before unpacking trusted-but-external assets:
  reject absolute paths, `..` traversal, and unsafe symlink entries
- Make binary selection from extracted archives less heuristic than
  `find ... -name "$BINARY_NAME" | head -n1`; prefer an explicit or validated
  candidate path when archive layouts are ambiguous

**sshf:**

- Documented as optional helper requiring `python3` for now
- Decide later whether to keep Python, replace `ssh_hosts.py`, or add a shell fallback

**Entrypoint:**

- Uninstall

**tmux:**

- Launch automatically if present
- Session name "user@host"

**Docker / Kubernetes:**

- Consider whether Dozzle belongs in the remote-ssh workflow as an optional
  live log viewer for Docker/Kubernetes.
  - Pros:
    - useful browser UI for live container logs
    - easier than juggling many `docker logs -f` / `kubectl logs -f` sessions
    - can help with quick debugging on Docker Compose or small clusters
    - fits as docs/examples/cheatsheet material
  - Cons:
    - it is a web/container app, not a standalone CLI tool for `$PATH`
    - not a replacement for Vector, Loki, ELK/OpenSearch, or retained logs
    - adds socket/RBAC/security considerations
    - may be too heavy for the minimal remote-ssh default install
  - Likely direction: do not add as a default tool; maybe add docs or navi
    examples for running it when needed.

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
- Consider roles later: `rc.d/roles.d/db.sh`, `web.sh`

**Low priority / polish:**

- Clarify the partial Zsh story:
  - `shell/rc.sh` is Bash-first and should fail clearly when sourced from Zsh
  - keep or remove Zsh-specific init branches intentionally, so docs and tests
    do not imply full Zsh support
- Consider pinning the quick-start `runme.sh` flow more strongly:
  - decide whether examples should prefer a tag over the moving `main` branch
- Make the login-time update check easier to tune:
  - keep it throttled and non-mutating
  - consider a more visible config file or command for the existing
    disable/interval settings
- Refresh developer documentation after recent structure changes:
  - update stale repository layout references in `dev/README.md`
  - keep post-install docs consistent about `bash --rcfile ... -i`
- Split larger pytest files when they become hard to review, especially
  `dev/tests/test_tool_init_shell.py`, `dev/tests/test_install_tool_core.py`,
  and shared helpers in `dev/tests/conftest.py`
- Improve `remote-ssh git status` SSH diagnosis edge cases:
  - classify broader `Permission denied` variants that include `publickey`,
    not only the exact `Permission denied (publickey)` output
  - avoid over-suggesting agent fixes when `ssh-add` is missing but SSH auth
    succeeds through `IdentityFile` or another non-agent path
  - if this area grows, split `dev/tests/test_git_status.py` into separate
    success, agent, and auth test files
- Consider moving remaining Git config reads from the `git status` renderer
  into the status model, so rendering is purely formatting.
