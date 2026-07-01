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
