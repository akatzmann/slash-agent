## ADDED Requirements

### Requirement: PowerShell Native Wrapper Sourcing
The wrapper script `bin/slash-agent.ps1` SHALL define `agent` and `/agent` command functions when dot-sourced within a PowerShell or PowerShell Core session.

#### Scenario: Sourcing slash-agent.ps1 in PowerShell
- **WHEN** the user sources `bin/slash-agent.ps1` in a PowerShell session
- **THEN** it exposes the `agent` and `/agent` commands and displays an active integration message.

### Requirement: PowerShell Context Capture
When running the agent in PowerShell, the system SHALL extract the last 20 commands of session history from the PSReadLine history file, falling back to the standard `Get-History` stream if the PSReadLine module or history file is unavailable.

#### Scenario: Extracting PSReadLine history
- **WHEN** the user executes `/agent` in a PowerShell session with PSReadLine active
- **THEN** the wrapper reads the tail of the file defined by `(Get-PSReadLineOption).HistorySavePath` and passes it to the python orchestrator.

### Requirement: Cross-Platform Subprocess Execution
On Windows systems, the python orchestrator SHALL execute commands via a thread-based, non-interactive `subprocess.Popen` runner using `powershell.exe` (or `pwsh` if available) as the shell, capturing stdout/stderr and streaming output in real-time.

#### Scenario: Running a command on Windows
- **WHEN** the agent tool executes `git status` on Windows
- **THEN** it runs the command under `powershell.exe` or `pwsh`, displaying output to the user in real-time and capturing the log output for the agent.

### Requirement: Subprocess Execution State Extraction on Windows
During execution on Windows, the subprocess runner SHALL append statements to output a standardized state block on stdout. The block MUST contain a state token (`___AGENT_SHELL_STATE___`), the command's exit code, the final working directory, and all environment variables formatted in a parseable layout.

#### Scenario: Executing command with state extraction
- **WHEN** the command completes under the Windows subprocess runner
- **THEN** it outputs `___AGENT_SHELL_STATE___`, the final exit code, the absolute path of the working directory, and the environment variables separated by a null byte `\x00` or a parseable delimiter.

### Requirement: PowerShell Host State Synchronization
When running in a PowerShell host session, the python orchestrator SHALL output PowerShell-compatible state synchronization statements to `$SYNC_FILE` (using `$env:KEY = 'value'` for environment variables and `Set-Location -LiteralPath` for directory changes), which the wrapper sources on exit.

#### Scenario: State synchronization in PowerShell
- **WHEN** the agent changes the active directory and sets environment variables, then exits
- **THEN** the parent PowerShell session executes the statements in the sync file to update its active PWD and environment variables.

### Requirement: System Prompt Environment Awareness
The python orchestrator SHALL prepend OS name, active shell, path separator, and working directory metadata to the system prompt to ensure the LLM structures file paths and CLI commands matching the host environment.

#### Scenario: Running the orchestrator on Windows PowerShell
- **WHEN** the agent is initialized on Windows PowerShell
- **THEN** the system prompt is prepended with `Operating System: Windows`, `Active Shell: powershell`, `Path Separator: '\'`, and the current working directory, instructing the model to format paths and commands accordingly.
