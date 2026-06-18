# ⚡ slash-agent: Native LLM Copilot for Your Terminal

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Shell: Bash](https://img.shields.io/badge/Shell-Bash-green.svg)](https://www.gnu.org/software/bash/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-orange.svg)](http://makeapullrequest.com)

**slash-agent** is an ultra-lightweight, zero-overhead AI coding partner that integrates natively into your active Bash shell.

> [!IMPORTANT]
> **No Daemons. Zero Idle Memory. 100% On-Demand.**
> slash-agent consumes **zero CPU and zero RAM** when you aren't using it. It remains completely inactive until you call `/agent`. It then instantly captures your terminal state (active tmux scrollback or command history fallback) to diagnose compiler failures, write files, and execute fixes—automatically syncing directories (`cd`) and environment exports back to your parent shell session.

---


## 🌟 Key Features

* **🔌 Zero-Overhead Integration:** Completely passive. Consumes zero CPU/memory until you run `/agent`—no running background daemons, cron jobs, or log listeners.
* **🔍 Context-Aware Diagnoses:** Instantly extracts the last 50 lines of your active `tmux` pane or terminal history, letting the LLM read error outputs and tracebacks without manual copy-pasting.
* **⚡ State Synchronization:** Working directory transitions (`cd`) and environment exports (`export KEY=VAL`) made by the agent automatically sync back to your parent shell session on exit.
* **🌉 Interactive PTY Bridge:** Executes proposed commands in a pseudo-terminal (PTY), allowing you to interactively type passwords (e.g. `sudo`), view colored output, and see progress bars.
* **🕹️ Steerable Confirmation Loop:** Full control over every action:
  * **`y` (yes):** Run the command.
  * **`n` (no):** Refuse the command and inform the agent.
  * **`e` (edit):** Inline edit the command before running it.
  * **`c` (comment):** Type natural language guidance back to the agent (e.g. *"Use yarn instead of npm"*).
* **🛡️ Dry-run & Auto-confirm Modes:** Preview agent actions safely with `-n` / `--dry-run`, or run fully unattended with `-y` / `--yes`.

---

## 🎬 See it in Action

```
$ npm run build
❌ ERROR: Build failed. Cannot find module 'dotenv' in server.js:12

$ /agent Fix this
[Agent Shell] Initializing with model 'gemma4:e4b-it-qat' at 'http://127.0.0.1:11434'...
[Agent Started Task]
Analyzing terminal context... Identified missing dependency 'dotenv' in server.js.

[Agent] Proposed Command:
  $ npm install dotenv && npm run build

Confirm action: [y]es / [n]o / [e]dit / [c]omment ? y
[Agent Running]: npm install dotenv && npm run build
...
added 1 package, and audited 120 packages in 1s
✓ Build completed successfully!

I have installed the missing 'dotenv' package and verified that the build now passes.
```

---

## 🚀 Installation

### Method 1: Single-Command Quick Installer (Recommended)

Get up and running in seconds. Stream the installer directly to your shell:
```bash
curl -fsSL https://raw.githubusercontent.com/akatzmann/slash-agent/master/bin/installer.sh | bash
```
*(This automatically clones the repo to `~/.slash-agent`, configures a Python virtual environment, installs Python packages, and registers the shell helper in your `~/.bashrc`.)*

### Method 2: Manual Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/akatzmann/slash-agent.git ~/.slash-agent
   cd ~/.slash-agent
   ```
2. **Install Python Requirements:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Register Shell Integration:**
   Add this line to your `~/.bashrc`:
   ```bash
   source ~/.slash-agent/bin/slash-agent.sh
   ```

---

## ⚙️ Configuration

Configure the LLM backend, endpoint, model, and capture settings in your `.env` file or shell profile:

```bash
# LLM Backend: openai (default), ollama, azure_openai, dummy
export AGENT_BACKEND="openai"

# Model name (Defaults: gpt-4o-mini for openai, gemma4:e4b-it-qat for ollama)
export AGENT_MODEL="gpt-4o-mini"

# API endpoint base URL (defaults to official OpenAI API endpoint)
export AGENT_ENDPOINT=""

# OpenAI API Key (required for default OpenAI backend)
export OPENAI_API_KEY="your-api-key-here"

# Context extraction settings
export AGENT_TMUX_LINES=50          # Lines captured from active tmux scrollback
export AGENT_HISTORY_COMMANDS=20    # Commands captured from history fallback
```

For a full list of configuration variables (e.g., Azure OpenAI variables), see the [.env.template](.env.template) file.

---

## 🛠️ Usage Examples

### 1. General Command Execution
```bash
/agent create a new directory named 'sandbox' and write a basic python flask server inside it
```

### 2. Post-Crash Diagnosis
If a compiler, build tool, or script crashes, run `/agent` with no arguments (or a request to fix it):
```bash
/agent Fix this crash
```

### 3. Dry-run Mode
Simulate proposed steps and check the agent's plan without making actual system changes:
```bash
/agent -n setup a docker compose file for PostgreSQL and Redis
```

### 4. Auto-confirm Mode
Run tasks without any confirmation prompts for safe, low, or moderate risk commands:
```bash
/agent -y update package lists and install tree
```

### 5. Auto-confirm Critical Commands
By default, critical commands (like `rm -rf` or commands using `sudo`) are not auto-confirmed by `-y` to prevent accidental damage. To auto-confirm even critical commands, pass the `--unsafe-yes` flag:
```bash
/agent --unsafe-yes clean up docker volumes and system cache
```

---

## 📘 Deep Dive

For more technical details on the architecture, the interactive PTY bridge loop, and the environment state-synchronization protocol, read the [Technical Documentation](docs/documentation.md).
