## 1. Core Package Implementation

- [x] 1.1 Create the `agent_shell` package structure with `__init__.py` and `tools.py`
- [x] 1.2 Implement the interactive PTY execution bridge that forwards stdin/stdout to the terminal while capturing output in a buffer
- [x] 1.3 Add ANSI escape code and carriage return stripping utilities for LLM input normalization
- [x] 1.4 Implement the tool confirmation prompt supporting `[y]es / [n]o / [e]dit / [c]omment` and dry-run simulation mode
- [x] 1.5 Create `agent_shell/main.py` which sets up the `py_agent_core` orchestrator with the Ollama backend and local tools
- [x] 1.6 Implement environment state sync file writer in Python to output commands for parent shell synchronization on exit
- [x] 1.7 Sync the PTY bridge terminal size (rows and columns) with the parent terminal dynamically
- [x] 1.8 Handle SIGINT (Ctrl+C) to terminate only the active PTY subprocess group while preserving the parent agent execution loop

## 2. Shell Integration & CLI Setup

- [x] 2.1 Create the sourceable Bash script `bin/agent-shell.sh` defining the `/agent` function
- [x] 2.2 Implement tmux pane capture (`tmux capture-pane`) and Bash history fallback retrieval inside the shell function
- [x] 2.3 Write temporary file handling in the shell function for passing captured context to Python and sourcing synchronization commands back to the shell

## 3. Verification & Documentation

- [x] 3.1 Create `README.md` with configuration guides and instructions on sourcing `bin/agent-shell.sh`
- [x] 3.2 Verify the tool runs correctly and processes commands using a local LLM model
- [x] 3.3 Verify interactive password prompt handling using `sudo` inside the `/agent` loop
- [x] 3.4 Verify environment state synchronization (e.g. `cd` updates) changes the parent shell directory correctly on exit
- [x] 3.5 Verify that the dry-run `-n` and auto-confirm `-y` flags function as specified
