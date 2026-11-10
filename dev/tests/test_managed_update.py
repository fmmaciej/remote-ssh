from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
from conftest import assert_ok, write_executable
from managed_fixture import EngineEnv
from test_managed_lifecycle import command


def git(engine: EngineEnv, repo: Path, *args: str) -> str:
    result = subprocess.run(
        [shutil.which("git") or "/usr/bin/git", "-c", "maintenance.auto=false",
         "-c", "gc.auto=0", "-c", "core.fsmonitor=false", "-C", repo, *args],
        env=engine.env,
        text=True,
        capture_output=True,
        timeout=120,
    )
    assert_ok(result)
    return result.stdout.strip()


def upstream(engine: EngineEnv) -> Path:
    assert engine.env["REMOTE_ENV_DIR"] == str(engine.repo)
    engine.env.update(
        {
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    git(engine, engine.repo, "init", "-q", "-b", "main")
    git(engine, engine.repo, "config", "user.name", "Fixture User")
    git(engine, engine.repo, "config", "user.email", "fixture@example.invalid")
    git(engine, engine.repo, "config", "commit.gpgsign", "false")
    git(engine, engine.repo, "config", "core.hooksPath", "/dev/null")
    git(engine, engine.repo, "add", ".")
    git(engine, engine.repo, "commit", "-qm", "initial fixture")
    origin = Path(engine.env["HOME"]) / "upstream"
    result = subprocess.run(
        [
            shutil.which("git") or "/usr/bin/git",
            "-c", "maintenance.auto=false", "-c", "gc.auto=0",
            "-c", "core.fsmonitor=false", "clone",
            "-q",
            "--no-hardlinks",
            engine.repo,
            origin,
        ],
        env=engine.env,
        text=True,
        capture_output=True,
        timeout=120,
    )
    assert_ok(result)
    git(engine, origin, "config", "user.name", "Fixture User")
    git(engine, origin, "config", "user.email", "fixture@example.invalid")
    git(engine, origin, "config", "commit.gpgsign", "false")
    git(engine, origin, "config", "core.hooksPath", "/dev/null")
    git(engine, engine.repo, "remote", "add", "origin", str(origin))
    git(engine, engine.repo, "fetch", "-q", "origin")
    git(engine, engine.repo, "branch", "--set-upstream-to=origin/main", "main")
    return origin


def commit(engine: EngineEnv, origin: Path) -> None:
    git(engine, origin, "add", "-A")
    git(engine, origin, "commit", "-qm", "fixture update")


def bump(engine: EngineEnv, origin: Path, tool: str) -> None:
    old = (engine.repo / f"tools/defs/{tool}.sh").read_bytes()
    engine.asset(tool, version="2.0")
    new = (engine.repo / f"tools/defs/{tool}.sh").read_bytes()
    (engine.repo / f"tools/defs/{tool}.sh").write_bytes(old)
    (origin / f"tools/defs/{tool}.sh").write_bytes(new)


def test_update_executes_fresh_engine_and_preserves_untracked_files(
    engine: EngineEnv,
) -> None:
    engine.asset("rg")
    assert_ok(command(engine, "install", "rg", "--yes"))
    origin = upstream(engine)
    bump(engine, origin, "rg")
    source = origin / "tools/lib/managed/install.sh"
    source.write_text(
        source.read_text().replace(
            "ms_install_one() {",
            'ms_install_one() {\n  printf fresh >>"$HOME/fresh-engine"',
        )
    )
    commit(engine, origin)
    (engine.repo / "local-note.md").write_text("keep untracked")
    result = command(engine, "update")
    assert_ok(result)
    assert (engine.bin / "rg").readlink() == engine.opt / "rg-2.0/rg"
    assert (Path(engine.env["HOME"]) / "fresh-engine").read_text() == "fresh"
    assert (engine.repo / "local-note.md").read_text() == "keep untracked"
    assert git(engine, engine.repo, "rev-parse", "HEAD") == git(
        engine, origin, "rev-parse", "HEAD"
    )
    assert_ok(
        engine.private(
            'ms_state_load\nms_member_has rg\nms_journal_active\n[[ "$MS_BATCH_PHASE" == settled ]]\n'
        )
    )


def test_empty_managed_set_updates_only_project_without_profile_install(
    engine: EngineEnv,
) -> None:
    engine.asset("rg")
    origin = upstream(engine)
    (origin / "revision.txt").write_text("fresh project")
    commit(engine, origin)
    result = command(engine, "update")
    assert_ok(result)
    assert "project-only update" in result.stdout
    assert (engine.repo / "revision.txt").read_text() == "fresh project"
    assert not (engine.bin / "rg").exists()
    assert not (Path(engine.env["HOME"]) / "curl.calls").exists()
    assert_ok(
        engine.private(
            'ms_state_load\nms_member_list\n[[ "${#MS_MEMBERS[@]}" == 0 ]]\n'
        )
    )


def test_uninstalled_tool_is_not_resurrected_by_unrelated_install_then_update(
    engine: EngineEnv,
) -> None:
    for tool in ["rg", "nu", "fd"]:
        engine.asset(tool, aliases=("nushell",) if tool == "nu" else ())
    upstream(engine)
    assert_ok(command(engine, "install", "rg", "nu", "--yes"))
    assert_ok(command(engine, "uninstall", "nu", "--yes"))
    assert_ok(command(engine, "install", "fd", "--yes"))
    assert_ok(command(engine, "update"))
    assert (
        not (engine.bin / "nu").is_symlink()
        and not (engine.bin / "nushell").is_symlink()
    )
    assert_ok(
        engine.private(
            "ms_state_load\nms_member_has rg\nms_member_has fd\nif ms_member_has nu; then exit 91; fi\n"
        )
    )


def test_first_update_adopts_six_layouts_before_retiring_rg_in_fresh_checkout(
    engine: EngineEnv,
) -> None:
    for tool in ["rg", "fd", "sk", "nu", "nvim", "flyline"]:
        engine.asset(
            tool,
            layout="bundle"
            if tool == "nvim"
            else "bash-builtin"
            if tool == "flyline"
            else "binary",
            aliases=("nushell",) if tool == "nu" else (),
        )
    origin = upstream(engine)
    (origin / "tools/defs/rg.sh").unlink()
    commit(engine, origin)
    engine.opt.mkdir()
    engine.bin.mkdir()
    (engine.opt / ".active").mkdir()
    for tool in ["rg", "fd", "sk", "nu", "nvim", "flyline"]:
        version = "0.1" if tool == "rg" else "1.0"
        root = engine.opt / f"{tool}-{version}"
        layout = (
            "bundle"
            if tool == "nvim"
            else "bash-builtin"
            if tool == "flyline"
            else "binary"
        )
        member = (
            "bin/nvim"
            if tool == "nvim"
            else "lib/flyline.so"
            if tool == "flyline"
            else tool
        )
        write_executable(root / member, "#!/bin/sh\nexit 91\n")
        if tool == "nvim":
            (root / "share/nvim/runtime").mkdir(parents=True)
        fmt, key = (2, "library") if tool == "flyline" else (1, "executable")
        (root / ".remote-ssh-release").write_text(
            f"format={fmt}\ntool={tool}\nversion={version}\nlayout={layout}\n{key}={member}\n"
        )
        link = (
            engine.opt / ".active/flyline"
            if tool == "flyline"
            else engine.bin / "nushell"
            if tool == "nu"
            else engine.bin / tool
        )
        link.symlink_to(root / member)
    legacy = Path(engine.env["XDG_CONFIG_HOME"]) / "remote-ssh/expected-tools"
    legacy.parent.mkdir()
    legacy.write_text("flyline\n")
    result = command(engine, "update")
    assert result.returncode == 1
    assert "retired: rg" in result.stderr
    assert legacy.read_text() == "flyline\n"
    assert_ok(
        engine.private(
            'ms_state_load\nfor tool in rg fd sk nu nvim flyline; do ms_member_has "$tool"; done\n'
            'if ms_member_has nushell; then exit 91; fi\nms_row_find release rg "$MS_PREFIX/rg-0.1"\n[[ "${MS_ROWS[MS_INDEX+2]}" == 0.1 ]]\n'
        )
    )
    listed = command(engine, "list", "--installed")
    assert_ok(listed)
    names = [line.split()[0] for line in listed.stdout.splitlines()[1:]]
    assert names == ["fd", "flyline", "nu", "nvim", "rg", "sk"]
    assert "retired" in listed.stdout and "nushell " not in listed.stdout
    checked = command(engine, "check")
    assert checked.returncode == 1 and "retired" in checked.stdout
    for layout in ("binary", "bundle", "bash-builtin"):
        assert f"layout={layout}" in checked.stdout
    assert not (Path(engine.env["HOME"]) / "curl.calls").exists()


def test_update_preserves_untracked_obstruction_before_reset(engine: EngineEnv) -> None:
    engine.asset("rg")
    assert_ok(command(engine, "install", "rg", "--yes"))
    origin = upstream(engine)
    (origin / "collision.txt").write_text("new tracked code")
    commit(engine, origin)
    local = engine.repo / "collision.txt"
    local.write_text("keep untracked user data")
    old = git(engine, engine.repo, "rev-parse", "HEAD")
    result = command(engine, "update")
    assert result.returncode == 1
    assert "untracked path" in result.stderr
    assert local.read_text() == "keep untracked user data"
    assert git(engine, engine.repo, "rev-parse", "HEAD") == old
    local.rename(Path(engine.env["HOME"]) / "saved-user-data")
    assert_ok(command(engine, "update"))
    assert local.read_text() == "new tracked code"
    assert_ok(engine.private("ms_state_load\nms_member_has rg\n"))


@pytest.mark.parametrize("overlap", ["metadata", "payload"])
def test_checkout_reset_never_overwrites_managed_data_inside_checkout(
    engine: EngineEnv, overlap: str
) -> None:
    engine.opt = engine.repo / "managed-tools"
    engine.env["INSTALL_PREFIX"] = str(engine.opt)
    engine.asset("rg")
    origin = upstream(engine)
    assert_ok(command(engine, "install", "rg", "--yes"))
    protected = (
        "managed-tools/.remote-ssh-managed/format"
        if overlap == "metadata"
        else "managed-tools/rg-1.0/rg"
    )
    target = origin / protected
    target.parent.mkdir(parents=True)
    target.write_text("foreign tracked replacement")
    commit(engine, origin)
    before = (engine.repo / protected).read_bytes()
    old = git(engine, engine.repo, "rev-parse", "HEAD")
    result = command(engine, "update")
    assert result.returncode == 1
    assert "overlaps managed data" in result.stderr
    assert (engine.repo / protected).read_bytes() == before
    assert git(engine, engine.repo, "rev-parse", "HEAD") == old
    assert_ok(engine.private("ms_state_load\nms_member_has rg\n"))


@pytest.mark.parametrize(
    "args", [["--yes"], ["rg"], ["--help", "--bogus"], ["--help", "rg"]]
)
def test_update_rejects_extra_arguments_before_state_or_git(
    engine: EngineEnv, args: list[str]
) -> None:
    result = command(engine, "update", *args)
    assert result.returncode == 1
    assert result.stderr
    assert not engine.opt.exists() and not engine.bin.exists()


def test_update_keeps_native_git_maintenance_and_fsmonitor_inside_operation(engine: EngineEnv) -> None:
    import hashlib
    import json
    import shlex
    import zlib

    engine.env["GIT_DEFAULT_HASH"] = "sha1"
    engine.asset("rg")
    origin = upstream(engine)
    (origin / "revision.txt").write_text("controlled native update")
    commit(engine, origin)
    hooks = Path(engine.env["HOME"]) / "controlled-git-hooks"
    hooks.mkdir()
    gc_marker = hooks / "gc-requested"
    fs_marker = hooks / "fsmonitor-requested"
    write_executable(hooks / "pre-auto-gc", f"#!/bin/sh\nprintf requested >{shlex.quote(str(gc_marker))}\nexit 1\n")
    write_executable(hooks / "fsmonitor", f"#!/bin/sh\nprintf requested >{shlex.quote(str(fs_marker))}\nprintf 'controlled-token\\000/\\000'\n")
    for key, value in [("core.hooksPath", str(hooks)), ("core.fsmonitor", str(hooks / "fsmonitor")),
                       ("maintenance.auto", "true"), ("maintenance.gc.enabled", "true"),
                       ("gc.auto", "1"), ("gc.autoDetach", "true")]:
        git(engine, engine.repo, "config", key, value)
    # Force native auto-GC's loose-object heuristic, without downloading or
    # modifying any real repository. A positive controlled probe is archived.
    found = 0
    candidate = 0
    while found < 300:
        payload = f"controlled-automatic-maintenance-{candidate}".encode()
        data = f"blob {len(payload)}\0".encode() + payload
        oid = hashlib.sha1(data).hexdigest()
        candidate += 1
        if oid.startswith("17"):
            path = engine.repo / ".git/objects" / oid[:2] / oid[2:]
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(zlib.compress(data))
            found += 1
    config = engine.repo / ".git/config"
    before = config.read_bytes()
    trace = hooks / "trace.jsonl"
    engine.env["GIT_TRACE2_EVENT"] = str(trace)
    result = command(engine, "update")
    assert_ok(result)
    assert "project-only update" in result.stdout
    assert (engine.repo / "revision.txt").read_text() == "controlled native update"
    assert config.read_bytes() == before
    assert not gc_marker.exists() and not fs_marker.exists()
    events = [json.loads(line) for line in trace.read_text().splitlines()]
    children = [event.get("argv", []) for event in events if event.get("event") == "child_start"]
    assert not any("maintenance" in argv or ("gc" in argv and "--auto" in argv) for argv in children)
