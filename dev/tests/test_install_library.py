from __future__ import annotations

import hashlib
import io
import os
import shlex
import shutil
import tarfile
from pathlib import Path

import pytest
from conftest import IsolatedEnv, assert_failed, assert_ok, run_cmd, write_executable


def library_fixture(repo: Path, env: IsolatedEnv, bash: str, invalid: str = ""):
    root = env.home / "checkout"
    for name in ("lib", "tools", "shell", "bin", "dots"):
        shutil.copytree(repo / name, root / name)
    archive = env.home / "library.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        info = tarfile.TarInfo("libflyline.dylib")
        data = b"fixture library, never executed\n"
        info.size = len(data)
        info.mode = 0o644  # A readable library need not be executable.
        if invalid == "symlink":
            info.type, info.linkname, info.size = tarfile.SYMTYPE, "/tmp/outside", 0
        elif invalid == "directory":
            info.type, info.size = tarfile.DIRTYPE, 0
        tar.addfile(info, io.BytesIO(data) if info.isfile() else None)
        if invalid == "traversal":
            info = tarfile.TarInfo("../escaped")
            tar.addfile(info)
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    if invalid == "checksum":
        checksum = "0" * 64
    member = "../libflyline.dylib" if invalid == "member" else "libflyline.dylib"
    (root / "tools/defs/flyline.sh").write_text(
        "TOOL_NAME=flyline\nGH_REPO=fixture/library\nRELEASE_TAG=v1\nVERSION=1\n"
        "INSTALL_LAYOUT=bash-builtin\n"
        'ASSETS=("darwin:aarch64:any|library.tar.gz")\n'
        f'CHECKSUMS=("library.tar.gz|{checksum}")\n'
        f'LIBRARY_MEMBERS=("library.tar.gz|{member}")\n'
    )
    probe_log = env.home / "probes"
    write_executable(
        env.bin_dir / "bash",
        f"""#!/bin/sh
        for arg do
          if [ "$arg" = remote-ssh-library-probe ]; then
            printf 'probe\n' >> {shlex.quote(str(probe_log))}
            exit {1 if invalid == "probe" else 0}
          fi
        done
        exec {shlex.quote(bash)} "$@"
        """,
    )
    write_executable(env.bin_dir / "curl", f'#!/bin/sh\ncp {shlex.quote(str(archive))} "$2"\n')
    write_executable(
        env.bin_dir / "uname", "#!/bin/sh\ncase $1 in -s) echo Darwin;; *) echo arm64;; esac\n"
    )
    opt = env.home / "custom prefix"
    opt.mkdir()
    active = opt / ".active"
    active.mkdir()
    old = opt / "flyline-0"
    old.mkdir()
    (old / "libflyline.dylib").write_text("old library\n")
    (old / ".remote-ssh-release").write_text(
        "format=2\ntool=flyline\nversion=0\nlayout=bash-builtin\nlibrary=libflyline.dylib\n"
    )
    (active / "flyline").symlink_to(old / "libflyline.dylib")
    if invalid == "active-directory":
        (active / "flyline").unlink()
        active.rmdir()
        redirected = env.home / "redirected"
        redirected.mkdir()
        active.symlink_to(redirected)
    if invalid == "link-switch":
        real_mv = shutil.which("mv")
        write_executable(
            env.bin_dir / "mv",
            f"""#!/bin/sh
        case "$*" in *'.active/flyline'*) exit 1;; esac
        exec {shlex.quote(str(real_mv))} "$@"
        """,
        )
    return (
        root,
        opt,
        probe_log,
        env.env
        | {
            "INSTALL_PREFIX": str(opt),
            "INSTALL_BIN_DIR": str(env.bin_dir),
            "REMOTE_SSH_UPDATE_CHECK": "0",
            "REMOTE_SSH_WELCOME": "0",
        },
    )


@pytest.mark.parametrize(
    "invalid",
    [
        "",
        "checksum",
        "symlink",
        "directory",
        "traversal",
        "member",
        "probe",
        "active-directory",
        "link-switch",
    ],
)
def test_library_install_is_transactional(repo_dir, isolated_env, runtime_bash, invalid):
    root, opt, probes, env = library_fixture(repo_dir, isolated_env, runtime_bash, invalid)
    old = (opt / "flyline-0/libflyline.dylib").read_bytes()
    result = run_cmd([runtime_bash, root / "tools/install-tool.sh", "flyline"], env=env)
    link = opt / ".active/flyline"
    if invalid:
        assert_failed(result)
        if invalid != "active-directory":
            assert link.resolve() == opt / "flyline-0/libflyline.dylib"
    else:
        assert_ok(result)
        assert link.readlink().is_absolute()
        assert link.resolve() == opt / "flyline-1/libflyline.dylib"
        assert not link.resolve().stat().st_mode & 0o111
        assert probes.read_text() == "probe\n"
        # A forced same-version reinstall allocates a new directory rather than
        # overwriting a library which an existing shell could still have mapped.
        first = link.resolve()
        assert_ok(run_cmd([runtime_bash, root / "tools/install-tool.sh", "flyline"], env=env))
        assert link.resolve() != first and first.read_bytes() == link.read_bytes()
    assert (opt / "flyline-0/libflyline.dylib").read_bytes() == old
    assert not (isolated_env.bin_dir / "flyline").exists()
    assert not list(opt.glob(".*.tmp.*"))


def test_library_management_lifecycle(repo_dir, isolated_env, runtime_bash):
    root, opt, probes, env = library_fixture(repo_dir, isolated_env, runtime_bash)
    cli = [runtime_bash, root / "bin/remote-ssh"]
    assert_ok(run_cmd([*cli, "install", "--yes", "flyline"], env=env))
    expected = Path(env["XDG_CONFIG_HOME"]) / "remote-ssh/expected-tools"
    assert [
        line for line in expected.read_text().splitlines() if line and not line.startswith("#")
    ] == ["flyline"]
    assert_ok(run_cmd([*cli, "install"], env=env))
    assert probes.read_text() == "probe\n"  # Pinned library is skipped.
    listing = run_cmd([*cli, "tool", "list"], env=env)
    assert_ok(listing)
    assert "flyline" in listing.stdout and "installed" in listing.stdout
    check = run_cmd([*cli, "check", "--strict"], env=env)
    assert_ok(check)
    assert "library" in check.stdout and "ok" in check.stdout
    doctor = run_cmd([*cli, "doctor"], env=env)
    assert "flyline" in doctor.stdout and "ok" in doctor.stdout
    # Both a library and an old format-1 executable release are protected by
    # their active links; only the inactive library is a prune candidate.
    before = run_cmd([*cli, "prune"], env=env)
    assert_ok(before)
    assert f"candidate: {opt / 'flyline-0'}" in before.stdout
    assert f"candidate: {opt / 'flyline-1'}" not in before.stdout
    assert_ok(run_cmd([*cli, "prune", "--apply"], env=env))
    assert not (opt / "flyline-0").exists() and (opt / "flyline-1").exists()
    assert_ok(run_cmd([*cli, "uninstall", "--yes"], env=env))
    assert not (opt / ".active/flyline").is_symlink()
    assert not (opt / "flyline-1").exists() and not expected.exists()


def test_prune_aborts_if_library_links_cannot_be_enumerated(repo_dir, isolated_env, runtime_bash):
    root, opt, _, env = library_fixture(repo_dir, isolated_env, runtime_bash)
    real_find = shutil.which("find")
    write_executable(
        isolated_env.bin_dir / "find",
        f"""#!/bin/sh
    case "$1" in */.active) exit 1;; esac
    exec {shlex.quote(str(real_find))} "$@"
    """,
    )
    result = run_cmd([runtime_bash, root / "bin/remote-ssh", "prune", "--apply"], env=env)
    assert_failed(result)
    assert "aborted" in result.stderr
    assert (opt / "flyline-0/libflyline.dylib").is_file()


@pytest.mark.parametrize(
    "selection", [["flyline"], ["rg", "flyline"], []], ids=["library", "mixed", "automatic"]
)
@pytest.mark.parametrize("active_kind", ["file", "directory-link", "broken-link", "unreadable"])
def test_library_uninstall_preflight_aborts_before_any_mutation(
    repo_dir,
    isolated_env,
    runtime_bash,
    selection,
    active_kind,
):
    root, opt, _, env = library_fixture(repo_dir, isolated_env, runtime_bash)
    old = opt / "flyline-0"
    active = opt / ".active"
    (active / "flyline").unlink()
    active.rmdir()
    target = isolated_env.home / "unrelated"
    target.mkdir()
    (target / "keep").write_text("untouched")
    if active_kind == "file":
        active.write_text("unrelated")
    elif active_kind == "unreadable":
        active.mkdir()
        active.chmod(0)
        if os.access(active, os.R_OK | os.X_OK):
            active.chmod(0o700)
            pytest.skip("Current user can access mode-000 directories")
    else:
        active.symlink_to(target if active_kind == "directory-link" else target / "absent")
    binary = opt / "rg-15.1.0"
    binary.mkdir()
    (binary / "rg").write_text("#!/bin/sh\nexit 0\n")
    (binary / "rg").chmod(0o755)
    (binary / ".remote-ssh-release").write_text(
        "format=1\ntool=rg\nversion=15.1.0\nlayout=binary\nexecutable=rg\n"
    )
    (isolated_env.bin_dir / "rg").symlink_to(binary / "rg")
    expected = Path(env["XDG_CONFIG_HOME"]) / "remote-ssh/expected-tools"
    expected.parent.mkdir(parents=True)
    expected.write_text("# preserve exact user config\nrg\nflyline\n")
    before = expected.read_bytes()
    try:
        result = run_cmd(
            [runtime_bash, root / "bin/remote-ssh", "uninstall", "--yes", *selection], env=env
        )
        assert_failed(result)
        assert "uninstall aborted" in result.stderr
        assert old.is_dir() and binary.is_dir()
        assert (isolated_env.bin_dir / "rg").is_symlink()
        assert expected.read_bytes() == before
        assert (target / "keep").read_text() == "untouched"
        if active_kind == "file":
            assert active.read_text() == "unrelated"
        elif active_kind != "unreadable":
            assert active.is_symlink()
    finally:
        if active_kind == "unreadable":
            active.chmod(0o700)


def test_valid_mixed_library_uninstall(repo_dir, isolated_env, runtime_bash):
    root, opt, _, env = library_fixture(repo_dir, isolated_env, runtime_bash)
    binary = opt / "rg-15.1.0"
    binary.mkdir()
    (binary / "rg").write_text("#!/bin/sh\nexit 0\n")
    (binary / "rg").chmod(0o755)
    (binary / ".remote-ssh-release").write_text(
        "format=1\ntool=rg\nversion=15.1.0\nlayout=binary\nexecutable=rg\n"
    )
    (isolated_env.bin_dir / "rg").symlink_to(binary / "rg")
    result = run_cmd(
        [runtime_bash, root / "bin/remote-ssh", "uninstall", "--yes", "rg", "flyline"], env=env
    )
    assert_ok(result)
    assert not binary.exists() and not (opt / "flyline-0").exists()
    assert not (opt / ".active/flyline").is_symlink()
    assert not (isolated_env.bin_dir / "rg").is_symlink()
