# shell-agent Specification

## Purpose
Provides an interactive terminal command-execution environment powered by an LLM agent, utilizing PTY-bridged subprocess execution, contextual tmux/history parsing, and shell state synchronization.
## Requirements
### Requirement: Native Shell Invocation
The system SHALL provide sourceable scripts that define a `/agent` command function in Bash, Zsh, Ksh, and Fish. It MUST behave invisibly under normal shell operations and launch the Python agent orchestrator when called with prompt arguments.

#### Scenario: Sourcing and calling the agent in Zsh
- **WHEN** the script `bin/slash-agent.sh` is sourced in Zsh and the user executes `/agent "Create a directory"`
- **THEN** the shell function SHALL resolve the script path dynamically using Zsh syntax and invoke the Python agent main orchestrator with the user prompt.

#### Scenario: Sourcing and calling the agent in Fish
- **WHEN** the script `bin/slash-agent.fish` is sourced in Fish and the user executes `/agent "Create a directory"`
- **THEN** the Fish function SHALL resolve the script path dynamically using Fish syntax and invoke the Python agent main orchestrator with the user prompt.

#### Scenario: Sourcing and calling the agent in Bash
- **WHEN** the script `bin/slash-agent.sh` is sourced and the user executes `/agent "Create a directory"`
- **THEN** the shell function SHALL invoke the Python agent main orchestrator with the user prompt.

---

### Requirement: Context Capture
The system SHALL capture the terminal history of the active session. If a tmux session is active, it SHALL capture the terminal screen pane buffer. If tmux is not active, it SHALL capture the recent shell command history using the command history capture mechanism of the active shell (Bash, Zsh, Ksh, or Fish).

#### Scenario: Running inside tmux
- **WHEN** the user is inside an active tmux pane and runs `/agent "Fix the compile error"`
- **THEN** the command SHALL capture the last 50 lines of output from the current tmux pane and pass it to the Python agent orchestrator as context.

#### Scenario: Running outside tmux in Zsh
- **WHEN** the user is outside tmux in a Zsh session and runs `/agent "Fix compile error"`
- **THEN** the command SHALL capture the last 20 commands from Zsh history using `fc -ln` and pass them to the Python agent orchestrator as context.

#### Scenario: Running outside tmux in Fish
- **WHEN** the user is outside tmux in a Fish session and runs `/agent "Fix compile error"`
- **THEN** the command SHALL capture the last 20 commands from Fish history using `history` and pass them to the Python agent orchestrator as context.

#### Scenario: Running outside tmux in Bash
- **WHEN** the user is outside tmux in a Bash session and runs `/agent "Fix compile error"`
- **THEN** the command SHALL fall back to capturing the last 20 commands from the shell history using `history` and pass them to the Python agent orchestrator as context.

---

### Requirement: Interactive Command Confirmation
The system SHALL prompt the user for confirmation before executing any command proposed by the LLM agent. The prompt SHALL support options to accept (`y`), reject (`n`), edit (`e`), or comment/feedback (`c`).

#### Scenario: Accepting the proposed command
- **WHEN** the agent proposes a command `npm install` and the user inputs `y` at the prompt
- **THEN** the system SHALL execute the command.

#### Scenario: Editing the proposed command
- **WHEN** the agent proposes a command `npm install` and the user inputs `e` at the prompt
- **THEN** the system SHALL prompt the user to input an edited command, and execute the edited command.

#### Scenario: Commenting on the proposed command
- **WHEN** the agent proposes a command `npm install` and the user inputs `c` and provides comment "Use yarn instead"
- **THEN** the system SHALL skip execution and return the comment "Command rejected by user: Use yarn instead" to the LLM agent.

---

### Requirement: Interactive Command Execution via PTY Bridge
The system SHALL execute the approved commands inside a pseudo-terminal (PTY) bridge. It SHALL pipe the user's stdin directly to the child process and stdout/stderr back to the terminal natively, while capturing the output buffer and stripping all ANSI escape codes before passing the result to the LLM agent.

#### Scenario: Running an interactive sudo command
- **WHEN** the system executes `sudo apt install htop` inside the PTY bridge
- **THEN** the PTY bridge SHALL allow the user to see the password prompt, type their password interactively, and capture the text output of the installation without ANSI colors.

---

### Requirement: Environment and Directory State Sync
The system SHALL track changes to the current working directory (PWD) and environment variables during agent execution, and SHALL synchronize those changes back to the parent shell session in a syntax compatible with the active shell (POSIX-compatible export/unset for Bash/Zsh/Ksh, or set -gx/set -e for Fish) when the agent exits.

#### Scenario: Navigating directories during agent execution
- **WHEN** the agent runs a command that changes PWD to `/path/to/new_folder`
- **THEN** on agent exit, the parent shell SHALL execute `cd "/path/to/new_folder"` to synchronize the directory.

#### Scenario: Sourcing state sync commands in Fish
- **WHEN** the agent runs under Fish and exits after modifying environment variables and PWD
- **THEN** the Python orchestrator writes Fish-compatible variable and location commands to the sync file, and the Fish wrapper sources them back to the active session.

---

### Requirement: Execution Flags and Dry-Run
The system SHALL support `-y` to skip all prompts and auto-confirm all commands, and `-n` / `--dry-run` to simulate command execution.

#### Scenario: Running in auto-confirm mode
- **WHEN** the user runs `/agent -y "Create directory foo"`
- **THEN** the system SHALL run all commands without prompting the user for confirmation.

#### Scenario: Running in dry-run mode
- **WHEN** the user runs `/agent -n "Create directory foo"`
- **THEN** the system SHALL output the commands it would run and simulate a successful response without actually executing them.

---

### Requirement: Proxy Environment Normalization and Sync
The system SHALL normalize, sanitize, and bidirectionally synchronize proxy environment variables (`HTTP_PROXY`/`http_proxy`, `HTTPS_PROXY`/`https_proxy`, `NO_PROXY`/`no_proxy`) at startup. It MUST:
1. Ensure both lowercase (Linux-preferred) and uppercase (Python-preferred) variations of each variable have identical values.
2. Strip shell-style wildcards (e.g., `*` or `*.`) from `NO_PROXY`/`no_proxy` values for compatibility with HTTP clients (e.g. `httpx`).
3. Automatically append default local bypasses (`localhost`, `127.0.0.1`) to `NO_PROXY`/`no_proxy` if any HTTP/HTTPS proxy is configured.
4. Ensure the sanitized environment is fully loaded before initializing any agent core systems and propagated statefully to PTY subprocess command executions.

#### Scenario: Sanitizing wildcards and adding local bypasses
- **WHEN** the agent starts and `HTTP_PROXY` is set to `http://proxy.example.com` and `no_proxy` is set to `*.local,10.0.0.1`
- **THEN** the system SHALL update `os.environ` and `session_state.env_vars` so that both `no_proxy` and `NO_PROXY` contain `local,10.0.0.1,localhost,127.0.0.1` and both `HTTP_PROXY` and `http_proxy` contain `http://proxy.example.com`.

### Requirement: Initial Working Directory Recording
Upon agent startup in `slash_agent/main.py`, the system SHALL record `session_state.initial_cwd = os.getcwd()` to serve as the immutable workspace boundary anchor.

#### Scenario: Startup records initial working directory
- **WHEN** `slash-agent` is initialized
- **THEN** `session_state.initial_cwd` stores the current working directory path at launch time

### Requirement: Tool Registration Order
In `slash_agent/main.py`, the tools array supplied to `Agent` SHALL register native file tools (`read_file`, `write_file`, `edit_file`) before `execute_command`.

#### Scenario: Tool schemas ordered with native tools first
- **WHEN** `Agent` is instantiated in `main.py`
- **THEN** `read_file`, `write_file`, and `edit_file` are positioned at indices prior to `execute_command`

### Requirement: Central Event Streaming Handlers
The main async event loop in `main.py` SHALL handle `tool_execution_start` and `tool_execution_end` events from `agent.prompt_stream()` to render formatted terminal output badges for all tools.

#### Scenario: Central loop intercepts tool events
- **WHEN** any tool execution event fires during prompt streaming
- **THEN** `main.py` formats and prints the appropriate start badge and completion status directly to stdout

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
The python orchestrator SHALL prepend OS name, user's interactive shell, command execution shell, path separator, and working directory metadata to the system prompt to ensure the LLM structures file paths and CLI commands matching the host environment and target execution subshell.

#### Scenario: Running the orchestrator on Windows PowerShell
- **WHEN** the agent is initialized on Windows PowerShell
- **THEN** the system prompt is prepended with metadata specifying `Operating System: Windows`, `User's Interactive Shell: powershell`, `Command Execution Shell: PowerShell`, `Path Separator: '\'`, and the current working directory, instructing the model to format paths and commands for PowerShell.

#### Scenario: Running the orchestrator on Linux PowerShell Core (pwsh)
- **WHEN** the agent is initialized on Linux PowerShell Core
- **THEN** the system prompt is prepended with metadata specifying `Operating System: Linux`, `User's Interactive Shell: pwsh`, `Command Execution Shell: bash`, `Path Separator: '/'`, and the current working directory, instructing the model to format paths and commands for bash.

### Requirement: PowerShell Sync File Extension
To prevent Windows from opening an external file handler when dot-sourcing the environment state synchronization commands, the synchronization file generated by the wrapper script MUST have a `.ps1` file extension.

#### Scenario: Running sync file on Windows PowerShell
- **WHEN** the agent finishes execution under PowerShell on Windows
- **THEN** the temporary sync file (e.g. `tmpXXXX.ps1`) is dot-sourced without launching any external file association dialogue or editor.

### Requirement: Windows Raw Character Read Fallback
When running on Windows, the system SHALL read keyboard input for confirmation prompts using Windows-native console APIs (specifically Python's standard `msvcrt` module) to avoid dependencies on Unix `termios`.

#### Scenario: Spawning confirmation prompt on Windows
- **WHEN** a confirmation prompt is displayed on Windows
- **THEN** the system reads a single character using `msvcrt.getwch()` and acts on it without throwing `NameError: name 'termios' is not defined`.

### Requirement: Environment Variable Key Sanitization
The system SHALL filter out empty environment variable keys and keys starting with `=` during process execution output parsing and parent shell state synchronization generation.

#### Scenario: Execution in environment containing internal Windows drive variables
- **WHEN** process environment output parsing or shell environment diff generation executes
- **THEN** internal drive variables (such as `=C:`) and empty key strings are ignored and excluded from generated shell sync scripts.

