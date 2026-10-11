import os
import subprocess
import tempfile
import pytest

from slash_agent.shell_init import (
    generate_init_script,
    detect_shell,
    resolve_shell_profile,
    install_init_hook,
    SUPPORTED_SHELLS,
)


def test_supported_shells():
    for shell in ["bash", "zsh", "fish", "ksh"]:
        assert shell in SUPPORTED_SHELLS


def test_generate_unsupported_shell():
    with pytest.raises(ValueError, match="Unsupported shell"):
        generate_init_script("tcsh")


def test_detect_shell():
    assert detect_shell({"SHELL": "/usr/bin/zsh"}) == "zsh"
    assert detect_shell({"SHELL": "/bin/fish"}) == "fish"
    assert detect_shell({"SHELL": "/bin/ksh"}) == "ksh"
    assert detect_shell({"SHELL": "/bin/bash"}) == "bash"
    assert detect_shell({"ZSH_VERSION": "5.9"}) == "zsh"
    assert detect_shell({}) == "bash"


def test_resolve_shell_profile(tmp_path):
    assert resolve_shell_profile("zsh", str(tmp_path), "Linux") == str(tmp_path / ".zshrc")
    assert resolve_shell_profile("fish", str(tmp_path), "Linux") == str(tmp_path / ".config" / "fish" / "config.fish")
    assert resolve_shell_profile("ksh", str(tmp_path), "Linux") == str(tmp_path / ".kshrc")
    assert resolve_shell_profile("bash", str(tmp_path), "Linux") == str(tmp_path / ".bashrc")
    
    # macOS bash with .bash_profile
    bash_prof = tmp_path / ".bash_profile"
    bash_prof.touch()
    assert resolve_shell_profile("bash", str(tmp_path), "Darwin") == str(bash_prof)


def test_install_init_hook_idempotent(tmp_path):
    # Test idempotent installation into .zshrc
    rc_file = tmp_path / ".zshrc"
    installed, path = install_init_hook("zsh", home_dir=str(tmp_path))
    assert installed is True
    assert path == str(rc_file)
    assert rc_file.exists()
    content = rc_file.read_text()
    assert "slash-agent init zsh" in content

    # Second run should be idempotent
    installed_again, _ = install_init_hook("zsh", home_dir=str(tmp_path))
    assert installed_again is False
    content_again = rc_file.read_text()
    assert content_again.count("slash-agent init zsh") == 1


def test_real_bash_execution():
    script = generate_init_script("bash", cmd_name="agent")
    cmd = ["bash", "-c", f'{script}\ntype /agent && type agent']
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"Bash execution failed: {res.stderr}"


def test_real_bash_custom_alias():
    script = generate_init_script("bash", cmd_name="myagent")
    cmd = ["bash", "-c", f'{script}\ntype /myagent && type myagent']
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"Bash custom alias failed: {res.stderr}"


def test_real_zsh_execution():
    script = generate_init_script("zsh", cmd_name="agent")
    cmd = ["zsh", "-f", "-c", f'{script}\nwhence /agent && whence agent']
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"Zsh execution failed: {res.stderr}"


def test_real_fish_execution():
    script = generate_init_script("fish", cmd_name="agent")
    cmd = ["fish", "-c", f'{script}\ntype agent']
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"Fish execution failed: {res.stderr}"


def test_real_mksh_execution():
    script = generate_init_script("ksh", cmd_name="agent")
    cmd = ["mksh", "-c", f'{script}\nwhence agent']
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"Mksh execution failed: {res.stderr}"


def test_cli_init_stdout():
    cmd = ["python3", "-m", "slash_agent.main", "init", "bash"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert "function /agent" in res.stdout
    assert "function agent" in res.stdout


def test_cli_init_custom_alias():
    cmd = ["python3", "-m", "slash_agent.main", "init", "bash", "--cmd", "foo"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert "function /foo" in res.stdout
    assert "function foo" in res.stdout


def test_cli_init_auto_detect():
    env = os.environ.copy()
    env["SHELL"] = "/bin/zsh"
    cmd = ["python3", "-m", "slash_agent.main", "init"]
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)
    assert res.returncode == 0
    assert "Integration (zsh)" in res.stdout


def test_cli_init_install(tmp_path):
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    cmd = ["python3", "-m", "slash_agent.main", "init", "bash", "--install"]
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)
    assert res.returncode == 0
    bashrc = tmp_path / ".bashrc"
    assert bashrc.exists()
    assert "slash-agent init bash" in bashrc.read_text()

