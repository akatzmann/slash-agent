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
