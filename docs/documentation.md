# slash-agent Technical Documentation

This document describes the design, architecture, internal communication protocol, and operational commands of slash-agent.

---

## 1. System Architecture & Lifecycle

The integration consists of three primary components working in sequence:

```
[ Active Bash Session ]
        │
        ▼ (Type `/agent <task>`)
[ Bash Sourcing Wrapper (bin/slash-agent.sh) ] ──► Captures Terminal Screen (tmux pane or history)
        │
        ▼ (Launches python controller with context)
[ Python Orchestrator (slash_agent/main.py) ] ──► Interfaces with Configured Backend (Agent client loop)
        │
        ▼ (For each tool execution)
[ PTY Bridge (slash_agent/tools.py) ] ──────────► Executes subprocess command in interactive PTY
        │
        ▼ (Captures exit code, PWD, and env deltas)
[ State Sync Protocol ] ────────────────────────► Writes parent shell commands to temp file
        │
        ▼ (On termination, parent shell sources sync file)
[ Active Bash Session (Updated State) ]
```

### Execution Lifecycle:
1. **Sourcing Hooks:** Sourcing `bin/slash-agent.sh` injects the `/agent` command function into the current active Bash environment.
2. **Context Collection:** The wrapper gathers active terminal outputs and invokes the Python orchestrator, passing paths to temporary files for context and state synchronization.
3. **Agent Loop & Client Initialization:** The Python entrypoint `slash_agent/main.py` parses arguments, configures environment settings, sets up the LLM agent client, and starts the task stream with the configured LLM backend (OpenAI, Ollama, Azure OpenAI, or Dummy).
4. **Interactive Command Execution:** When the agent decides to execute a shell command, it invokes the PTY execution bridge which requests user permission and streams input/output in raw mode.
5. **Parent Shell Updates:** After execution finishes, env variables and working directory transitions are written out as Bash statements to a temp sync file. The wrapper sources this file on termination, applying the changes directly to the host shell session.

---

## 2. Dynamic Context Capture

To provide the LLM agent with precise context (such as compiler errors, crash logs, or directory listings), the tool automatically captures recent terminal console screen outputs:

* **tmux Pane Scrollback (Preferred):** If the user is running inside a `tmux` session, the wrapper extracts the scrollback buffer of the active pane.
  - **Environment Variable:** `AGENT_TMUX_LINES`
  - **Default Value:** `50` lines
  - **Command:** `tmux capture-pane -p -S -<lines>`
* **Interactive Command History (Fallback):** If tmux is not detected, the wrapper temporarily enables local history options and extracts recent user commands.
  - **Environment Variable:** `AGENT_HISTORY_COMMANDS`
  - **Default Value:** `20` commands
  - **Command:** `history <lines>`

---

## 3. Parent Shell State Synchronization Protocol

Because standard Python processes cannot modify the environment or working directory of their parent shell, the agent synchronizes states using a custom boundary communication protocol:

### Subprocess Output Injection
The command running inside the PTY is appended with a special marker token `___AGENT_SHELL_STATE___` and state query commands:
```bash
<original_command>; _exit_code=$?; echo ""; echo "___AGENT_SHELL_STATE___"; echo "exit_code=$_exit_code"; echo "pwd=$(pwd)"; env -0
```

### Data Parsing
1. **Output Separation:** The PTY bridge intercepts stdout and stops writing to the screen as soon as it matches the `___AGENT_SHELL_STATE___` token.
2. **State Updates:** It reads the exit code, extracts the final path of `pwd` to update the agent's virtual `cwd`, and parses the environment variables (serialized as null-terminated strings via `env -0`).
3. **Environment Deltas:** On termination, `main.py` performs a diff between the initial shell environment variables and the final session variables, writing commands to a temporary file:
   - For working directory updates: `cd "/new/path"`
   - For environment additions/updates: `export KEY=VALUE`
   - For environment deletions: `unset KEY`
4. **Parent Sourcing:** The parent shell sources this temporary file on wrapper script exit, applying all transitions statefully.

---

## 4. Interactive Steering & Configuration Options

Users have full, real-time control over what commands are executed on their system.

### Interactive Prompts
Before executing any proposed command, the agent pauses and asks:
```
Confirm action: [y]es / [n]o / [e]dit / [c]omment ?
```
- **`y` (yes):** Executes the command inside the raw pseudo-terminal (PTY) immediately.
- **`n` (no):** Refuses execution. The agent is notified that the user rejected the command.
- **`e` (edit):** Restores terminal inputs and prompts the user to edit the command string before running it.
- **`c` (comment):** Allows the user to provide text feedback (e.g., *"No, use node 18"*), which is sent back to the LLM agent to guide its next steps.

### Command-line Parameters
- **`-y`, `--yes` (Auto-confirm):** Skips the confirmation prompt and executes commands automatically. Note: This will **not** auto-confirm commands flagged with a `critical` risk level (e.g. `rm -rf`, `sudo`).
- **`--unsafe-yes` (Unsafe Auto-confirm):** Auto-confirms all commands, bypassing prompts even for `critical` risk operations.
- **`-n`, `--dry-run` (Simulation):** Simulates a successful execution (Exit code 0, mock output) without making changes to the system.

### Command Safety Risk Levels
Before prompting the user (or deciding to auto-confirm), the system evaluates the safety category of every proposed command:
- **`Safe`** (Green): Informational actions (e.g. `git status`, `pwd`). `risk_description` is optional.
- **`Low`** (Cyan): Safe configuration changes (e.g. `git add`, `python -m venv`). `risk_description` is optional.
- **`Moderate`** (Yellow): Changes to files or setup state (e.g. `git commit`, `npm install`). Requires a `risk_description` explaining potential risks.
- **`Critical`** (Red): Destructive file operations, administrative commands, or remote scripts (e.g. `rm -rf`, `sudo`). Requires a `risk_description` and always forces manual confirmation unless overridden by `--unsafe-yes`.

### Configuration Environment Variables
Configure these variables in your `.env` file, shell profile, or `~/.bashrc`:
- `AGENT_BACKEND`: LLM backend engine. Supported options: `openai` (default), `ollama`, `azure_openai`, `dummy`.
- `AGENT_MODEL`: Model name used by the LLM backend. Defaults to `gpt-4o-mini` for `openai`, `gemma4:e4b-it-qat` for `ollama`, and `gpt-4o` for `azure_openai`.
- `AGENT_ENDPOINT`: Host base URL endpoint. Defaults: official OpenAI API endpoint for `openai`, `http://127.0.0.1:11434` for `ollama`.
- `OPENAI_API_KEY`: API key for the default `openai` backend.
- `AZURE_OPENAI_API_KEY`: API key for the `azure_openai` backend.
- `AZURE_OPENAI_API_VERSION`: API version for the `azure_openai` backend (defaults to `2024-02-15-preview`).
- `AGENT_TMUX_LINES`: Lines captured from tmux scrollback (defaults to `50`).
- `AGENT_HISTORY_COMMANDS`: Number of commands captured from history fallback (defaults to `20`).

---

## 5. Installation Options

### Method 1: Single-Command Quick Installer
The quickest way to get started is by streaming the installer script from GitHub directly into bash:
```bash
curl -fsSL https://raw.githubusercontent.com/akatzmann/slash-agent/master/bin/installer.sh | bash
```
**What this script does:**
1. Verifies the presence of requirements `git`, `python3`, and virtual environment capabilities (`venv` or `virtualenv`).
2. Clones the repository to `~/.slash-agent` (customizable via `INSTALL_DIR` environment variable).
3. Creates a local Python virtual environment (`.venv`) and installs the dependencies from `requirements.txt`.
4. Idempotently adds the sourcing hook statement (`source ~/.slash-agent/bin/slash-agent.sh`) to the end of `~/.bashrc`.

### Method 2: Manual Installation
For users who want to review every step manually:
1. **Clone the repository** to your preferred local directory.
2. **Install requirements:** Ensure you have the python dependencies (including `py-agent-core` from GitHub) installed in your active Python environment:
   ```bash
   pip install -r requirements.txt
   ```
3. **Register wrapper:** Register the bash shell wrapper in your `~/.bashrc`:
   ```bash
   source /path/to/slash-agent/bin/slash-agent.sh
   ```

