## Context

The workspace `/notebooks/2026-06-16_AgentShell` is currently empty. We want to implement a native shell agent addon. We will leverage the existing `py_agent_core` orchestrator package located under `/notebooks/2026-05-28_PyAgentCore/` by adding its directory to `PYTHONPATH` and executing our script using the virtualenv Python binary at `/notebooks/2026-05-28_PyAgentCore/.venv/bin/python3`.

## Goals / Non-Goals

**Goals:**
- Provide a sourceable Bash script (`bin/agent-shell.sh`) that sets up `/agent`.
- Capture tmux pane outputs (using `tmux capture-pane`) or Bash command history and feed it to the agent.
- Implement an interactive PTY bridge in Python to execute commands so password prompts (e.g. `sudo`) and interactive programs work natively.
- Clean ANSI escape sequences and carriage returns from subprocess outputs before they are added to the LLM agent transcript.
- Implement state synchronization (such as working directory `cd` and custom env changes) from the agent subprocess back to the parent shell.
- Support options: `-y` (auto-confirm) and `-n`/`--dry-run` (simulate run without execution).
- Implement interactive confirmation prompt supporting `[y]es / [n]o / [e]dit / [c]omment`.

**Non-Goals:**
- Support shells other than Bash in the initial version (e.g., Zsh, Fish).
- Modify the user's primary shell prompt or add hooks that intercept standard, non-agent shell commands (standard shell behaviour must remain completely unaffected).
- Support background persistent subshells that hold long-running processes across separate `/agent` invocations.

## Decisions

### Decision 1: Command execution via stateless subshell with environment tracking
- **Design choice:** The python tool executes commands by starting a shell subprocess. To preserve directory (`cd`) and environment changes, the tool maintains `cwd` and `env_vars` in memory. Each command runs as `cd {cwd} && {command}`, followed by a state capture command:
  ```bash
  _exit_code=$?
  echo "___AGENT_SHELL_STATE___"
  echo "exit_code=$_exit_code"
  echo "pwd=$(pwd)"
  env -0
  ```
- **Rationale:** Spawning a single, long-running persistent interactive bash subprocess in the background and sending lines to it (via pexpect/pty) is notoriously difficult to synchronize, parse, and protect against hangs. A stateless wrapper is simple, robust, and deterministic.
- **Alternatives considered:** Keeping a persistent background subshell open and writing commands to its stdin (rejected due to synchronization fragility).

### Decision 2: Pseudo-Terminal (PTY) bridging for execution
- **Design choice:** Commands are executed inside a dynamically allocated pseudo-terminal (PTY) using Python's `pty` module and a selector-based copy loop. Stdin is forwarded directly from the parent TTY, and stdout/stderr are written back to `sys.stdout` while being copied to an in-memory buffer. Additionally, the PTY's columns and rows are synchronized with the parent terminal size using `os.get_terminal_size()`.
- **Rationale:** Standard subprocess pipe redirection breaks `sudo` and other interactive password/confirmation inputs. A PTY bridge makes the subprocess believe it is running in a real interactive terminal, enabling native password prompts. Synchronizing terminal size guarantees that output layouts (like columnar lists or interactive menus) render correctly.
- **Alternatives considered:** Direct execution with pipe redirection (breaks interactive commands); piping password via stdin using `sudo -S` (unsafe, security hazard, and only works for sudo).

### Decision 3: Directory and Env synchronization using a sync file
- **Design choice:** The parent Bash function `/agent` creates a temporary file (`mktemp`) and passes its path to Python via `--sync-file`. When the Python agent finishes, it writes bash synchronization commands (e.g. `cd "/notebooks/folder"`) to this file. The parent Bash function sources this file on exit and deletes it.
- **Rationale:** A child process cannot modify its parent process's environment. Sourcing a temporary command file is a clean, standard Unix mechanism.
- **Alternatives considered:** Printing synchronization commands to stdout (would pollute the console and interfere with user-facing messages).

### Decision 4: ANSI stripping on captured outputs
- **Design choice:** We strip ANSI color and formatting escape codes from the captured terminal output and subprocess output before feeding them to the LLM agent.
- **Rationale:** ANSI sequences bloat the LLM's prompt window, waste tokens, and degrade the quality of code/error analyses.

## Risks / Trade-offs

- **[Risk] Subprocess hangs on unexpected prompt:** If the PTY runs a command that asks an unexpected question and does not receive input, the process may hang.
  - *Mitigation:* The Python PTY bridge intercepts `Ctrl+C` inputs from the user, forwards `SIGINT` to the child process group to kill the active command, and returns control gracefully to the agent loop.
- **[Risk] Command execution in dry-run mode:** The LLM may think commands succeeded and act on false assumptions.
  - *Mitigation:* In dry-run mode, the tool mocks output saying `[Dry-run] Command succeeded` and does not run any PTY process. We instruct the system prompt to expect mock outputs in dry-run mode.
- **[Risk] Capturing sensitive information (passwords):** Passwords typed into `sudo` could potentially be captured in the output buffer.
  - *Mitigation:* When `sudo` prompts for a password, it disables terminal echo. Because the password is not printed back to stdout, the PTY read buffer does not capture the password characters.
