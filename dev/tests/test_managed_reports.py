from __future__ import annotations

import shlex
import subprocess
from pathlib import Path

import pytest
from conftest import assert_ok, write_executable
from managed_fixture import EngineEnv
from test_managed_lifecycle import command
from test_managed_update import git


def report_repo(engine: EngineEnv) -> None:
    engine.env.update({"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1"})
    git(engine, engine.repo, "init")
    git(engine, engine.repo, "config", "user.name", "Fixture")
    git(engine, engine.repo, "config", "user.email", "fixture@example.invalid")
    git(engine, engine.repo, "config", "commit.gpgsign", "false")
    git(engine, engine.repo, "add", "shell/rc.sh")
    git(engine, engine.repo, "commit", "-m", "synthetic report fixture")


def test_list_empty_filters_alphabetic_alias_and_readonly(engine: EngineEnv) -> None:
    engine.asset("zeta")
    engine.asset("alpha", aliases=("aaa",))
    engine.asset("unsupported")
    p = engine.repo / "tools/defs/unsupported.sh"
    p.write_text(p.read_text().replace("linux:x86_64:gnu", "other:other:any"))
    for args in [[], ["--installed"], ["--all"]]:
        result = command(engine, "list", *args)
        assert_ok(result)
        assert not engine.opt.exists() and not engine.bin.exists()
        if not args:
            assert "alpha" in result.stdout and "unsupported" not in result.stdout
            assert result.stdout.index("alpha") < result.stdout.index("zeta")
        elif args == ["--all"]:
            assert "unsupported" in result.stdout
        else:
            assert "No tools found." in result.stdout
    assert_ok(command(engine, "install", "alpha", "--yes"))
    installed = command(engine, "list", "--installed")
    assert_ok(installed)
    assert installed.stdout.count("alpha") == 1 and "aaa " not in installed.stdout
    payload = (engine.bin / "alpha").resolve()
    payload.unlink()
    broken = command(engine, "list", "--installed")
    assert_ok(broken)
    assert (
        "alpha" in broken.stdout
        and "broken" in broken.stdout
        and "missing" in broken.stdout
    )


def test_check_empty_ignores_expected_only_and_fzf_hint_is_informational(
    engine: EngineEnv,
) -> None:
    report_repo(engine)
    expected = Path(engine.env["XDG_CONFIG_HOME"]) / "remote-ssh/expected-tools"
    expected.parent.mkdir(parents=True)
    expected.write_text("fzf\nexpected-only\n")
    result = command(engine, "check")
    assert_ok(result)
    assert "No managed tools." in result.stdout and "migration-needed" in result.stdout
    assert (
        "remote-ssh install sk" in result.stdout
        and "remote-ssh check sk" in result.stdout
    )
    assert (
        "expected-only" not in result.stdout
        and expected.read_text() == "fzf\nexpected-only\n"
    )
    assert not engine.opt.exists()


def test_check_healthy_alias_stale_missing_shadow_and_external(
    engine: EngineEnv,
) -> None:
    report_repo(engine)
    engine.asset("nu", aliases=("nushell",))
    assert_ok(command(engine, "install", "nu", "--yes"))
    assert_ok(command(engine, "check", "nu"))
    (engine.bin / "nushell").unlink()
    missing = command(engine, "check", "nu")
    assert missing.returncode == 1 and "alias: nushell status=missing" in missing.stdout
    assert_ok(command(engine, "install", "nu", "--yes"))
    shadow = Path(engine.env["PATH"].split(":")[1]) / "nu"
    write_executable(shadow, "#!/bin/sh\nexit 99\n")
    env = engine.env | {"PATH": f"{shadow.parent}:{engine.env['PATH']}"}
    result = subprocess.run(
        [engine.bash, str(engine.repo / "bin/remote-ssh"), "check", "nu"],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 1 and "path-shadowed" in result.stdout
    engine.asset("nu", version="2.0", aliases=("nushell",))
    result = command(engine, "check", "nu")
    assert result.returncode == 1 and "stale" in result.stdout
    assert_ok(command(engine, "uninstall", "nu", "--yes"))
    result = command(engine, "check", "nu")
    assert result.returncode == 1 and "external-only" in result.stdout


def test_retired_and_unsupported_members_remain_in_both_reports(
    engine: EngineEnv,
) -> None:
    report_repo(engine)
    engine.asset("gone")
    engine.asset("other")
    assert_ok(command(engine, "install", "gone", "other", "--yes"))
    (engine.repo / "tools/defs/gone.sh").unlink()
    p = engine.repo / "tools/defs/other.sh"
    p.write_text(p.read_text().replace("linux:x86_64:gnu", "other:other:any"))
    listed = command(engine, "list", "--installed")
    assert_ok(listed)
    assert (
        "gone" in listed.stdout
        and "retired" in listed.stdout
        and "unsupported" in listed.stdout
    )
    checked = command(engine, "check")
    assert (
        checked.returncode == 1
        and "retired" in checked.stdout
        and "unsupported" in checked.stdout
    )
    assert (engine.bin / "gone").exists() and (engine.bin / "other").exists()


@pytest.mark.parametrize(
    "args",
    [
        ("tool", "list"),
        ("doctor",),
        ("check", "--strict"),
        ("list", "--all", "--installed", "--help"),
        ("list", "--help", "oops"),
        ("check", "--help", "unknown"),
    ],
)
def test_removed_and_invalid_report_inputs_do_not_initialize(
    engine: EngineEnv, args: tuple[str, ...]
) -> None:
    result = command(engine, *args)
    assert result.returncode == 1
    assert not engine.opt.exists() and not engine.bin.exists()


def test_report_suppresses_rc_bash_env_and_git_fsmonitor_side_effects(
    engine: EngineEnv,
) -> None:
    report_repo(engine)
    sentinel = engine.assets / "executed"
    hook = engine.assets / "hook"
    write_executable(hook, f"#!/bin/sh\nprintf bad >>{shlex.quote(str(sentinel))}\n")
    git(engine, engine.repo, "config", "core.fsmonitor", str(hook))
    (engine.repo / "shell/rc.sh").write_text(
        f"printf bad >>{shlex.quote(str(sentinel))}\n"
    )
    bash_env = engine.assets / "bash-env"
    bash_env.write_text(f"printf bad >>{shlex.quote(str(sentinel))}\n")
    index = engine.repo / ".git/index"
    before = (index.read_bytes(), index.stat().st_mtime_ns)
    # A PATH utility implemented with env-bash must also inherit the cleared
    # startup environment, before report inventory starts.
    from test_managed_public_faults import utility_stub

    utility_stub(engine, "find", "")
    # Set startup env after the management interpreter has started. The check
    # syntax child must suppress it rather than sourcing rc or hooks.
    result = engine.private(
        '. "$TOOLS_LIB_DIR/commands.lib.sh"\nexport BASH_ENV="$1" ENV="$1"\nremote_ssh_cmd_check_main "$REPO_DIR" "$REPO_DIR" "$REPO_DIR"\n',
        str(bash_env),
    )
    assert_ok(result)
    assert not sentinel.exists()
    assert before == (index.read_bytes(), index.stat().st_mtime_ns)
    assert not engine.opt.exists()


def test_check_library_has_no_executable_path_requirement(engine: EngineEnv) -> None:
    report_repo(engine)
    engine.asset("flyline", layout="bash-builtin")
    # An existing qualified fixture library is data to the report. No load or
    # fake native qualification is used here.
    root = engine.opt / "flyline-1.0"
    (root / "lib").mkdir(parents=True)
    (root / "lib/flyline.so").write_text("library data; never executed")
    (root / ".remote-ssh-release").write_text(
        "format=2\ntool=flyline\nversion=1.0\nlayout=bash-builtin\nlibrary=lib/flyline.so\n"
    )
    active = engine.opt / ".active"
    active.mkdir()
    (active / "flyline").symlink_to(root / "lib/flyline.so")
    result = command(engine, "check", "flyline")
    assert_ok(result)
    assert (
        "adoption-pending" in result.stdout
        and "no executable PATH required" in result.stdout
    )
    assert not (engine.opt / ".remote-ssh-managed").exists()


def test_report_discards_buffer_when_writer_changes_generation(
    engine: EngineEnv,
) -> None:
    import time
    from test_managed_public_faults import utility_stub

    report_repo(engine)
    engine.asset("rg")
    entered = engine.assets / "entered"
    release = engine.assets / "release"
    stub = utility_stub(
        engine,
        "git",
        'for arg in "$@"; do\n if [[ "$arg" == status ]]; then\n touch "$ASSET_DIR/entered"\n for ((n=0;n<200;n++)); do [[ ! -e "$ASSET_DIR/release" ]] || break; sleep 0.05; done\n [[ -e "$ASSET_DIR/release" ]] || exit 88\n fi\ndone\n',
    )
    proc = subprocess.Popen(
        [engine.bash, str(engine.repo / "bin/remote-ssh"), "check"],
        env=engine.env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        deadline = time.monotonic() + 15
        while not entered.exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        assert entered.exists()
        assert_ok(command(engine, "install", "rg", "--yes"))
        release.touch()
        out, err = proc.communicate(timeout=30)
        assert proc.returncode == 1 and out == "" and "retry report" in err
    finally:
        release.touch()
        if proc.poll() is None:
            proc.kill()
            proc.communicate(timeout=5)
        stub.unlink()


def test_list_exposes_failed_and_not_run_without_forging_membership(
    engine: EngineEnv,
) -> None:
    report_repo(engine)
    for tool in ("rg", "fd", "sk"):
        engine.asset(tool)
    (engine.assets / "fd.tar.gz").write_bytes(b"checksum failure")
    result = command(engine, "install", "rg", "fd", "sk", "--yes")
    assert result.returncode == 1
    listed = command(engine, "list")
    assert_ok(listed)
    rows = {
        line.split()[0]: line
        for line in listed.stdout.splitlines()
        if line.split() and line.split()[0] in {"rg", "fd", "sk"}
    }
    assert "managed" in rows["rg"] and "last=install:completed" in rows["rg"]
    assert "unmanaged" in rows["fd"] and "failed" in rows["fd"]
    assert "unmanaged" in rows["sk"] and "not-run" in rows["sk"]
    installed = command(engine, "list", "--installed")
    assert_ok(installed)
    assert "fd " not in installed.stdout and "sk " not in installed.stdout
    assert_ok(command(engine, "check", "rg"))


def test_public_fixture_copy_uses_tracked_whitelist_and_exact_owned_additions(
    tmp_path: Path,
) -> None:
    import shutil
    from conftest import copy_public_tree, public_test_env

    source = tmp_path / "synthetic-source"
    source.mkdir()
    env = public_test_env() | {"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1"}
    subprocess.run(
        [shutil.which("git") or "/usr/bin/git", "-C", str(source), "init", "-q"],
        env=env,
        check=True,
    )
    (source / "public").write_text("public fixture")
    (source / "user.local").write_text("synthetic private; excluded even if tracked")
    (source / ".env.private").write_text("synthetic private; excluded even if tracked")
    (source / "public-link").symlink_to("user.local")
    subprocess.run(
        [
            shutil.which("git") or "/usr/bin/git",
            "-C",
            str(source),
            "add",
            "public",
            "public-link",
            "user.local",
            ".env.private",
        ],
        env=env,
        check=True,
    )
    (source / "unknown-untracked").write_text("must not be copied")
    owned = source / "tools/lib/managed/state.sh"
    owned.parent.mkdir(parents=True)
    owned.write_text("# explicit owned public addition")
    destination = tmp_path / "copy"
    copy_public_tree(source, ".", destination)
    assert (destination / "public").read_text() == "public fixture"
    assert (destination / "public-link").is_symlink()
    assert (
        not (destination / "user.local").exists()
        and not (destination / ".env.private").exists()
    )
    assert not (destination / "unknown-untracked").exists()
    assert (destination / "tools/lib/managed/state.sh").exists()


def test_isolated_fixture_excludes_ambient_credentials_and_rebinds_git_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from conftest import isolated_env

    monkeypatch.setenv("REMOTE_SSH_TEST_CREDENTIAL_TOKEN", "synthetic-denied-token")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(tmp_path / "shared-outer-config"))
    fixture = isolated_env.__wrapped__(tmp_path)
    assert "REMOTE_SSH_TEST_CREDENTIAL_TOKEN" not in fixture.env
    assert fixture.env["GIT_CONFIG_GLOBAL"] == str(fixture.home / ".gitconfig")
    result = subprocess.run(
        ["/bin/sh", "-c", 'test -z "${REMOTE_SSH_TEST_CREDENTIAL_TOKEN+x}" && printf isolated'],
        env=fixture.env, text=True, capture_output=True, timeout=5,
    )
    assert_ok(result)
    assert result.stdout == "isolated"


@pytest.mark.parametrize("external", [False, True])
def test_repair01_terminal_uninstall_reports_available_and_explicit_missing_readonly(engine: EngineEnv, external: bool) -> None:
    from test_managed_uninstall import repair_snapshot

    engine.asset("rg")
    report_repo(engine)
    assert_ok(command(engine, "install", "rg", "--yes"))
    assert_ok(command(engine, "uninstall", "rg", "--yes"))
    if external:
        outside = Path(engine.env["HOME"]) / "external-bin"
        write_executable(outside / "rg", '#!/bin/sh\nprintf executed >"$HOME/executed-external"\n')
        engine.env["PATH"] = str(outside) + ":" + engine.env["PATH"]
    for args in [("list",), ("list", "--all"), ("list", "--installed")]:
        before = repair_snapshot(engine)
        result = command(engine, *args)
        assert_ok(result)
        rows = [line for line in result.stdout.splitlines() if line.startswith("rg ")]
        if "--installed" in args:
            assert not rows
        else:
            assert len(rows) == 1 and "unmanaged" in rows[0] and "available" in rows[0]
            assert "missing" not in rows[0] and "broken" not in rows[0]
        assert repair_snapshot(engine) == before
    before = repair_snapshot(engine)
    result = command(engine, "check", "rg")
    assert result.returncode == 1 and "missing" in result.stdout
    if external:
        assert "external-only" in result.stdout
        assert not (Path(engine.env["HOME"]) / "executed-external").exists()
    assert repair_snapshot(engine) == before
    assert_ok(engine.private('ms_state_load\nif ms_member_has rg; then exit 91; fi\n'))


@pytest.mark.parametrize("condition", ["missing", "broken", "failed-not-run"])
def test_repair01_terminal_classification_is_per_tool(engine: EngineEnv, condition: str) -> None:
    from test_managed_uninstall import repair_snapshot

    engine.asset("nu", aliases=("nushell",))
    engine.asset("rg", aliases=("rga",))
    engine.asset("fd")
    engine.asset("sk")
    assert_ok(command(engine, "install", "nu", "rg", "--yes"))
    assert_ok(command(engine, "uninstall", "nu", "--yes"))
    if condition == "missing":
        (engine.opt / "rg-1.0/rg").unlink()
    elif condition == "broken":
        (engine.bin / "rga").unlink()
    else:
        with (engine.assets / "fd.tar.gz").open("ab") as stream:
            stream.write(b"corrupt")
        assert command(engine, "install", "fd", "sk", "--yes").returncode == 1
    before = repair_snapshot(engine)
    result = command(engine, "list", "--all")
    assert_ok(result)
    rows = {line.split()[0]: line for line in result.stdout.splitlines() if line.split()}
    assert "unmanaged" in rows["nu"] and "available" in rows["nu"]
    assert "missing" not in rows["nu"] and "broken" not in rows["nu"]
    assert "managed" in rows["rg"]
    if condition == "failed-not-run":
        assert "failed" in rows["fd"] and "not-run" in rows["sk"]
    else:
        assert condition in rows["rg"]
    assert repair_snapshot(engine) == before
    result = command(engine, "list", "--installed")
    assert_ok(result)
    assert not any(line.startswith("nu ") for line in result.stdout.splitlines())
    assert any(line.startswith("rg ") for line in result.stdout.splitlines())
    assert repair_snapshot(engine) == before
