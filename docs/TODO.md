# TODO

**Hardening / install reliability:**

- Complete pinned checksum coverage for tools whose upstream releases do not
  publish per-asset `.sha256` files
- Consider signature or artifact attestation validation

**sshf:**

- Documented as optional helper requiring `python3` for now
- Decide later whether to keep Python, replace `ssh_hosts.py`, or add a shell fallback

**Entrypoint:**

- Uninstall

**tmux:**

- Launch automatically if present
- Session name "user@host"

**rc.d:**

- Consider roles later: `rc.d/roles.d/db.sh`, `web.sh`
