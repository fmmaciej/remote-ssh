"""Independent bounded audit probes; never install into the calling HOME."""
from __future__ import annotations

import hashlib
import json
import os
import shlex
import shutil
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
RESULTS: list[dict] = []


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(args, env, cwd, *, expected=0):
    result = subprocess.run(
        [str(a) for a in args], env=env, cwd=cwd, capture_output=True, text=True, timeout=15
    )
    assert (result.returncode == 0) == (expected == 0), (
        args, result.returncode, result.stdout, result.stderr
    )
    return result


def executable(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    path.chmod(0o755)


def fingerprint():
    protected = json.loads(
        (REPO / "dev/docs/install-cli-planning-evidence/protected-before-implementation.json").read_text()
    )["sha256"]
    final = json.loads(
        (REPO / "dev/docs/install-cli-implementation-evidence/final-source-hashes.json").read_text()
    )
    assert all(digest(REPO / p) == h for p, h in protected.items())
    assert all(digest(REPO / p) == h for p, h in final.items())
    immutables = {
        name: digest(REPO / "dev/docs" / name)
        for name in (
            "install-cli-implementation-plan.md", "install-cli-plan-audit.md",
            "install-cli-implementation-addendum.md", "install-cli-addendum-audit.md",
        )
    }
    assert immutables["install-cli-implementation-plan.md"] == (
        "503e5fb19da5ff45dc3484cc8562dc8169bb7fb6be24e2c712d4f61b9ee38339"
    )
    return {"protected_files": len(protected), "protected_mismatches": [], "final": final,
            "immutable_process_inputs": immutables}


def probe(bash: str):
    with tempfile.TemporaryDirectory(prefix="cli-independent-audit-", dir="/private/tmp") as temp:
        home = Path(temp) / "home"
        home.mkdir()
        root = home / "repo [] ! ' $ ; &"
        root.mkdir()
        for name in ("bin", "lib", "shell", "dots", "tools", "docs"):
            shutil.copytree(REPO / name, root / name)
        shutil.rmtree(root / "tools/defs")
        (root / "tools/defs").mkdir()
        for tool in ("demo", "second", "third"):
            (root / f"tools/defs/{tool}.sh").write_text(
                f"TOOL_NAME={tool}\nGH_REPO=owner/{tool}\nRELEASE_TAG=v1\nVERSION=1\n"
                f'BINARY_NAME={tool}\nASSETS=("linux:x86_64:any|{tool}")\n'
            )
        bindir = home / "physical bin ' $ ; &"
        bindir.mkdir()
        alias = home / "bin alias"
        alias.symlink_to(bindir, target_is_directory=True)
        transport = home / "transport"
        transport.mkdir()
        (transport / "bash").symlink_to(bash)
        executable(transport / "uname", '#!/bin/sh\ncase "$1" in -s) echo Linux;; *) echo x86_64;; esac\n')
        for net in ("curl", "git", "wget"):
            executable(transport / net, '#!/bin/sh\nprintf attempted >> "$HOME/network"\nexit 91\n')
        env = {
            "HOME": str(home), "PATH": f"{transport}:/usr/bin:/bin",
            "XDG_CONFIG_HOME": str(home / "config"), "XDG_STATE_HOME": str(home / "state"),
            "INSTALL_BIN_DIR": "bin alias", "INSTALL_PREFIX": str(home / "opt"),
            "REMOTE_SSH_UPDATE_CHECK": "0", "REMOTE_SSH_ENABLE_GIT_SESSION_IDENTITY": "0",
            "REMOTE_SSH_WELCOME": "0", "LC_ALL": "C",
        }
        executable(home / "opt/demo-1/demo", '#!/bin/sh\nexit 0\n')
        (bindir / "demo").symlink_to(home / "opt/demo-1/demo")
        startup = home / ".bashrc"
        startup.write_text("# untouched audit sentinel\n")
        cli = bindir / "remote-ssh"
        install = run([bash, root / "bin/remote-ssh", "install", "--yes", "demo"], env, home)
        assert cli.readlink() == root / "bin/remote-ssh"
        expected_file = home / "config/remote-ssh/expected-tools"
        assert expected_file.is_file()
        assert set(p.name for p in bindir.iterdir()) == {"remote-ssh", "demo"}
        guide_command = next(x.strip()[5:] for x in install.stdout.splitlines() if x.startswith("  run: "))
        start_command = next(x.strip() for x in install.stdout.splitlines() if x.startswith("  bash --rcfile "))
        export = next(x.strip() for x in install.stdout.splitlines() if x.startswith("  export PATH="))
        for shell in ([bash, "--noprofile", "--norc", "-c"], ["/bin/zsh", "-f", "-c"]):
            guide = run([*shell, guide_command], env, home)
            assert "Interactive usage" in guide.stdout
            command = start_command + " -c " + shlex.quote('test -n "$REMOTE_ENV_DIR" && alias rhelp && printf audit-activated')
            assert "audit-activated" in run([*shell, command], env, home).stdout
        ordinary = run([bash, "--noprofile", "--norc", "-c", "! command -v remote-ssh; " + export + "\nremote-ssh --help"], env, home)
        assert "Usage: remote-ssh" in ordinary.stdout
        # Exact ownership through a directory alias is accepted and reused.
        inode = cli.lstat().st_ino
        assert "export PATH=" not in run(
            [bash, root / "bin/remote-ssh", "install"],
            env | {"PATH": f"{alias}:{env['PATH']}"}, home,
        ).stdout
        assert cli.lstat().st_ino == inode
        # Collision on an already configured installation preserves config and source mode.
        before = expected_file.read_bytes()
        cli.unlink()
        cli.symlink_to("missing")
        source = root / "bin/remote-ssh"
        source.chmod(0o644)
        fail = run([bash, source, "install", "second"], env, home, expected=1)
        assert "refusing to replace" in fail.stderr and "requires confirmation" not in fail.stderr
        assert expected_file.read_bytes() == before
        assert source.stat().st_mode & 0o111 == 0
        assert cli.readlink() == Path("missing")
        cli.unlink()
        # First/middle failures with ABSENT expected-tools complement the candidate sentinel cases.
        executable(root / "tools/install-tool.sh", '''#!/usr/bin/env bash
printf '%s\\n' "$1" >> "$HOME/attempts"
[[ "$1" != "$FAIL_TOOL" ]] || exit 23
mkdir -p "$INSTALL_PREFIX/$1-1" || exit 1
printf '#!/bin/sh\\nexit 0\\n' > "$INSTALL_PREFIX/$1-1/$1"
chmod +x "$INSTALL_PREFIX/$1-1/$1"
ln -s "$INSTALL_PREFIX/$1-1/$1" "$INSTALL_BIN_DIR/$1"
''')
        expected_file.unlink()
        for tool, attempts in (("demo", ["demo"]), ("second", ["demo", "second"])):
            for link in (cli, bindir / "demo"):
                if link.is_symlink():
                    link.unlink()
            if (home / "attempts").exists():
                (home / "attempts").unlink()
            failed = run([bash, source, "install", "--yes", "demo", "second", "third"], env | {"FAIL_TOOL": tool}, home, expected=1)
            assert (home / "attempts").read_text().splitlines() == attempts
            assert not expected_file.exists()
            assert "Installed CLI:" not in failed.stdout and "Configuring environment" not in failed.stdout
            run([cli, "--help"], env, home)
        assert startup.read_text() == "# untouched audit sentinel\n"
        assert not (home / "network").exists()
        RESULTS.append({"bash": bash, "version": run([bash, "-c", 'echo "$BASH_VERSION"'], env, home).stdout.strip(),
                        "status": "passed", "checks": ["relative destination through directory alias", "canonical source/link reuse",
                        "fresh Bash/Zsh printed commands", "real explicit rc activation", "ordinary shell with copied PATH export",
                        "existing config collision nonmutation", "absent config first/middle tool failure", "retained CLI help",
                        "startup and network sentinels"]})


if __name__ == "__main__":
    meta = fingerprint()
    for interpreter in ("/bin/bash", "/opt/homebrew/bin/bash"):
        probe(interpreter)
    (OUT / "independent-probes.json").write_text(json.dumps({"fingerprints": meta, "probes": RESULTS}, indent=2) + "\n")
    print(json.dumps({"protected_files": meta["protected_files"], "probes": RESULTS}, indent=2))
