from __future__ import annotations

import os
import signal
import subprocess
import time
from pathlib import Path

import pytest
from conftest import ToolStateEnv, assert_ok
from test_managed_state import run, script


def wait_path(path: Path, process: subprocess.Popen[str]) -> None:
    deadline = time.monotonic() + 15
    while not path.exists():
        assert process.poll() is None, process.communicate()
        assert time.monotonic() < deadline
        time.sleep(0.02)


@pytest.mark.parametrize("death", [signal.SIGTERM, signal.SIGKILL])
def test_ticket_serializes_writers_and_survives_owner_signals(
    repo_dir: Path, tool_env: ToolStateEnv, runtime_bash: str, death: signal.Signals
) -> None:
    ready = tool_env.home / "ready"
    first = subprocess.Popen(
        [
            runtime_bash,
            "-c",
            script(
                repo_dir,
                'ms_state_load\nms_lock_acquire "$MS_PREFIX"\n'
                'printf ready >"$HOME/ready"\nwhile :; do sleep 1; done',
            ),
        ],
        env=tool_env.env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        wait_path(ready, first)
        blocked = run(
            repo_dir,
            tool_env,
            runtime_bash,
            'ms_state_load\nMS_LOCK_TIMEOUT=0\nms_lock_acquire "$MS_PREFIX"\nprintf entered',
        )
        assert blocked.returncode != 0
        assert "entered" not in blocked.stdout
        # Report readers see an active writer without taking writable locks.
        report = run(repo_dir, tool_env, runtime_bash, "ms_report_begin")
        assert report.returncode != 0
        first.send_signal(death)
        first.communicate(timeout=5)
        next_writer = run(
            repo_dir,
            tool_env,
            runtime_bash,
            'ms_state_load\nMS_LOCK_TIMEOUT=2\nms_lock_acquire "$MS_PREFIX"\nprintf entered',
        )
        assert_ok(next_writer)
        assert next_writer.stdout == "entered"
        tickets = list((tool_env.opt_dir / ".remote-ssh-lock").glob("p*"))
        assert len(tickets) == (1 if death == signal.SIGKILL else 0)
    finally:
        if first.poll() is None:
            first.kill()
            first.communicate()


def test_simultaneous_bakery_writers_never_overlap_critical_sections(
    repo_dir: Path, tool_env: ToolStateEnv, runtime_bash: str
) -> None:
    # Initialize storage, then race independent processes (same root pair).
    assert_ok(
        run(
            repo_dir,
            tool_env,
            runtime_bash,
            'ms_state_load\nms_lock_acquire "$MS_PREFIX"',
        )
    )
    processes = [
        subprocess.Popen(
            [
                runtime_bash,
                "-c",
                script(
                    repo_dir,
                    'ms_state_load\nMS_LOCK_TIMEOUT=12\nms_lock_acquire "$MS_PREFIX"\n'
                    'mkdir "$HOME/critical"\nprintf "enter %s\\n" "$$" >>"$HOME/order"\n'
                    'sleep 0.1\nprintf "exit %s\\n" "$$" >>"$HOME/order"\nrmdir "$HOME/critical"',
                ),
            ],
            env=tool_env.env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        for _ in range(4)
    ]
    for process in processes:
        stdout, stderr = process.communicate(timeout=20)
        assert process.returncode == 0, (stdout, stderr)
    lines = (tool_env.home / "order").read_text().splitlines()
    assert len(lines) == 8
    for entering, leaving in zip(lines[::2], lines[1::2], strict=True):
        assert entering.startswith("enter ") and leaving == entering.replace(
            "enter", "exit"
        )


def test_live_choosing_ticket_blocks_and_dead_ticket_is_ignored_without_reclaim(
    repo_dir: Path, tool_env: ToolStateEnv, runtime_bash: str
) -> None:
    assert_ok(
        run(
            repo_dir,
            tool_env,
            runtime_bash,
            'ms_state_load\nms_lock_acquire "$MS_PREFIX"',
        )
    )
    lock = tool_env.opt_dir / ".remote-ssh-lock"
    choosing = lock / f"p{os.getpid()}-123456"
    choosing.mkdir(mode=0o700)
    result = run(
        repo_dir,
        tool_env,
        runtime_bash,
        'ms_state_load\nMS_LOCK_TIMEOUT=0\nms_lock_acquire "$MS_PREFIX"',
    )
    assert result.returncode != 0
    choosing.rmdir()
    dead = subprocess.Popen([runtime_bash, "-c", "exit 0"])
    dead.wait()
    stale = lock / f"p{dead.pid}-654321"
    stale.mkdir(mode=0o700)
    assert_ok(
        run(
            repo_dir,
            tool_env,
            runtime_bash,
            'ms_state_load\nms_lock_acquire "$MS_PREFIX"',
        )
    )
    assert stale.exists()


def test_prune_lock_plan_needs_only_prefix_and_reports_never_create_storage(
    repo_dir: Path, tool_env: ToolStateEnv, runtime_bash: str
) -> None:
    tool_env.bin_dir.chmod(0o555)
    try:
        result = run(
            repo_dir,
            tool_env,
            runtime_bash,
            'ms_state_load\nms_lock_plan prune 1\n[[ "${#MS_REQUIRED_LOCKS[@]}" == 1 ]]\n'
            'ms_lock_acquire "${MS_REQUIRED_LOCKS[@]}"\n[[ ! -e "$MS_BIN/.remote-ssh-lock" ]]',
        )
        assert_ok(result)
    finally:
        tool_env.bin_dir.chmod(0o755)


def test_registered_delayed_mv_keeps_roots_busy_after_owner_sigkill(
    repo_dir: Path, tool_env: ToolStateEnv, runtime_bash: str
) -> None:
    source = tool_env.home / "source"
    destination = tool_env.home / "destination"
    source.write_text("published only under the original lease")
    stub = tool_env.bin_dir / "mv"
    stub.write_text(
        f"#!{runtime_bash}\n"
        'for target in "$@"; do :; done\n'
        'if [[ "$target" == "$HOME/destination" ]]; then\n'
        '  printf ready >"$HOME/utility-ready"\n'
        '  while [[ ! -e "$HOME/release-utility" ]]; do sleep 0.05; done\n'
        'fi\nexec /bin/mv "$@"\n'
    )
    stub.chmod(0o755)
    owner = subprocess.Popen(
        [
            runtime_bash,
            "-c",
            script(
                repo_dir,
                'ms_state_load\nms_lock_acquire "$MS_PREFIX" "$MS_BIN"\n'
                'ms_lock_mutate mv "$HOME/source" "$HOME/destination"',
            ),
        ],
        env=tool_env.env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        wait_path(tool_env.home / "utility-ready", owner)
        owner.kill()
        owner.wait(timeout=5)
        # Both roots and optimistic readers must see the live mutator even though
        # the original owner is now dead and reaped.
        for root in ['"$MS_PREFIX"', '"$MS_BIN"']:
            result = run(
                repo_dir,
                tool_env,
                runtime_bash,
                f"ms_state_load\nMS_LOCK_TIMEOUT=0\nms_lock_acquire {root}\nprintf entered",
            )
            assert result.returncode != 0
            assert "entered" not in result.stdout
        assert run(repo_dir, tool_env, runtime_bash, "ms_report_begin").returncode != 0
        assert not destination.exists()
        (tool_env.home / "release-utility").touch()
        deadline = time.monotonic() + 10
        while not destination.exists():
            assert time.monotonic() < deadline
            time.sleep(0.02)
        # The new writer can enter only after that registered utility exits.
        result = run(
            repo_dir,
            tool_env,
            runtime_bash,
            'ms_state_load\nMS_LOCK_TIMEOUT=5\nms_lock_acquire "$MS_PREFIX" "$MS_BIN"\nprintf entered',
        )
        assert_ok(result)
        assert result.stdout == "entered"
        assert destination.read_text() == "published only under the original lease"
    finally:
        (tool_env.home / "release-utility").touch()
        if owner.poll() is None:
            owner.kill()
        owner.communicate(timeout=10)
