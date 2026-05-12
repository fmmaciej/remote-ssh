from __future__ import annotations

from pathlib import Path

from conftest import IsolatedEnv, assert_ok, run_remote_ssh


def prepare_prune_dirs(env: IsolatedEnv) -> tuple[Path, Path]:
    bin_dir = env.home / "managed-bin"
    opt_dir = env.home / "managed-opt"
    bin_dir.mkdir()
    opt_dir.mkdir()
    return bin_dir, opt_dir


def prepare_rg_install(bin_dir: Path, opt_dir: Path) -> None:
    active = opt_dir / "rg-15.1.0"
    stale = opt_dir / "rg-14.1.0"
    unknown = opt_dir / "not-a-tool-1.0.0"
    active.mkdir()
    stale.mkdir()
    unknown.mkdir()
    rg = active / "rg"
    rg.write_text("#!/usr/bin/env bash\nprintf rg\n", encoding="utf-8")
    rg.chmod(0o755)
    (bin_dir / "rg").symlink_to(rg)


def prune_env(env: IsolatedEnv, bin_dir: Path, opt_dir: Path) -> dict[str, str]:
    return env.env | {
        "INSTALL_PREFIX": str(opt_dir),
        "INSTALL_BIN_DIR": str(bin_dir),
        "PATH": f"{bin_dir}:/usr/bin:/bin",
    }


def test_prune_dry_run_keeps_candidates(repo_dir: Path, isolated_env: IsolatedEnv) -> None:
    bin_dir, opt_dir = prepare_prune_dirs(isolated_env)
    prepare_rg_install(bin_dir, opt_dir)

    result = run_remote_ssh(repo_dir, ["prune"], env=prune_env(isolated_env, bin_dir, opt_dir))

    assert_ok(result)
    assert "remote-ssh prune (dry-run)" in result.stdout
    assert f"candidate: {opt_dir / 'rg-14.1.0'}" in result.stdout
    assert (opt_dir / "rg-14.1.0").is_dir()
    assert (opt_dir / "rg-15.1.0").is_dir()
    assert (opt_dir / "not-a-tool-1.0.0").is_dir()


def test_prune_apply_removes_only_safe_candidates(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    bin_dir, opt_dir = prepare_prune_dirs(isolated_env)
    prepare_rg_install(bin_dir, opt_dir)
    outside = isolated_env.home / "outside" / "rg-1.0.0"
    outside.mkdir(parents=True)

    result = run_remote_ssh(
        repo_dir,
        ["prune", "--apply"],
        env=prune_env(isolated_env, bin_dir, opt_dir),
    )

    assert_ok(result)
    assert "remote-ssh prune --apply" in result.stdout
    assert f"removed: {opt_dir / 'rg-14.1.0'}" in result.stdout
    assert not (opt_dir / "rg-14.1.0").exists()
    assert (opt_dir / "rg-15.1.0").is_dir()
    assert (opt_dir / "not-a-tool-1.0.0").is_dir()
    assert outside.is_dir()


def test_prune_preserves_relative_symlink_target(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    bin_dir, opt_dir = prepare_prune_dirs(isolated_env)
    active = opt_dir / "rg-15.1.0"
    stale = opt_dir / "rg-14.1.0"
    active.mkdir()
    stale.mkdir()
    rg = active / "rg"
    rg.write_text("#!/usr/bin/env bash\nprintf rg\n", encoding="utf-8")
    rg.chmod(0o755)
    (bin_dir / "rg").symlink_to(Path("../managed-opt/rg-15.1.0/rg"))

    result = run_remote_ssh(
        repo_dir,
        ["prune", "--apply"],
        env=prune_env(isolated_env, bin_dir, opt_dir),
    )

    assert_ok(result)
    assert f"removed: {stale}" in result.stdout
    assert not stale.exists()
    assert active.is_dir()
