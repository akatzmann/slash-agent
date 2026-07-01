## Why

Currently, slash-agent only supports Unix-like shell environments (Bash, Zsh, Ksh, Fish) and relies on POSIX-specific APIs (such as `pty`, `termios`, `tty`, `fcntl`). Windows users are forced to use WSL2. This change introduces native PowerShell support on Windows and cross-platform PowerShell Core on Linux/macOS, removing the WSL2 hard dependency and expanding the target audience.

## What Changes

- Add a new native PowerShell installer (`bin/installer.ps1`) to check prerequisites, clone/update the repository, set up `.venv`, configure backend variables, and handle `$PROFILE` registration.
- Add a new native PowerShell wrapper (`bin/slash-agent.ps1`) to capture console history, invoke the python orchestrator, and source environment updates.
- Modify the python orchestrator (`slash_agent/tools.py`) to run commands on Windows using a thread-based, non-interactive `subprocess.Popen` bridge, bypassing Unix-only `pty` / `termios` modules.
- Modify the prompt and env sync generation (`slash_agent/main.py`) to dynamically prepend OS/shell environment awareness to the system prompt and output PowerShell-compatible environment/location variables.

## Capabilities

### New Capabilities

*(None)*

### Modified Capabilities

- `simple-installer`: Modify specification to support automated verification, installation, configuration, and profile registration using PowerShell on Windows.
- `shell-agent`: Modify specification to support native shell invocation, context capture, and environment/directory state synchronization under PowerShell.

## Impact

- **New files**: `bin/installer.ps1`, `bin/slash-agent.ps1`
- **Modified files**: `slash_agent/tools.py`, `slash_agent/main.py`, `README.md`
- **Dependencies**: No new external Python packages are introduced; standard library modules (`subprocess`, `threading`, `platform`) are used.
