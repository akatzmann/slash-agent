## MODIFIED Requirements

### Requirement: Native Shell Invocation
The system SHALL provide sourceable scripts that define a `/agent` command function in Bash, Zsh, Ksh, and Fish. It MUST behave invisibly under normal shell operations and launch the Python agent orchestrator when called with prompt arguments.

#### Scenario: Sourcing and calling the agent in Zsh
- **WHEN** the script `bin/slash-agent.sh` is sourced in Zsh and the user executes `/agent "Create a directory"`
- **THEN** the shell function SHALL resolve the script path dynamically using Zsh syntax and invoke the Python agent main orchestrator with the user prompt.

#### Scenario: Sourcing and calling the agent in Fish
- **WHEN** the script `bin/slash-agent.fish` is sourced in Fish and the user executes `/agent "Create a directory"`
- **THEN** the Fish function SHALL resolve the script path dynamically using Fish syntax and invoke the Python agent main orchestrator with the user prompt.

---

### Requirement: Context Capture
The system SHALL capture the terminal history of the active session. If a tmux session is active, it SHALL capture the terminal screen pane buffer. If tmux is not active, it SHALL capture the recent shell command history using the command history capture mechanism of the active shell (Bash, Zsh, Ksh, or Fish).

#### Scenario: Running outside tmux in Zsh
- **WHEN** the user is outside tmux in a Zsh session and runs `/agent "Fix compile error"`
- **THEN** the command SHALL capture the last 20 commands from Zsh history using `fc -ln` and pass them to the Python agent orchestrator as context.

#### Scenario: Running outside tmux in Fish
- **WHEN** the user is outside tmux in a Fish session and runs `/agent "Fix compile error"`
- **THEN** the command SHALL capture the last 20 commands from Fish history using `history` and pass them to the Python agent orchestrator as context.

---

### Requirement: Environment and Directory State Sync
The system SHALL track changes to the current working directory (PWD) and environment variables during agent execution, and SHALL synchronize those changes back to the parent shell session in a syntax compatible with the active shell (POSIX-compatible export/unset for Bash/Zsh/Ksh, or set -gx/set -e for Fish) when the agent exits.

#### Scenario: Sourcing state sync commands in Fish
- **WHEN** the agent runs under Fish and exits after modifying environment variables and PWD
- **THEN** the Python orchestrator writes Fish-compatible variable and location commands to the sync file, and the Fish wrapper sources them back to the active session.
