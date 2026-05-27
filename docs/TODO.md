# TODO

**Top priority: README:**

- Reorganize `README.md` as the main landing page for the project.
  - Make the first screen explain what remote-ssh is, who it is for, and why it
    exists.
  - Keep install instructions short and route details to `docs/install.md`.
  - Keep shell, tool, and developer details out of README unless they are needed
    for first-time use.
  - Make sure README links clearly to `docs/shell.md`, `docs/tools.md`,
    `docs/install.md`, `dev/README.md`, and this TODO.

**Hardening / install reliability:**

- Finish checksum coverage for tools that still install without pinned
  `CHECKSUMS`: `bat`, `eza`, `fd`, `fzf`, `navi`, `nu`, `nvim`, `yazi`,
  `zoxide`.
  - Goal: every downloaded asset should be verified before extraction or
    installation whenever an upstream SHA-256 can be trusted.
  - Keep checksums optional only for projects that do not publish trustworthy
    hashes.

- Later, consider checking whether downloaded files are officially signed by
  the upstream project.
  - This is lower priority than SHA-256 coverage.
  - Do not add heavyweight verification dependencies to runtime without a
    deliberate design decision.

- Harden archive extraction before unpacking external release assets.
  - Current risk: `tar`/`unzip` extraction trusts archive paths.
  - Reject absolute paths, `..` traversal, and unsafe symlink entries before
    extraction.
  - Keep the implementation Bash-friendly and compatible with the minimal
    runtime dependency policy.

- Make binary selection from extracted archives explicit enough to avoid
  installing the wrong file.
  - Current behavior searches for the first file named `$BINARY_NAME` under
    the extracted tree.
  - Prefer a validated candidate path or manifest field when archive layouts
    are ambiguous.
  - Errors should explain which candidates were found and why none was chosen.

**ssh-pick:**

- Documented as optional helper requiring `python3` for now

- Decide later whether to keep Python, replace `ssh_hosts.py`, or add a shell fallback

**Tmux vs Zellij:**

- Launch automatically if present;
  document when each one makes sense
    before adding any automatic launch behavior.

- Session name "user@host"

- Consider whether remote-ssh should recommend `tmux`, `zellij`, both, or
  neither by default.
  - `tmux` pros:
    - widely available on servers and familiar to many admins
    - very stable for long-running SSH sessions
    - works well even on older/minimal systems
  - `tmux` cons:
    - config and keybindings are less discoverable
    - harder for new users to learn
    - usually depends on the host package manager, not the remote-ssh exact
      asset workflow
  - `zellij` pros:
    - standalone GitHub release fits the remote-ssh tool model
    - more discoverable UI and layouts
    - good fit for project-oriented terminal workspaces
  - `zellij` cons:
    - less universally installed and less familiar than `tmux`
    - may be heavier than needed for minimal remote sessions
    - default keybindings can conflict with existing user habits
  - Likely direction: keep both optional

**Neovim / LazyVim:**

- Consider optional LazyVim support as a separate Neovim profile, not the
  default editor.
  - Keep `vim` and `nvim` on the lightweight bundled `dots/vimrc`.
  - Use `NVIM_APPNAME=remote-ssh-lazyvim` for isolation from the default
    Neovim state and config.
  - Add an optional helper or alias such as
    `nvim-lazy='NVIM_APPNAME=remote-ssh-lazyvim nvim'`.
  - Do not install LazyVim plugins during `runme.sh`; first launch may need
    network access and can be slow.
  - If added, document the manual starter install flow in `remote-ssh guide`
    or shell docs.
  - Keep this opt-in because LazyVim may require Git, network access, fonts,
    and plugin-specific tools depending on the selected plugin set.

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

- Refresh post-install docs after recent structure changes:
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
