# github-documentation Specification

## Purpose
Provides technical documentation and guide resources outlining slash-agent architecture, configuration parameters, and platforms compatibility guidelines.
## Requirements
### Requirement: Architecture and Component Documentation
The documentation SHALL describe the core components: the POSIX shell sourcing wrapper (supporting Bash, Zsh, Ksh), the Fish sourcing wrapper, the Python controller, and the PTY execution tool, explaining the complete execution lifecycle.

#### Scenario: Verification of component details
- **WHEN** the user reads the architecture section of `docs/documentation.md`
- **THEN** they find detailed descriptions of:
  - Sourcing `bin/slash-agent.sh` to inject the `/agent` wrapper function for Bash/Zsh/Ksh.
  - Sourcing `bin/slash-agent.fish` to inject the `/agent` wrapper function for Fish.
  - Sourcing temporary environment files to apply working directory updates (`cd`) and exports (utilizing standard Bourne export/unset or Fish-specific set commands).
  - The Python entrypoint `slash_agent/main.py` configuring client, backend, and LLM agent contexts.

---

### Requirement: Scrollback and History Capture Documentation
The documentation SHALL detail the context extraction mechanism, explaining how context is retrieved dynamically.

#### Scenario: Context details verification
- **WHEN** the user reviews the context capture section of `docs/documentation.md`
- **THEN** they find specifications for:
  - Pane scrollback retrieval using `tmux capture-pane` (controlled by `AGENT_TMUX_LINES`, defaulting to 50 lines).
  - Terminal interactive history extraction fallback (controlled by `AGENT_HISTORY_COMMANDS`, defaulting to 20 commands).

---

### Requirement: Parent Shell Environment Sync Protocol Documentation
The documentation SHALL define the state synchronization protocol, explaining how the subprocess state is communicated back to the parent shell.

#### Scenario: Sync protocol details verification
- **WHEN** the user reviews the sync protocol section of `docs/documentation.md`
- **THEN** they find technical details explaining:
  - The use of the output separator token `___AGENT_SHELL_STATE___`.
  - Capturing PTY output, exit code, and `pwd`.
  - Capturing current environment variables via null-terminated byte sequences (`env -0`).
  - How environment delta commands are written to a temp file and evaluated in the host shell.

---

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

---

### Requirement: Windows Compatibility Documentation
The documentation SHALL specify the compatibility requirements for Windows users, guiding them to use WSL2 (Windows Subsystem for Linux) as the supported environment.

#### Scenario: Windows developer reads compatibility guide
- **WHEN** a Windows developer checks the compatibility or installation section in `README.md`
- **THEN** they find clear documentation instructing them to use WSL2 (Ubuntu/Debian) to install and run the agent natively.

---

### Requirement: WSL2 Host Network Integration Documentation
The documentation SHALL provide clear, concise guidelines for connecting `slash-agent` inside WSL2 to local LLM servers (like `llama.cpp` or `Ollama`) on the Windows host, documenting both Mirrored Networking and NAT Mode routing configurations.

#### Scenario: Windows developer reads about Mirrored Networking and NAT Mode configuration
- **WHEN** a developer checks the WSL2 host network integration guidelines in the technical documentation
- **THEN** they find:
  - Concise steps to configure Mirrored Networking (`networkingMode=mirrored`) inside `.wslconfig`.
  - A fallback configuration for NAT Mode routing using dynamic IP route resolution (`ip route show...`).
  - Security warnings explaining the implications of binding Windows-hosted LLM runners to `0.0.0.0`.

---

### Requirement: Documentation for Thinking Mode and Re-configuration
The system documentation MUST include detailed instructions for configuring, using, and updating the agent's thinking level and running the re-configuration wizard. Additionally, all references to configuration parameters in `README.md` and `docs/documentation.md` SHALL guide the user to find and edit their settings in their XDG-standard user configuration directory (e.g. `~/.config/slash-agent/env`), explaining how custom path overrides (`SLASH_AGENT_CONFIG_FILE`) and fallback defaults operate.

#### Scenario: User reviews updated README.md or docs/documentation.md
- **WHEN** the user reads `README.md` or `docs/documentation.md`
- **THEN** they find:
  - Explanations of `AGENT_THINKING_LEVEL` and how different levels map to backend implementations (OpenAI reasoning effort, Ollama think parameters).
  - Explanations and visual examples of the live reasoning stream formatting in the terminal.
  - Instructions on using `/agent --configure` or `/agent -c` to update their local settings, endpoints, and variables interactively.
  - Explicit guidance pointing them to their user configuration file located at `~/.config/slash-agent/env` (or custom overrides) instead of the repository root `.env`.

---

### Requirement: Project Positioning and Feature Comparison Documentation
The documentation and README files SHALL include project positioning context, defining what the tool is and is not, explaining privacy-first advantages (including BYOK and offline local-only configurations), and providing a comparative matrix showing how slash-agent compares to Standard Web UIs, Shell Copilots, and Project Agents.

#### Scenario: Developer reviews project positioning in README
- **WHEN** the user reads `README.md`
- **THEN** they find:
  - An opt-in AI Seed Prompt block (`[!TIP]`) enabling AI pair programmers to audit and summarize slash-agent positioning.
  - "The 10-Second Reality Check" specifying what slash-agent is and what it is not.
  - "The Privacy-First Advantage" detailing Bring Your Own Keys (BYOK) and local offline Ollama support.
  - "Feature Comparison Matrix" comparing standard Web UIs, Shell Copilots, Project Agents, and slash-agent.

#### Scenario: Developer reviews comparison details in Technical Documentation
- **WHEN** the user reads `docs/documentation.md`
- **THEN** they find the Feature Comparison Matrix integrated near the top of the file to establish architectural positioning.

---

### Requirement: Community Governance and Contribution Documentation
The repository MUST provide comprehensive contributor documentation (`CONTRIBUTING.md`), code of conduct standards (`CODE_OF_CONDUCT.md`), and security vulnerability reporting procedures (`SECURITY.md`).

#### Scenario: Contributor reviews community documentation
- **WHEN** a contributor visits the repository on GitHub or locally inspects repository governance files
- **THEN** they find clear setup steps in `CONTRIBUTING.md`, community behavior standards in `CODE_OF_CONDUCT.md`, and private vulnerability reporting instructions to `@akatzmann` in `SECURITY.md`.

---

### Requirement: GitHub Issue Forms for Bugs and Features
The repository MUST provide structured GitHub issue templates (`.github/ISSUE_TEMPLATE/bug_report.yml` and `.github/ISSUE_TEMPLATE/feature_request.yml`) to capture detailed reports.

#### Scenario: User submits a bug report via GitHub
- **WHEN** a user opens a new issue using the bug report template
- **THEN** the form prompts them for detailed environment info including Shell Type (Bash/Zsh/Fish/tmux) and LLM Backend (Ollama/OpenAI/Azure OpenAI).
