## ADDED Requirements

### Requirement: Native Shell Invocation
The system SHALL provide a sourceable script that defines a `/agent` command function in Bash. It MUST behave invisibly under normal shell operations and launch the Python agent orchestrator when called with prompt arguments.

#### Scenario: Sourcing and calling the agent
- **WHEN** the script `bin/agent-shell.sh` is sourced and the user executes `/agent "Create a directory"`
- **THEN** the shell function SHALL invoke the Python agent main orchestrator with the user prompt.

---

### Requirement: Context Capture
The system SHALL capture the terminal history of the active session. If a tmux session is active, it SHALL capture the terminal screen pane buffer. If tmux is not active, it SHALL capture the recent shell command history.

#### Scenario: Running inside tmux
- **WHEN** the user is inside an active tmux pane and runs `/agent "Fix the compile error"`
- **THEN** the command SHALL capture the last 50 lines of output from the current tmux pane and pass it to the Python agent orchestrator as context.

#### Scenario: Running outside tmux
- **WHEN** the user is outside tmux and runs `/agent "Fix the compile error"`
- **THEN** the command SHALL fall back to capturing the last 20 commands from the shell history and pass them to the Python agent orchestrator as context.

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
The system SHALL track changes to the current working directory (PWD) and environment variables during agent execution, and SHALL synchronize those changes back to the parent shell session when the agent exits.

#### Scenario: Navigating directories during agent execution
- **WHEN** the agent runs a command that changes PWD to `/notebooks/new_folder`
- **THEN** on agent exit, the parent shell SHALL execute `cd /notebooks/new_folder` to synchronize the directory.

---

### Requirement: Execution Flags and Dry-Run
The system SHALL support `-y` to skip all prompts and auto-confirm all commands, and `-n` / `--dry-run` to simulate command execution.

#### Scenario: Running in auto-confirm mode
- **WHEN** the user runs `/agent -y "Create directory foo"`
- **THEN** the system SHALL run all commands without prompting the user for confirmation.

#### Scenario: Running in dry-run mode
- **WHEN** the user runs `/agent -n "Create directory foo"`
- **THEN** the system SHALL output the commands it would run and simulate a successful response without actually executing them.
