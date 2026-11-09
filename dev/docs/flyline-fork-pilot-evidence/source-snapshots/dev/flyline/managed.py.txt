"""Isolated checkout fixture for native testing of the actual managed runtime.

Intercepts the fixture release URL with local, explicitly supplied archive bytes.
Never installs into the user's prefix or publishes a release.
"""

from __future__ import annotations

import hashlib
import json
import shlex
import shutil
import subprocess
from pathlib import Path


def install(repo: Path, bash: Path, library: Path, home: Path, env: dict[str, str]) -> Path:
    provenance = json.loads((library.parent / "provenance.json").read_text())
    if hashlib.sha256(library.read_bytes()).hexdigest() != provenance["library_sha256"]:
        raise ValueError("Library differs from its build provenance")
    identity, target = provenance["identity"], provenance["target"]
    archive = library.parent / f"flyline-{identity}-{target}.tar.gz"
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    expected = f"{checksum}  {archive.name}\n"
    if (library.parent / "SHA256SUMS").read_text() != expected:
        raise ValueError("Archive differs from SHA256SUMS")
    checkout = home / "checkout"
    for name in ("lib", "tools", "shell", "bin", "dots"):
        shutil.copytree(repo / name, checkout / name)
    member = provenance["library_member"]
    # This definition is fixture-only. Production must use a published release.
    (checkout / "tools/defs/flyline.sh").write_text(
        "TOOL_NAME=flyline\nGH_REPO=fixture/flyline\nRELEASE_TAG=pilot\n"
        f"VERSION={shlex.quote(identity)}\nINSTALL_LAYOUT=bash-builtin\n"
        f'ASSETS=("darwin:aarch64:any|{archive.name}")\n'
        f'CHECKSUMS=("{archive.name}|{checksum}")\n'
        f'LIBRARY_MEMBERS=("{archive.name}|{member}")\n'
    )
    curl = home / "bin/curl"
    curl.write_text(
        "#!/bin/sh\n"
        f'[ "$3" = "https://github.com/fixture/flyline/releases/download/pilot/{archive.name}" ] || exit 99\n'
        f'cp {shlex.quote(str(archive))} "$2"\n'
    )
    curl.chmod(0o755)
    env.update(
        INSTALL_PREFIX=str(home / "managed prefix"),
        INSTALL_BIN_DIR=str(home / "bin"),
        REMOTE_SSH_ENABLE_FLYLINE="1",
    )
    result = subprocess.run(
        [str(bash), str(checkout / "bin/remote-ssh"), "install", "--yes", "flyline"],
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )
    (home / "install.log").write_text(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError(f"Native managed installation failed: {result.stdout}{result.stderr}")
    return checkout
