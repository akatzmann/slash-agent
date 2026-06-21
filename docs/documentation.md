# slash-agent Technical Documentation

This document describes the design, architecture, internal communication protocol, and operational commands of slash-agent.

---

## Feature Comparison Matrix

The following matrix compares `slash-agent` against standard Web UIs, traditional shell copilots, and full-repository project agents to highlight its specific operational scope:

| Capability | 🌐 Standard Web UI <br> (ChatGPT / Claude) | 💻 Shell Copilots <br> (Copilot CLI / Gh-Cli) | 🧰 Project Agents <br> (Aider / Claude Code) | ⚡ slash-agent |
| :--- | :--- | :--- | :--- | :--- |
| **🧠 How it Gets Context** | ⌨️ Manual copy-paste | 📝 You type a prompt | 📂 Reads entire git repo | 🖥️ Scrapes active terminal scrollback |
| **🚀 Idle System Overhead** | 🚫 None (Browser) | 🚫 None (On-Demand) | ⚠️ High (Heavy runtimes) | ⚡ Zero (Dormant shell function) |
| **🛠️ Command Execution** | ❌ None (Read-only) | 🔄 Prints text to run | 🤖 Autonomous file edits | 🤝 Interactive PTY Loop (Run/Edit/Steer) |
| **🔗 Parent Shell Sync** | ❌ No | ❌ No | ❌ No | ✅ Yes (`cd` & `export` persist) |
| **🔒 Local Privacy Support** | ❌ No (Cloud only) | ❌ No (Cloud only) | ✅ Yes (Configurable) | ✅ Yes (Full Ollama/Local support) |
| **🎯 Primary Superpower** | Abstract logic & algorithmic brainstorming | Quick syntax lookups <br> (e.g., *"how to untar file"*) | Large autonomous feature builds & massive refactors | Instant post-crash fixes & rapid terminal adjustments |

---

## 1. System Architecture & Lifecycle

The integration consists of core components working in sequence depending on your shell:

```
[ Active POSIX Session (Bash/Zsh/Ksh) ]           [ Active Fish Session ]
         │                                                  │
         ▼ (Type `/agent <task>`)                           ▼ (Type `agent <task>`)
[ POSIX Wrapper (bin/slash-agent.sh) ]            [ Fish Wrapper (bin/slash-agent.fish) ]
         │                                                  │
         └─────────────────────────┬────────────────────────┘
                                   │ (Captures tmux pane or history)
                                   ▼ 
           [ Python Orchestrator (slash_agent/main.py) ] ──► Interfaces with Backend
                                   │
                                   ▼ (For each tool execution)
           [ PTY Bridge (slash_agent/tools.py) ] ──────────► Subprocess in interactive PTY
                                   │
                                   ▼ (Captures exit code, PWD, and env deltas)
           [ State Sync Protocol ] ────────────────────────► Writes shell commands to temp file
                                   │
                                   ▼ (On termination, parent shell sources sync file)
[ Active Session (Updated State) ]
```

### Execution Lifecycle:
1. **Sourcing Hooks:** Sourcing `bin/slash-agent.sh` (or `bin/slash-agent.fish` for Fish) registers the agent command function in the active session.
2. **Context Collection:** The wrapper gathers active terminal outputs and invokes the Python orchestrator, passing paths to temporary files for context and state synchronization, along with the `--shell` flag indicating the parent shell context.
3. **Agent Loop & Client Initialization:** The Python entrypoint `slash_agent/main.py` parses arguments (including the active shell parameter), configures environment settings, sets up the LLM agent client, and starts the task stream with the configured LLM backend.
4. **Interactive Command Execution:** When the agent decides to execute a shell command, it invokes the PTY execution bridge which requests user permission and streams input/output in raw mode.
5. **Parent Shell Updates:** After execution finishes, env variables and working directory transitions are written out as shell-compatible statements (POSIX export/unset or Fish-specific set commands) to a temp sync file. The parent shell wrapper sources this file on exit, applying the changes directly to the host shell session.

---

## 2. Dynamic Context Capture

To provide the LLM agent with precise context (such as compiler errors, crash logs, or directory listings), the tool automatically captures recent terminal console screen outputs:

* **tmux Pane Scrollback (Preferred):** If the user is running inside a `tmux` session, the wrapper extracts the scrollback buffer of the active pane.
  - **Environment Variable:** `AGENT_TMUX_LINES`
  - **Default Value:** `50` lines
  - **Command:** `tmux capture-pane -p -S -<lines>`
* **Interactive Command History (Fallback):** If tmux is not detected, the wrapper extracts recent user commands using the history utility of the active shell:
  - **Bash/Ksh**: Uses `history <lines>` (temporarily enabling interactive history).
  - **Zsh**: Uses `fc -ln -<lines>` (retrieving history commands without line numbers).
  - **Fish**: Uses `history | head -n <lines>`.
  - **Environment Variable:** `AGENT_HISTORY_COMMANDS`
  - **Default Value:** `20` commands

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
   - **For POSIX Shells (Bash, Zsh, Ksh)**:
     - Directory change: `cd "/new/path"`
     - Additions/updates: `export KEY=VALUE`
     - Removals: `unset KEY`
   - **For Fish Shell**:
     - Directory change: `cd "/new/path"`
     - Additions/updates: `set -gx KEY VALUE`
     - Removals: `set -e KEY`
4. **Parent Sourcing:** The parent shell wrapper sources this temporary file on script exit, applying all transitions statefully.

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
- **`-c`, `--configure` (Re-configuration):** Launches the interactive configuration wizard, allowing you to easily adjust backend, model, endpoint, keys, and thinking level settings. (This flag is intercepted at the shell-wrapper level).

### Command Safety Risk Levels
Before prompting the user (or deciding to auto-confirm), the system evaluates the safety category of every proposed command:
- **`Safe`** (Green): Informational actions (e.g. `git status`, `pwd`). `risk_description` is optional.
- **`Low`** (Cyan): Safe configuration changes (e.g. `git add`, `python -m venv`). `risk_description` is optional.
- **`Moderate`** (Yellow): Changes to files or setup state (e.g. `git commit`, `npm install`). Requires a `risk_description` explaining potential risks.
- **`Critical`** (Red): Destructive file operations, administrative commands, or remote scripts (e.g. `rm -rf`, `sudo`). Requires a `risk_description` and always forces manual confirmation unless overridden by `--unsafe-yes`.

### Configuration Environment Variables
Configure these variables in your configuration file (defaulting to `~/.config/slash-agent/env`), shell profile, or `~/.bashrc`. You can also override the default configuration path by setting the `SLASH_AGENT_CONFIG_FILE` environment variable.
- `AGENT_BACKEND`: LLM backend engine. Supported options: `ollama` (default), `openai`, `azure_openai`, `dummy`.
- `AGENT_MODEL`: Model name used by the LLM backend. Defaults to `gemma4:latest` for `ollama`, `gpt-5.4-nano` for `openai`, and `gpt-5.4-nano` for `azure_openai`.
- `AGENT_ENDPOINT`: Host base URL endpoint. Defaults: `http://127.0.0.1:11434` for `ollama`, official OpenAI API endpoint for `openai`.
- `OPENAI_API_KEY`: API key for the `openai` backend.
- `AZURE_OPENAI_API_KEY`: API key for the `azure_openai` backend.
- `AZURE_OPENAI_API_VERSION`: API version for the `azure_openai` backend (defaults to `2025-04-01-preview`).
- `AGENT_TMUX_LINES`: Lines captured from tmux scrollback (defaults to `50`).
- `AGENT_HISTORY_COMMANDS`: Number of commands captured from history fallback (defaults to `20`).
- `AGENT_THINKING_LEVEL`: Specifies the thinking/reasoning depth level. Valid options are `off` (default), `low`, `medium`, and `high`. Maps to `reasoning_effort` for OpenAI models and toggles thinking options (`think=True`) in Ollama backends (e.g., DeepSeek-R1).

### Visual Formatting of Reasoning Stream
When an agent is configured with a thinking level other than `"off"`, the LLM backend streams reasoning/thinking tokens before generating the final text response. `slash-agent` captures these events (`thinking_delta`) and formats them visually in the terminal:
1. **Header Block:** Preceded by a bold dark gray `[Thinking...]` header.
2. **Styled Output:** The reasoning stream is wrapped inside ANSI Dim and Italic escape codes (`\033[3;90m...\033[0m`) to distinguish it from standard response text.
3. **Response Transition:** As soon as the model finishes reasoning and starts outputting normal response text (`text_delta`), the style block is closed and a bold green `[Agent Response]` header is printed.

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

