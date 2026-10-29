def test_remote_ssh_guide_supports_post_install_section(
    repo_dir: Path,
    isolated_env: IsolatedEnv,
) -> None:
    result = run_remote_ssh(repo_dir, ["guide", "post-install"], env=isolated_env.env)

    assert_ok(result)
    output = result.stdout
    assert "Interactive usage" in output
    assert "SSH configuration" in output
    assert "VS Code Remote-SSH terminal profile" in output
    assert "Optional Git and SSH setup" in output
    commands = [
        line.strip() for line in output.splitlines() if line.strip().startswith("bash --rcfile ")
    ]
    assert len(commands) == 1
    capture_env = {
        key: value for key, value in isolated_env.env.items() if key not in ("BASH_ENV", "ENV")
    }
    captured = run_cmd(
        [
            "bash",
            "--noprofile",
            "--norc",
            "-c",
            r"""bash() { printf '%s\0' "$@"; }
"""
            + commands[0],
        ],
        env=capture_env,
    )
    assert_ok(captured)
    assert captured.stdout == "--rcfile\0" + str(repo_dir / "shell/rc.sh") + "\0-i\0"
    assert '"terminal.integrated.defaultProfile.linux": "bash + remote-ssh"' in output
    assert "Commands" not in output
    assert "@INSTALL_DIR@" not in output
    assert "@INTERACTIVE_COMMAND@" not in output
