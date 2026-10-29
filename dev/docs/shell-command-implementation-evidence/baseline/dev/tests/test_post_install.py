from __future__ import annotations

import shlex
import shutil
import textwrap
from pathlib import Path

import pytest
from conftest import IsolatedEnv, assert_ok, run_cmd, write_executable
from test_install_cli import footer_commands, prepare_cli_install


def test_post_install_prints_short_guide_hint(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    script = textwrap.dedent(
        r"""
        set -euo pipefail
        . "$1/tools/lib/env.sh"
        . "$1/tools/lib/install/post_install.sh"
        install_print_post_install "/opt/remote-ssh"
        """
    )
    result = run_cmd(["bash", "-c", script, "bash", repo_dir], env=isolated_env.env)

    assert_ok(result)
    output = result.stdout

    assert "Post-install setup:" in output
    assert "export PATH=" in output
    assert ':"$PATH"' in output
    assert "bash --rcfile /opt/remote-ssh/shell/rc.sh -i" in output
    assert f"{isolated_env.home}/.local/bin/remote-ssh guide post-install" in output
    assert "startup files were not modified" in output
    assert len(output.splitlines()) <= 10
    assert "Interactive usage" not in output
    assert "SSH configuration" not in output
    assert "VS Code Remote-SSH terminal profile" not in output
    assert "Optional Git and SSH setup" not in output


def test_post_install_renderer_renders_split_templates_in_order(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    write_executable(
        isolated_env.bin_dir / "hostname",
        """
        #!/usr/bin/env bash
        printf 'test-host.example\\n'
        """,
    )
    write_executable(
        isolated_env.bin_dir / "whoami",
        """
        #!/usr/bin/env bash
        printf 'shared-user\\n'
        """,
    )

    script = textwrap.dedent(
        r"""
        set -euo pipefail
        . "$1/tools/lib/env.sh"
        . "$1/tools/lib/install/post_install.sh"
        export SSH_CONNECTION="198.51.100.20 12345 203.0.113.10 22"
        install_render_post_install "/opt/remote-ssh"
        """
    )
    result = run_cmd(["bash", "-c", script, "bash", repo_dir], env=isolated_env.env)

    assert_ok(result)
    output = result.stdout

    assert output.index("Interactive usage") < output.index("SSH configuration")
    assert output.index("SSH configuration") < output.index("VS Code Remote-SSH terminal profile")
    assert output.index("VS Code Remote-SSH terminal profile") < output.index(
        "Optional Git and SSH setup"
    )
    assert "bash --rcfile /opt/remote-ssh/shell/rc.sh -i" in output
    assert "Host test-host.example" in output
    assert "HostName 203.0.113.10" in output
    assert "User shared-user" in output
    assert '"terminal.integrated.defaultProfile.linux": "bash + remote-ssh"' in output
    assert "git remote set-url origin git@github.com-myuser:OWNER/REPO.git" in output
    assert "@INSTALL_DIR@" not in output
    assert "@HOSTNAME@" not in output
    assert "@IP_ADDRESS@" not in output
    assert "@WHO_AM_I@" not in output


@pytest.mark.parametrize("path_present", [False, True, "alias"])
def test_footer_and_guide_commands_execute_without_path(
    repo_dir: Path, isolated_env: IsolatedEnv, runtime_bash: str, path_present: bool | str
) -> None:
    c = prepare_cli_install(repo_dir, isolated_env, runtime_bash)
    c.env["REMOTE_SSH_WELCOME"] = "0"
    if path_present == "alias":
        alias = c.home / "directory alias"
        alias.symlink_to(c.bin, target_is_directory=True)
        c.env["PATH"] = f"{alias}:{c.env['PATH']}"
    elif path_present:
        c.env["PATH"] = f"{c.bin}:{c.env['PATH']}"
    else:
        # A prefix/substring match is not a directory match.
        c.env["PATH"] = f"{c.bin}-different:{c.env['PATH']}"
    result = c.run("install", "--yes", "demo")
    assert_ok(result)
    guide, start, export = footer_commands(result.stdout)
    assert (export is None) == bool(path_present)
    if export:
        assert ':"$PATH"' in export
        assert c.env["PATH"] not in export
    interpreters = [[runtime_bash, "--noprofile", "--norc", "-c"]]
    if shutil.which("zsh"):
        interpreters.append([shutil.which("zsh") or "/bin/zsh", "-f", "-c"])
    for shell in interpreters:
        rendered = c.shell([*shell, guide])
        assert_ok(rendered)
        assert "Interactive usage" in rendered.stdout
        assert "@INTERACTIVE_COMMAND@" not in rendered.stdout
        interactive = next(
            line.strip() for line in rendered.stdout.splitlines() if "  bash --rcfile " in line
        )
        for command in (start, interactive):
            activation = c.shell(
                [
                    *shell,
                    command
                    + " -c "
                    + shlex.quote(
                        'test -n "$REMOTE_ENV_DIR" && alias rhelp >/dev/null && printf activation-ok'
                    ),
                ]
            )
            assert_ok(activation)
            assert "activation-ok" in activation.stdout
        if export:
            lookup = c.shell([*shell, export + "\ncommand -v remote-ssh"])
            assert_ok(lookup)
            assert lookup.stdout.strip() == str(c.command)
    assert not c.network.exists()
