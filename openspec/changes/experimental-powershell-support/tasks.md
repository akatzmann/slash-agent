## 1. Shell Integrations

- [x] 1.1 Implement native PowerShell wrapper script bin/slash-agent.ps1
- [x] 1.2 Implement native PowerShell installer script bin/installer.ps1

## 2. Python Orchestrator Updates

- [x] 2.1 Update slash_agent/tools.py to dynamically bypass POSIX imports on Windows
- [x] 2.2 Add run_command_windows function in slash_agent/tools.py to execute processes via Popen and stream real-time outputs on Windows
- [x] 2.3 Normalize file-sensitivity path comparisons to use forward-slashes and append Windows-specific sensitive files/directories in slash_agent/tools.py
- [x] 2.4 Add environment awareness dynamic metadata injection to system_prompt in slash_agent/main.py
- [x] 2.5 Support powershell shell-type in get_env_diff and state sync file serialization in slash_agent/main.py

## 3. Documentation & Verification

- [x] 3.1 Update README.md to describe Windows installation via PowerShell one-liner and documentation
- [x] 3.2 Verify installation, configuration, and execution flows in a simulated environment
- [x] 3.3 Fix cross-platform config path handling in bin/installer.ps1 ($HOME fallback and .env filename on Linux/macOS)
- [x] 3.4 Refine main.py system prompt environment awareness variables to distinguish between user interactive shell and subprocess execution shell on non-Windows environments
- [x] 3.5 Fix temp sync file naming in bin/slash-agent.ps1 to use .ps1 extension instead of .tmp
- [x] 3.6 Implement Windows raw character read fallback using msvcrt in slash_agent/tools.py
