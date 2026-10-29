from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
from conftest import IsolatedEnv, assert_ok, write_executable

from bench.pty_runner import run_pty_sample

SIMPLE_RENDERERS = """
remote_ssh_welcome_render_remote_ssh() { printf 'remote\\n'; }
remote_ssh_welcome_render_hw() { printf 'hardware\\n'; }
remote_ssh_welcome_render_sw() { printf 'software\\n'; }
"""
WRAPPERS = ("00-remote-ssh.sh", "10-hw.sh", "20-sw.sh")


def _fixture(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    runtime_bash: str,
    tmp_path: Path,
    *,
    simple: bool = True,
) -> tuple[Path, dict[str, str], Path]:
    tree = tmp_path / "runtime"
    for directory in ("shell", "lib", "tools", "bin", "dots", "scripts"):
        shutil.copytree(repo_dir / directory, tree / directory)
    log = tmp_path / "exec.log"
    library = tree / "shell" / "welcome.lib.sh"
    library.write_text('printf "%s\\n" "${0##*/}" >>"$WELCOME_EXEC_LOG"\n' + library.read_text())
    if simple:
        bundled = tree / "shell" / "welcome" / "bundled.sh"
        bundled.write_text(bundled.read_text() + SIMPLE_RENDERERS)
    env = {
        key: value
        for key, value in isolated_env.env.items()
        if not key.startswith(("REMOTE_SSH_", "BASH_FUNC_"))
        and key
        not in {
            "NO_COLOR",
            "BASH_ENV",
            "ENV",
            "SHELLOPTS",
            "BASHOPTS",
            "REMOTE_ENV_DIR",
            "REMOTE_SHELL_DIR",
        }
    }
    (isolated_env.bin_dir / "bash").symlink_to(runtime_bash)
    temp = tmp_path / "temp"
    temp.mkdir()
    env.update(
        {
            "REMOTE_ENV_DIR": str(tree),
            "REMOTE_SHELL_DIR": str(tree / "shell"),
            "REMOTE_SSH_WELCOME_COLOR": "0",
            "REMOTE_SSH_UPDATE_CHECK": "0",
            "WELCOME_EXEC_LOG": str(log),
            "TMPDIR": str(temp),
            "LC_ALL": "C",
        }
    )
    return tree, env, log


def _run(
    tree: Path,
    env: dict[str, str],
    runtime_bash: str,
    *,
    setup: str = "",
    command: str = "remote_ssh_welcome_run",
    input_text: str = "",
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            runtime_bash,
            "-c",
            '. "$1/shell/welcome.lib.sh"\n'
            + setup
            + "\n"
            + command
            + "\nprintf 'CALLER-NEXT\\n'\n",
            "_",
            str(tree),
        ],
        env=env,
        text=True,
        input=input_text,
        capture_output=True,
        start_new_session=True,
        check=False,
    )


def _log(path: Path) -> list[str]:
    return path.read_text().splitlines()


@pytest.mark.parametrize("setup", ["", "set -e", "export BASH_ENV=", "shopt -s nocasematch"])
def test_bundled_canonical_wrappers_use_one_fresh_worker(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str, tmp_path: Path, setup: str
) -> None:
    tree, env, log = _fixture(repo_dir, isolated_env, runtime_bash, tmp_path)
    result = _run(tree, env, runtime_bash, setup=setup)
    assert_ok(result)
    assert result.stdout == "remote\nhardware\nsoftware\nCALLER-NEXT\n"
    assert result.stderr == ""
    assert _log(log) == ["_", "bundled-runner.sh"]


@pytest.mark.parametrize("variant", ["missing", "disabled", "nonexecutable-foreign", "empty"])
def test_bundled_eligibility_and_empty_arrays(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str, tmp_path: Path, variant: str
) -> None:
    tree, env, log = _fixture(repo_dir, isolated_env, runtime_bash, tmp_path)
    directory = tree / "shell" / "welcome.d"
    if variant == "missing":
        (directory / "10-hw.sh").unlink()
    elif variant == "disabled":
        (directory / "10-hw.sh").chmod(0o644)
    elif variant == "nonexecutable-foreign":
        (directory / "05-foreign").write_text("this is ignored\n")
    else:
        for name in WRAPPERS:
            (directory / name).unlink()
    result = _run(
        tree,
        env,
        runtime_bash,
        setup="set -euo pipefail",
        command='remote_ssh_welcome_run_bundled "$REMOTE_SHELL_DIR/welcome.d"',
    )
    assert_ok(result)
    assert result.stderr == ""
    expected = (
        ""
        if variant == "empty"
        else "remote\n"
        + ("hardware\n" if variant == "nonexecutable-foreign" else "")
        + "software\n"
    )
    assert result.stdout == expected + "CALLER-NEXT\n"
    assert _log(log) == (["_"] if variant == "empty" else ["_", "bundled-runner.sh"])


@pytest.mark.parametrize(
    "variant",
    [
        "extra-lf",
        "missing-lf",
        "bytes",
        "huge",
        "nul-middle",
        "nul-end",
        "case-content",
        "case-path",
        "shebang",
        "symlink",
        "foreign-symlink",
        "unknown",
        "modified",
        "worker-missing",
    ],
)
def test_bundled_mismatches_fall_back_for_the_entire_group(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str, tmp_path: Path, variant: str
) -> None:
    tree, env, log = _fixture(repo_dir, isolated_env, runtime_bash, tmp_path)
    directory = tree / "shell" / "welcome.d"
    module = directory / "10-hw.sh"
    original = module.read_bytes()
    if variant == "extra-lf":
        module.write_bytes(original + b"\n")
    elif variant == "missing-lf":
        module.write_bytes(original[:-1])
    elif variant == "bytes":
        module.write_bytes(original + b"# extra bytes")
    elif variant == "huge":
        module.write_bytes(original + b"#" + b"x" * 1024 * 1024)
    elif variant.startswith("nul"):
        module.write_bytes(original[:-1] + b"\0\n" if variant == "nul-middle" else original + b"\0")
    elif variant == "case-content":
        module.write_bytes(original.replace(b"render_hw", b"render_HW"))
    elif variant == "case-path":
        module.rename(directory / "10-HW.sh")
    elif variant == "shebang":
        module.write_bytes(original.replace(b"#!/usr/bin/env bash", b"#!/bin/bash"))
    elif variant in {"symlink", "foreign-symlink"}:
        target = tmp_path / "target"
        write_executable(
            target,
            original.decode()
            if variant == "symlink"
            else "#!/bin/sh\nprintf 'foreign-interpreter\\n'\n",
        )
        module.unlink()
        module.symlink_to(target)
    elif variant == "unknown":
        write_executable(directory / "05-foreign", "#!/bin/sh\nprintf 'foreign-between\\n'\n")
    elif variant == "modified":
        module.write_bytes(original + b"printf 'modified-body\\n'\n")
    else:
        (tree / "shell" / "welcome" / "bundled-runner.sh").unlink()
    result = _run(tree, env, runtime_bash, setup="shopt -s nocasematch")
    assert_ok(result)
    assert result.stdout.startswith("remote\n") and result.stdout.endswith(
        "software\nCALLER-NEXT\n"
    )
    assert "bundled-runner.sh" not in _log(log)
    assert "00-remote-ssh.sh" in _log(log) and "20-sw.sh" in _log(log)
    if variant == "unknown":
        assert result.stdout == "remote\nforeign-between\nhardware\nsoftware\nCALLER-NEXT\n"
    if variant == "foreign-symlink":
        assert "foreign-interpreter\n" in result.stdout
    if variant == "modified":
        assert "hardware\nmodified-body\n" in result.stdout


def test_bundled_qualification_rejects_open_failure_without_relying_on_permissions(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str, tmp_path: Path
) -> None:
    tree, env, _ = _fixture(repo_dir, isolated_env, runtime_bash, tmp_path)
    result = _run(
        tree,
        env,
        runtime_bash,
        command=r"""
        ulimit -n 32
        for ((fd=3; fd<32; fd++)); do eval "exec $fd</dev/null"; done
        if remote_ssh_welcome_bundled_renderer "$REMOTE_SHELL_DIR/welcome.d" "$REMOTE_SHELL_DIR/welcome.d/10-hw.sh"; then
          printf 'WRONGLY-QUALIFIED\n'
        else
          printf 'open-failure-rejected\n'
        fi
        """,
    )
    assert_ok(result)
    assert result.stdout == "open-failure-rejected\nCALLER-NEXT\n"


def test_bundled_canonical_content_mapping_and_renamed_standalone_symlinks(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str, tmp_path: Path
) -> None:
    tree, env, _ = _fixture(repo_dir, isolated_env, runtime_bash, tmp_path)
    result = _run(
        tree,
        env,
        runtime_bash,
        command='for path in "$REMOTE_SHELL_DIR"/welcome.d/*.sh; do remote_ssh_welcome_bundled_renderer "$REMOTE_SHELL_DIR/welcome.d" "$path"; done',
    )
    assert_ok(result)
    assert result.stdout.splitlines() == [
        "remote_ssh_welcome_render_remote_ssh",
        "remote_ssh_welcome_render_hw",
        "remote_ssh_welcome_render_sw",
        "CALLER-NEXT",
    ]
    for name, expected in zip(WRAPPERS, ("remote\n", "hardware\n", "software\n"), strict=True):
        alias = tree / "shell" / "welcome.d" / "renamed"
        alias.symlink_to(name)
        standalone = subprocess.run(
            [str(alias)],
            env={k: v for k, v in env.items() if k != "REMOTE_SHELL_DIR"},
            capture_output=True,
            text=True,
            start_new_session=True,
            check=False,
        )
        assert_ok(standalone)
        assert standalone.stdout == expected
        alias.unlink()


@pytest.mark.parametrize("option", ["SHELLOPTS", "BASHOPTS"])
def test_bundled_exported_options_keep_external_launch_scope_and_caller_state(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str, tmp_path: Path, option: str
) -> None:
    tree, env, log = _fixture(repo_dir, isolated_env, runtime_bash, tmp_path)
    if (
        option == "BASHOPTS"
        and subprocess.check_output(
            [runtime_bash, "-c", 'printf "%s" "${BASH_VERSINFO[0]}"'], text=True
        )
        == "3"
    ):
        pytest.skip("Bash 3.2 has no BASHOPTS")
    bundled = tree / "shell" / "welcome" / "bundled.sh"
    bundled.write_text(
        bundled.read_text()
        + '\nremote_ssh_welcome_render_hw() { case $- in *e*) printf "e=on\\n" ;; *) printf "e=off\\n" ;; esac; if shopt -q nullglob; then printf "n=on\\n"; else printf "n=off\\n"; fi; }\n'
    )
    result = _run(
        tree,
        env,
        runtime_bash,
        setup=f'set -e; shopt -u nullglob; export {option}; before="$(declare -p {option})"',
        command=f'remote_ssh_welcome_run\n[[ "$-" == *e* ]]; ! shopt -q nullglob; after="$(declare -p {option})"; [[ "$before" == "$after" ]]; printf "caller-options-preserved\\n"',
    )
    assert_ok(result)
    assert "e=off\n" in result.stdout
    assert ("n=on\n" in result.stdout) == (option == "BASHOPTS")
    assert "caller-options-preserved\n" in result.stdout
    assert _log(log) == ["_", *WRAPPERS]


def test_bundled_nonempty_bash_env_retains_once_per_module_hooks(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str, tmp_path: Path
) -> None:
    tree, env, log = _fixture(repo_dir, isolated_env, runtime_bash, tmp_path)
    hook = tmp_path / "hook"
    hook.write_text('printf "hook:%s\\n" "${0##*/}"\n')
    result = _run(tree, env | {"HOOK": str(hook)}, runtime_bash, setup='export BASH_ENV="$HOOK"')
    assert_ok(result)
    # Bash 3.2 sets $0 to bash while reading BASH_ENV, before the script name.
    old_bash = (
        subprocess.check_output(
            [runtime_bash, "-c", 'printf "%s" "${BASH_VERSINFO[0]}"'], text=True
        )
        == "3"
    )
    hook_names = ["bash"] * 3 if old_bash else list(WRAPPERS)
    assert (
        result.stdout
        == f"hook:{hook_names[0]}\nremote\nhook:{hook_names[1]}\nhardware\nhook:{hook_names[2]}\nsoftware\nCALLER-NEXT\n"
    )
    assert _log(log) == ["_", *WRAPPERS]


@pytest.mark.parametrize("selected", ["other-tree", "unset", "same-tree-alias"])
def test_bundled_worker_is_bound_to_the_loaded_physical_tree(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str, tmp_path: Path, selected: str
) -> None:
    tree, env, log = _fixture(repo_dir, isolated_env, runtime_bash, tmp_path)
    if selected == "other-tree":
        other = tmp_path / "other"
        shutil.copytree(tree, other)
        bundled = other / "shell" / "welcome" / "bundled.sh"
        bundled.write_text(bundled.read_text().replace("'hardware\\n'", "'other-tree-hardware\\n'"))
        env["SELECTED_SHELL"] = str(other / "shell")
        setup = 'export REMOTE_SHELL_DIR="$SELECTED_SHELL"'
    elif selected == "same-tree-alias":
        alias = tmp_path / "alias"
        alias.symlink_to(tree)
        env["SELECTED_SHELL"] = str(alias / "shell")
        setup = 'export REMOTE_SHELL_DIR="$SELECTED_SHELL"'
    else:
        setup = "unset REMOTE_SHELL_DIR"
    result = _run(tree, env, runtime_bash, setup=setup)
    assert_ok(result)
    assert (
        result.stdout
        == "remote\n"
        + ("other-tree-hardware\n" if selected == "other-tree" else "hardware\n")
        + "software\nCALLER-NEXT\n"
    )
    assert _log(log) == (
        ["_", *WRAPPERS] if selected == "other-tree" else ["_", "bundled-runner.sh"]
    )


@pytest.mark.parametrize("exit_status", [7, 125])
@pytest.mark.parametrize("debug", [False, True])
def test_bundled_renderer_exit_replays_once_and_continues(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    runtime_bash: str,
    tmp_path: Path,
    exit_status: int,
    debug: bool,
) -> None:
    tree, env, log = _fixture(repo_dir, isolated_env, runtime_bash, tmp_path)
    bundled = tree / "shell" / "welcome" / "bundled.sh"
    bundled.write_text(
        bundled.read_text()
        + f'\nremote_ssh_welcome_render_remote_ssh() {{ printf "before-exit\\n"; printf "renderer-stderr\\n" >&2; exit {exit_status}; }}\n'
    )
    result = _run(tree, env | {"REMOTE_SSH_WELCOME_DEBUG": "1" if debug else "0"}, runtime_bash)
    assert_ok(result)
    assert result.stdout == "before-exit\nhardware\nsoftware\nCALLER-NEXT\n"
    assert ("renderer-stderr" in result.stderr) == debug
    assert (f"(exit {exit_status})" in result.stderr) == debug
    assert _log(log) == ["_", "bundled-runner.sh"]
    assert list(Path(env["TMPDIR"]).iterdir()) == []


@pytest.mark.parametrize("failure", ["preflight", "library", "after-start"])
def test_bundled_worker_only_falls_back_before_display(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str, tmp_path: Path, failure: str
) -> None:
    tree, env, log = _fixture(repo_dir, isolated_env, runtime_bash, tmp_path)
    worker = tree / "shell" / "welcome" / "bundled-runner.sh"
    if failure == "library":
        library = tree / "shell" / "welcome.lib.sh"
        library.write_text(
            'if [[ "${0##*/}" == bundled-runner.sh ]]; then return 1; fi\n' + library.read_text()
        )
    else:
        write_executable(
            worker,
            "#!/usr/bin/env bash\n"
            + ("exit 125\n" if failure == "preflight" else "printf 'started-once\\n'\nexit 7\n"),
        )
    result = _run(tree, env | {"REMOTE_SSH_WELCOME_DEBUG": "1"}, runtime_bash)
    assert_ok(result)
    if failure == "after-start":
        assert result.stdout == "started-once\nCALLER-NEXT\n"
        assert "bundled worker failed (exit 7)" in result.stderr
        assert _log(log) == ["_"]
    else:
        assert result.stdout == "remote\nhardware\nsoftware\nCALLER-NEXT\n"
        assert _log(log) == ["_", *WRAPPERS]


@pytest.mark.parametrize("omission", ["hardware-file", "low-level-function"])
def test_worker_incomplete_required_library_stops_before_any_display(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    runtime_bash: str,
    tmp_path: Path,
    omission: str,
) -> None:
    tree, env, _ = _fixture(repo_dir, isolated_env, runtime_bash, tmp_path)
    hardware = tree / "shell" / "welcome" / "hw.sh"
    if omission == "hardware-file":
        hardware.unlink()
    else:
        hardware.write_text(hardware.read_text() + "\nunset -f remote_ssh_welcome_cpu_count\n")
    worker = tree / "shell" / "welcome" / "bundled-runner.sh"
    # An inherited renderer must not conceal a missing provider source file.
    result = subprocess.run(
        [
            runtime_bash,
            "-c",
            'remote_ssh_welcome_print_hw() { printf "inherited-hardware\\n"; }; '
            'export -f remote_ssh_welcome_print_hw; exec "$@"',
            "_",
            str(worker),
            "--",
            *(str(tree / "shell" / "welcome.d" / name) for name in WRAPPERS),
        ],
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        start_new_session=True,
        check=False,
    )
    assert result.returncode == 125, {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
    assert result.stdout == ""


@pytest.mark.parametrize("debug", [False, True])
def test_worker_only_missing_helper_falls_back_once_then_runs_user_and_caller(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    runtime_bash: str,
    tmp_path: Path,
    debug: bool,
) -> None:
    tree, env, log = _fixture(repo_dir, isolated_env, runtime_bash, tmp_path)
    library = tree / "shell" / "welcome.lib.sh"
    library.write_text(
        library.read_text()
        + '\nif [[ "${0##*/}" == bundled-runner.sh ]]; then unset -f remote_ssh_welcome_cpu_count; fi\n'
    )
    user = Path(env["XDG_CONFIG_HOME"]) / "remote-ssh" / "welcome.d"
    write_executable(user / "50-user", "#!/bin/sh\nprintf 'user-after-fallback\\n'\n")
    result = _run(tree, env | {"REMOTE_SSH_WELCOME_DEBUG": "1" if debug else "0"}, runtime_bash)
    assert_ok(result)
    assert result.stdout == "remote\nhardware\nsoftware\nuser-after-fallback\nCALLER-NEXT\n"
    assert _log(log) == ["_", "bundled-runner.sh", *WRAPPERS]
    assert ("required function unavailable: remote_ssh_welcome_cpu_count" in result.stderr) == debug
    assert list(Path(env["TMPDIR"]).iterdir()) == []


@pytest.mark.parametrize("kind", ["issues", "module"])
def test_bundled_temp_allocation_failure_keeps_existing_policy(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str, tmp_path: Path, kind: str
) -> None:
    tree, env, _ = _fixture(repo_dir, isolated_env, runtime_bash, tmp_path)
    write_executable(
        isolated_env.bin_dir / "mktemp",
        f'#!/bin/sh\ncase "$1" in *welcome-{kind}.*) exit 1 ;; esac\nexec /usr/bin/mktemp "$@"\n',
    )
    bundled = tree / "shell" / "welcome" / "bundled.sh"
    bundled.write_text(
        bundled.read_text()
        + '\nremote_ssh_welcome_render_remote_ssh() { printf "remote\\n"; remote_ssh_welcome_issue tools; }\n'
    )
    result = _run(tree, env, runtime_bash)
    assert_ok(result)
    assert (
        result.stdout
        == ("remote\nhardware\nsoftware\n" if kind == "issues" else "") + "CALLER-NEXT\n"
    )
    assert list(Path(env["TMPDIR"]).iterdir()) == []


def test_bundled_and_user_issues_are_collected_once_on_repeated_runs(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str, tmp_path: Path
) -> None:
    tree, env, log = _fixture(repo_dir, isolated_env, runtime_bash, tmp_path)
    bundled = tree / "shell" / "welcome" / "bundled.sh"
    bundled.write_text(
        bundled.read_text()
        + '\nremote_ssh_welcome_render_remote_ssh() { printf "remote\\n"; remote_ssh_welcome_issue tools; remote_ssh_welcome_issue tools; }\n'
    )
    user = Path(env["XDG_CONFIG_HOME"]) / "remote-ssh" / "welcome.d"
    write_executable(
        user / "00-remote-ssh.sh",
        '#!/bin/sh\nprintf "__REMOTE_SSH_WELCOME_ISSUE__:sw\\n"\nprintf "update\\nunknown\\nupdate\\n" >>"$REMOTE_SSH_WELCOME_ISSUES_FILE"\n',
    )
    inherited = tmp_path / "inherited"
    inherited.write_text("untouched\n")
    result = _run(
        tree,
        env | {"REMOTE_SSH_WELCOME_DEBUG": "1", "REMOTE_SSH_WELCOME_ISSUES_FILE": str(inherited)},
        runtime_bash,
        command='remote_ssh_welcome_run\n. "$1/shell/welcome.lib.sh"\nremote_ssh_welcome_run\n[[ -z "${REMOTE_SSH_WELCOME_ISSUES_FILE+x}" ]]; ! declare -p REMOTE_SSH_WELCOME_ISSUES >/dev/null 2>&1',
    )
    assert_ok(result)
    assert result.stdout.count("next:    remote-ssh doctor") == 2
    assert result.stdout.count("__REMOTE_SSH_WELCOME_ISSUE__:sw") == 2
    assert result.stderr.count("ignoring unknown issue: unknown") == 2
    assert inherited.read_text() == "untouched\n"
    assert _log(log).count("bundled-runner.sh") == 2
    assert list(Path(env["TMPDIR"]).iterdir()) == []


def test_user_reserved_basename_and_canonical_bytes_remain_external(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str, tmp_path: Path
) -> None:
    tree, env, log = _fixture(repo_dir, isolated_env, runtime_bash, tmp_path)
    user = Path(env["XDG_CONFIG_HOME"]) / "remote-ssh" / "welcome.d"
    user.mkdir(parents=True)
    shutil.copy2(tree / "shell" / "welcome.d" / "10-hw.sh", user / "10-hw.sh")
    (user.parent / "welcome.lib.sh").write_text(
        'remote_ssh_welcome_render_hw() { printf "canonical-user-external\\n"; }\n'
    )
    write_executable(
        user / "00-remote-ssh.sh",
        '#!/usr/bin/awk -f\nBEGIN { print "non-bash-user" }\n',
    )
    result = _run(tree, env, runtime_bash)
    assert_ok(result)
    assert (
        result.stdout
        == "remote\nhardware\nsoftware\nnon-bash-user\ncanonical-user-external\nCALLER-NEXT\n"
    )
    assert _log(log) == ["_", "bundled-runner.sh"]


def test_renderer_state_mutations_do_not_escape_capture_or_cross_worker_boundary(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str, tmp_path: Path
) -> None:
    tree, env, log = _fixture(repo_dir, isolated_env, runtime_bash, tmp_path)
    bundled = tree / "shell" / "welcome" / "bundled.sh"
    bundled.write_text(
        bundled.read_text()
        + r"""
remote_ssh_welcome_render_remote_ssh() {
  printf 'remote-before-exit\n'
  cd /
  private=changed
  export SHARED=changed
  REMOTE_SSH_STATUS_LIB_LOADED=1
  hostname() { printf 'changed\n'; }
  trap ':' EXIT USR1
  shopt -s nullglob
  set -f
  IFS=:
  exec 3>&-
  exit 7
}
remote_ssh_welcome_render_hw() {
  printf 'sibling:%s:%s:%s\n' "${private-unset}" "$SHARED" "${REMOTE_SSH_STATUS_LIB_LOADED-unset}"
  hostname
  [[ $- != *f* ]] && ! shopt -q nullglob && [[ "$IFS" == $' \t\n' ]] || printf 'STATE-LEAK\n'
  printf 'sibling-fd\n' >&3
  if read -r consumed; then printf 'CONSUMED-INPUT\n'; fi
}
"""
    )
    user = Path(env["XDG_CONFIG_HOME"]) / "remote-ssh" / "welcome.d"
    write_executable(
        user / "50-user",
        '#!/bin/sh\nprintf "user:%s:%s\\n" "${private-unset}" "$SHARED"\nprintf "user-fd\\n" >&3\n',
    )
    fd_file = tmp_path / "fd"
    env.update({"SHARED": "original", "FD_FILE": str(fd_file)})
    result = _run(
        tree,
        env,
        runtime_bash,
        setup='private=original; hostname() { printf "exported-hostname\\n"; }; export -f hostname; exec 3>"$FD_FILE"; before_pwd="$PWD"; trap ":" USR1',
        command='remote_ssh_welcome_run\n[[ "$private" == original && "$SHARED" == original && "$PWD" == "$before_pwd" ]]; [[ $- != *f* ]]; ! shopt -q nullglob; printf "caller-fd\\n" >&3; read -r caller_input; printf "input:%s\\n" "$caller_input"; trap -p USR1',
        input_text="still-for-caller\n",
    )
    assert_ok(result)
    assert (
        result.stdout
        == "remote-before-exit\nsibling:unset:original:unset\nexported-hostname\nsoftware\nuser:unset:original\ninput:still-for-caller\ntrap -- ':' SIGUSR1\nCALLER-NEXT\n"
    )
    assert fd_file.read_text() == "sibling-fd\nuser-fd\ncaller-fd\n"
    assert _log(log) == ["_", "bundled-runner.sh"]


def test_worker_status_library_state_remains_in_first_capture(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str, tmp_path: Path
) -> None:
    tree, env, _ = _fixture(repo_dir, isolated_env, runtime_bash, tmp_path)
    bundled = tree / "shell" / "welcome" / "bundled.sh"
    bundled.write_text(
        bundled.read_text()
        + '\nremote_ssh_welcome_render_remote_ssh() { remote_ssh_welcome_load_commands; printf "status-first:%s\\n" "$REMOTE_SSH_STATUS_LIB_LOADED"; }\nremote_ssh_welcome_render_hw() { printf "status-sibling:%s\\n" "${REMOTE_SSH_STATUS_LIB_LOADED-unset}"; if declare -F remote_ssh_tool_status_load >/dev/null; then printf "FUNCTION-LEAK\\n"; fi; }\n'
    )
    result = _run(tree, env, runtime_bash, setup="REMOTE_SSH_STATUS_LIB_LOADED=1")
    assert_ok(result)
    assert result.stdout == "status-first:1\nstatus-sibling:unset\nsoftware\nCALLER-NEXT\n"


@pytest.mark.parametrize("controlling_terminal", [False, True])
def test_bundled_and_external_replay_preserve_text_and_terminal_transport(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
    runtime_bash: str,
    tmp_path: Path,
    controlling_terminal: bool,
) -> None:
    tree, env, _ = _fixture(repo_dir, isolated_env, runtime_bash, tmp_path)
    bundled = tree / "shell" / "welcome" / "bundled.sh"
    bundled.write_text(
        bundled.read_text()
        + r"""
remote_ssh_welcome_render_remote_ssh() { :; }
remote_ssh_welcome_render_hw() { printf '\n  spaces \\ slash\nCR\rtext\nno-final-LF'; }
remote_ssh_welcome_render_sw() { printf 'last\n'; }
"""
    )
    expected = "\n  spaces \\ slash\nCR\rtext\nno-final-LF\nlast\n"
    redirected = tmp_path / "redirected"
    env["OUTPUT_FILE"] = str(redirected)
    command = 'remote_ssh_welcome_run_bundled "$REMOTE_SHELL_DIR/welcome.d" >"$OUTPUT_FILE"'
    if controlling_terminal:
        sample = run_pty_sample(
            [
                runtime_bash,
                "-c",
                '. "$1/shell/welcome.lib.sh"; ' + command + '; printf "READY-TRANSPORT\\n"',
                "_",
                str(tree),
            ],
            env,
            tmp_path,
            "READY-TRANSPORT",
            10,
        )
        assert sample.returncode == 0 and not sample.timed_out
        assert sample.output_tail == expected.replace("\n", "\r\n") + "READY-TRANSPORT\r\n"
        assert redirected.read_bytes() == b""
    else:
        result = _run(tree, env, runtime_bash, command=command)
        assert_ok(result)
        assert result.stdout == "CALLER-NEXT\n"
        assert redirected.read_bytes() == expected.encode()
