from __future__ import annotations

from pathlib import Path

from conftest import assert_ok
from managed_fixture import EngineEnv
from test_managed_lifecycle import command
from test_managed_update import commit, upstream


def test_quick_profile_is_additive_and_both_spellings_select_same_set(
    engine: EngineEnv,
) -> None:
    quick = (
        "rg",
        "fd",
        "sd",
        "bat",
        "starship",
        "eza",
        "zoxide",
        "sk",
        "navi",
        "atuin",
    )
    for tool in (*quick, "extra"):
        engine.asset(tool)
    assert_ok(command(engine, "install", "extra", "rg", "fd", "--yes"))
    assert_ok(command(engine, "install", "sk", "sk", "--yes"))
    assert_ok(command(engine, "install", "--profile", "quick", "--yes"))
    calls = Path(engine.env["HOME"]) / "curl.calls"
    before = calls.read_bytes()
    assert len(before.splitlines()) == len(quick) + 1
    assert_ok(command(engine, "install", "--profile=quick", "--yes"))
    assert calls.read_bytes() == before
    result = engine.private(
        'ms_state_load\nms_member_list\nprintf "%s\\n" "${MS_MEMBERS[@]}"\n'
    )
    assert_ok(result)
    assert set(result.stdout.splitlines()) == set(quick) | {"extra"}


def test_profile_changes_only_apply_to_later_explicit_install(
    engine: EngineEnv,
) -> None:
    for tool in ("rg", "navi", "sk"):
        engine.asset(tool)
    sets = engine.repo / "tools/lib/install/tool_sets.sh"
    original = sets.read_text()
    line = next(
        line for line in original.splitlines() if line.startswith("QUICK_TOOLS=")
    )
    sets.write_text(original.replace(line, "QUICK_TOOLS=(rg navi)"))
    origin = upstream(engine)
    assert_ok(command(engine, "install", "--profile", "quick", "--yes"))
    assert_ok(command(engine, "uninstall", "navi", "--yes"))
    fresh = origin / "tools/lib/install/tool_sets.sh"
    fresh.write_text(
        fresh.read_text().replace("QUICK_TOOLS=(rg navi)", "QUICK_TOOLS=(rg navi sk)")
    )
    commit(engine, origin)
    assert_ok(command(engine, "update"))
    assert not (engine.bin / "navi").exists() and not (engine.bin / "sk").exists()
    assert_ok(
        engine.private(
            "ms_state_load\nms_member_has rg\nif ms_member_has navi || ms_member_has sk; then exit 91; fi\n"
        )
    )
    assert_ok(command(engine, "install", "--profile=quick", "--yes"))
    assert (engine.bin / "navi").exists() and (engine.bin / "sk").exists()


def test_bundle_requirement_revision_keeps_old_manifest_without_requiring_removed_data(
    engine: EngineEnv,
) -> None:
    import hashlib
    import io
    import tarfile
    from test_managed_reports import report_repo

    report_repo(engine)
    engine.asset("nvim", layout="bundle")
    definition = engine.repo / "tools/defs/nvim.sh"
    definition.write_text(
        definition.read_text().replace(
            'BUNDLE_REQUIRED_PATHS=("share/nvim/runtime")',
            'BUNDLE_REQUIRED_PATHS=("share/nvim/runtime/data")',
        )
    )
    assert_ok(command(engine, "install", "nvim", "--yes"))
    old = (engine.bin / "nvim").resolve().parent.parent
    old_data = (old / "share/nvim/runtime/data").read_bytes()
    engine.asset("nvim", layout="bundle", version="2.0")
    archive = engine.assets / "nvim.tar.gz"
    old_hash = hashlib.sha256(archive.read_bytes()).hexdigest()
    entries = []
    with tarfile.open(archive, "r:gz") as source:
        for member in source.getmembers():
            if member.name.endswith("/runtime/data"):
                continue
            data = source.extractfile(member).read() if member.isfile() else None
            entries.append((member, data))
    with tarfile.open(archive, "w:gz") as target:
        for member, data in entries:
            target.addfile(member, io.BytesIO(data) if data is not None else None)
    definition.write_text(
        definition.read_text().replace(
            old_hash, hashlib.sha256(archive.read_bytes()).hexdigest()
        )
    )
    assert_ok(command(engine, "install", "nvim", "--yes"))
    current = (engine.bin / "nvim").resolve().parent.parent
    assert current != old and not (current / "share/nvim/runtime/data").exists()
    assert (old / "share/nvim/runtime/data").read_bytes() == old_data
    assert_ok(command(engine, "check", "nvim"))
