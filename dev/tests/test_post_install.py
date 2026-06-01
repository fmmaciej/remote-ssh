from __future__ import annotations

import textwrap
from pathlib import Path

from conftest import IsolatedEnv, assert_ok, run_cmd, write_executable


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
    assert "  run: remote-ssh guide post-install" in output
    assert "  includes SSH, VS Code Remote-SSH, Git, and interactive shell setup" in output
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
    assert output.index("VS Code Remote-SSH terminal profile") < output.index("Optional Git and SSH setup")
    assert 'bash --rcfile "/opt/remote-ssh/shell/rc.sh"' in output
    assert "Host test-host.example" in output
    assert "HostName 203.0.113.10" in output
    assert "User shared-user" in output
    assert '"terminal.integrated.defaultProfile.linux": "bash + remote-ssh"' in output
    assert "git remote set-url origin git@github.com-myuser:OWNER/REPO.git" in output
    assert "@INSTALL_DIR@" not in output
    assert "@HOSTNAME@" not in output
    assert "@IP_ADDRESS@" not in output
    assert "@WHO_AM_I@" not in output
