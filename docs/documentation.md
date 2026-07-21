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
- `AGENT_BACKEND`: LLM backend engine. Supported options: `ollama` (default), `openai` (also used for local OpenAI-compatible APIs), `azure_openai`, `dummy`.
- `AGENT_MODEL`: Model name used by the LLM backend. Defaults to `gemma4:latest` for `ollama`, `gpt-5.4-nano` for `openai`, and `gpt-5.4-nano` for `azure_openai`. For local APIs, set to the GGUF filename (e.g. `gemma4-27b.gguf` for router mode) or alias.
- `AGENT_ENDPOINT`: Host base URL endpoint. Defaults: `http://127.0.0.1:11434` for `ollama`, official OpenAI API endpoint for `openai`. For local APIs, set to your local address (e.g. `http://127.0.0.1:8080/v1`).
- `OPENAI_API_KEY`: API key for the `openai` backend. (For local APIs, use a dummy placeholder string like `local-api-key`).
- `AZURE_OPENAI_API_KEY`: API key for the `azure_openai` backend.
- `AZURE_OPENAI_API_VERSION`: API version for the `azure_openai` backend (defaults to `2025-04-01-preview`).
- `AGENT_TMUX_LINES`: Lines captured from tmux scrollback (defaults to `50`).
- `AGENT_HISTORY_COMMANDS`: Number of commands captured from history fallback (defaults to `20`).
- `AGENT_THINKING_LEVEL`: Specifies the thinking/reasoning depth level. Valid options are `off` (default), `low`, `medium`, and `high`. Maps to `reasoning_effort` for OpenAI models and toggles thinking options (`think=True`) in Ollama backends (e.g., DeepSeek-R1).
- `AGENT_TEMPERATURE`: Float value specifying the LLM sampling temperature (e.g. `0.2`). Left blank or unset to use the model's/API's default temperature. Note: OpenAI's o-series reasoning models (such as `o1`/`o3`) do not support custom temperature.
- `AGENT_TOP_P`: Float value specifying the nucleus sampling probability threshold (e.g. `0.9`). Left blank or unset to use the model's/API's default value. Note: OpenAI's o-series reasoning models do not support custom `top_p`.
- `AGENT_READ_LINE_LIMIT`: Integer specifying the default maximum line count read by the `read_file` tool before truncation occurs (defaults to `800`).

### Visual Formatting of Reasoning Stream
When an agent is configured with a thinking level other than `"off"`, the LLM backend streams reasoning/thinking tokens before generating the final text response. `slash-agent` captures these events (`thinking_delta`) and formats them visually in the terminal:
1. **Header Block:** Preceded by a bold dark gray `[Thinking...]` header.
2. **Styled Output:** The reasoning stream is wrapped inside ANSI Dim and Italic escape codes (`\033[3;90m...\033[0m`) to distinguish it from standard response text.
3. **Response Transition:** As soon as the model finishes reasoning and starts outputting normal response text (`text_delta`), the style block is closed and a bold green `[Agent Response]` header is printed.

---

## 5. Local OpenAI-Compatible APIs (llama.cpp, vLLM, SGLang, Xinference)

Many modern local LLM runners expose an OpenAI-compatible `/v1/chat/completions` API. You can connect `slash-agent` to any of these engines by choosing the `OpenAI` backend and setting:
* `AGENT_ENDPOINT`: Pointing to your local server URL (must include the `/v1` suffix).
* `OPENAI_API_KEY`: Set to any non-empty dummy string (e.g., `local-api-key`) to satisfy SDK verification.
* `AGENT_MODEL`: Set to the specific model identifier or GGUF filename configured on your server.

### Provider Comparison Matrix
The table below lists the standard configuration parameters for popular local runners:

| Runner / Engine | Default API Port | Configuration Example (`AGENT_MODEL` / `model` param) | Special Notes |
| :--- | :--- | :--- | :--- |
| **llama.cpp** | `8080` | `gemma4-27b` (Single model mode)<br>`gemma4-27b.gguf` (Router mode) | If using Router mode (`--models-dir`), the parameter specifies the GGUF file to load. |
| **vLLM** | `8000` | `Qwen/Qwen2.5-Coder-7B-Instruct` | Must match the Hugging Face repo name passed to vLLM on startup. |
| **SGLang** | `30000` | `meta-llama/Llama-3-8B-Instruct` | Must match the model path configured on startup. |
| **Xinference** | `9997` | `gemma4-27b` | Must match the model registration UID on the Xinference server. |

### 🧠 Using Local Reasoning Models (e.g., DeepSeek-R1)
If you are running DeepSeek-R1 locally and notice raw `<think>...</think>` tags polluting the agent output or tools failing to parse because of thinking formatting, configure your server to disable or suppress reasoning tokens during standard completion calls (e.g., by launching your `llama-server` with the `--reasoning-budget 0` argument).

### WSL2 Host Network Integration

When running local LLM servers (like `llama.cpp` or `Ollama`) natively on your Windows host while executing `slash-agent` inside WSL2, network isolation prevents connection to `localhost`. You can bridge this boundary using one of two methods:

#### Method 1: Mirrored Networking
Shares the Windows host network stack directly with the WSL VM, enabling loopback communication.
1. Create or edit `%USERPROFILE%\.wslconfig` on your Windows host and add:
   ```ini
   [wsl2]
   networkingMode=mirrored
   ```
2. Restart WSL by running `wsl --shutdown` in Windows Command Prompt or PowerShell.
3. Configure `slash-agent` to connect to loopback (e.g., `http://localhost:8080/v1` for `llama.cpp` or `http://localhost:11434` for Ollama).
*Note: Requires Windows 11 (22H2+) and WSL 2.0.0+. Can conflict with corporate VPNs or local Kubernetes VM setups.*

#### Method 2: NAT Mode Routing (Fallback)
Allows communication through the virtual NAT switch interface.
1. Configure your Windows LLM server to listen on all interfaces (`0.0.0.0`) and ensure Windows Defender Firewall allows inbound traffic on its port (e.g., `8080` or `11434`).
2. Resolve the Windows host address dynamically inside your agent environment configuration (`~/.config/slash-agent/env`):
   ```bash
   export AGENT_ENDPOINT="http://$(ip route show | grep default | awk '{print $3}'):8080/v1"
   ```
*Note: Works universally on all Windows and WSL setups, but exposes the LLM server to your local network.*

---

## 6. Installation Options

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

---

## 7. Background Task Execution

To support persistent operations (e.g. local dev servers, continuous linters, or parallel executions), `slash-agent` provides non-blocking, asynchronous execution capabilities mapped to a stateful registry.

### Spawning Asynchronous Processes
When executing a command, the agent can pass the parameter `background=True` to bypass the interactive pseudo-terminal (PTY) loop.
* **Process Spawning:** The task is spawned using `subprocess.Popen` in non-blocking mode.
* **Logging:** The stdout and stderr are redirected to a volatile log file inside `tempfile.gettempdir() + "/slash-agent/tasks/task_<id>.log"`. The file is created with restricted `0o600` owner-only permissions.
* **Registry Mapping:** The task metadata and the Popen instance are saved inside `session_state.active_tasks` mapping to a unique task ID (e.g., `task_1`, `task_2`).

### Task Management Tools
The agent controls background tasks using four dedicated tools:
1. **`list_background_tasks`**: Returns a formatted list of all active background tasks, their command strings, start times, and execution statuses.
2. **`get_task_logs(task_id, tail_lines)`**: Reads the volatile task log file on disk and returns the trailing lines to the agent for inspection.
3. **`kill_background_task(task_id)`**: Forcefully terminates the process group statefully and purges it from the registry.
4. **`wait_seconds(seconds)`**: Pauses execution statefully using `asyncio.sleep` to let background tasks complete without prompt gating.

### Cross-Platform Cleanup Guarantees (Orphan Prevention)
To ensure that background tasks do not become orphaned daemons when the agent session ends, the system deploys three layers of termination hooks:
1. **Orchestrator `finally` / `atexit` Cleanup:** An exit handler reaps all active processes.
2. **POSIX Process Groups:** On macOS and Linux, processes are spawned in separate process groups using `os.setpgrp()`. During teardown, the system signals the entire process group (`os.killpg`) using `SIGTERM` followed by a forceful `SIGKILL` if still running after a grace period.
3. **Linux/WSL2 `prctl` Binding:** On Linux hosts (and WSL2), the runner sets `prctl(PR_SET_PDEATHSIG, SIGTERM)` on the child process. The OS kernel reaps the process group automatically if the parent Python orchestrator dies abruptly (e.g., via `SIGKILL`).
4. **Windows Job Objects:** On Windows hosts, the runner uses `win32job` to assign child processes to a parent-bound Job Object configured with `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`. The OS propagates termination immediately when the parent process handle is closed.

