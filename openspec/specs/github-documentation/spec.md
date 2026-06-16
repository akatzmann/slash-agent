# github-documentation Specification

## Purpose
TBD - created by archiving change add-github-documentation. Update Purpose after archive.
## Requirements
### Requirement: Architecture and Component Documentation
The documentation SHALL describe the three core components: Bash sourcing wrapper, Python controller, and PTY execution tool, explaining the complete execution lifecycle.

#### Scenario: Verification of component details
- **WHEN** the user reads the architecture section of `docs/documentation.md`
- **THEN** they find detailed descriptions of:
  - Sourcing `bin/agent-shell.sh` to inject the `/agent` wrapper function.
  - Sourcing temporary environment files to apply working directory updates (`cd`) and exports.
  - The Python entrypoint `agent_shell/main.py` configuring client and LLM agent contexts.

### Requirement: Scrollback and History Capture Documentation
The documentation SHALL detail the context extraction mechanism, explaining how context is retrieved dynamically.

#### Scenario: Context details verification
- **WHEN** the user reviews the context capture section of `docs/documentation.md`
- **THEN** they find specifications for:
  - Pane scrollback retrieval using `tmux capture-pane` (controlled by `AGENT_TMUX_LINES`, defaulting to 50 lines).
  - Terminal interactive history extraction fallback (controlled by `AGENT_HISTORY_COMMANDS`, defaulting to 20 commands).

### Requirement: Parent Shell Environment Sync Protocol Documentation
The documentation SHALL define the state synchronization protocol, explaining how the subprocess state is communicated back to the parent shell.

#### Scenario: Sync protocol details verification
- **WHEN** the user reviews the sync protocol section of `docs/documentation.md`
- **THEN** they find technical details explaining:
  - The use of the output separator token `___AGENT_SHELL_STATE___`.
  - Capturing PTY output, exit code, and `pwd`.
  - Capturing current environment variables via null-terminated byte sequences (`env -0`).
  - How environment delta commands are written to a temp file and evaluated in the host shell.

### Requirement: Interactive Steering and Configuration Options
The documentation SHALL list all interactive user steering actions (y/n/e/c) and CLI parameters (`-y/--yes`, `-n/--dry-run`), defining their operational outcomes.

#### Scenario: User steering verification
- **WHEN** the user inspects the interactive steering and flags section of `docs/documentation.md`
- **THEN** they find explanations for:
  - **`y` (yes):** Run the command inside PTY.
  - **`n` (no):** Refuse the command and inform the agent.
  - **`e` (edit):** Interactively edit the command string before execution.
  - **`c` (comment):** Input feedback text to steer the LLM agent's behavior.
  - **`-y`/`--yes`:** Automatically accept all commands without confirmation prompts.
  - **`-n`/`--dry-run`:** Simulate commands and report simulated successes.

