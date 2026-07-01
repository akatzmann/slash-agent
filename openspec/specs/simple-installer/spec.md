# simple-installer Specification

## Purpose
Automates the installation, dependency management, configuration, and shell-integration setup of slash-agent across multiple supported shells and environments.
## Requirements
### Requirement: Automated Prerequisites Verification
The installer script SHALL verify the presence of `git`, `python3`, and a working virtual environment builder (`venv` or `virtualenv`) on the host system, exiting with a non-zero code if any are missing. If the virtual environment builder is missing, the installer SHALL detect the host package manager and print a platform-specific command to install it.

#### Scenario: Missing git on target host
- **WHEN** git is not found in the executable PATH
- **THEN** the installer exits with exit code 1 and prints an error message.

#### Scenario: Missing virtual environment builder with apt-get available
- **WHEN** python3 -m venv and virtualenv fail to create a virtual environment, and apt-get is available
- **THEN** the installer exits with exit code 1 and suggests `sudo apt install python3-venv` or `pip install virtualenv`.

#### Scenario: Missing virtual environment builder with dnf available
- **WHEN** python3 -m venv and virtualenv fail to create a virtual environment, and dnf is available
- **THEN** the installer exits with exit code 1 and suggests `sudo dnf install python3-virtualenv` or `pip install virtualenv`.

#### Scenario: Missing virtual environment builder with pacman available
- **WHEN** python3 -m venv and virtualenv fail to create a virtual environment, and pacman is available
- **THEN** the installer exits with exit code 1 and suggests `sudo pacman -S python-virtualenv` or `pip install virtualenv`.

#### Scenario: Missing virtual environment builder with apk available
- **WHEN** python3 -m venv and virtualenv fail to create a virtual environment, and apk is available
- **THEN** the installer exits with exit code 1 and suggests `sudo apk add py3-virtualenv` or `pip install virtualenv`.

#### Scenario: Missing virtual environment builder with brew available on macOS
- **WHEN** python3 -m venv and virtualenv fail to create a virtual environment, brew is available, and the system is macOS
- **THEN** the installer exits with exit code 1 and suggests `brew install python` or `pip install virtualenv`.

---

### Requirement: Repository Cloning and Setup
The installer script SHALL clone the codebase from the project repository to a local installation folder. This folder SHALL default to `~/.slash-agent` (originally `~/.agent-shell`), but can be overridden using the environment variable `INSTALL_DIR`.

#### Scenario: Cloning to a custom target directory
- **WHEN** the installer runs and `INSTALL_DIR` is set to a custom path
- **THEN** it clones the repository to that custom path.

#### Scenario: Updating an existing installation directory
- **WHEN** the installer runs and the target installation directory already exists
- **THEN** it performs a safe update from the repository (e.g. `git pull`), prints an updating status message instead of a fresh install message, and continues successfully.

---

### Requirement: Virtual Environment and Dependency Setup
The installer script SHALL initialize a Python 3 virtual environment in the installation directory and install requirements using pip.

#### Scenario: Python dependencies installation
- **WHEN** the virtual environment is set up
- **THEN** pip is invoked to install all python packages specified in `requirements.txt`.

---

### Requirement: Configuration Preservation and Setup
The installer script SHALL configure the environment settings by creating or preserving the environment configuration file in the user's standard configuration directory (defaulting to `~/.config/slash-agent/env` or `$XDG_CONFIG_HOME/slash-agent/env` with secure `600` permissions). If the configuration file already exists, it SHALL preserve the existing configuration instead of overwriting it. Additionally, if the configuration file already exists but is missing the `AGENT_TEMPERATURE` and `AGENT_TOP_P` parameters, the installer script SHALL automatically append them as empty placeholder values to ensure backward compatibility.

#### Scenario: Running installer for the first time
- **WHEN** the installer is executed and no configuration file exists in the user's config directory
- **THEN** it prompts the user or probes the environment to create a new configuration file with secure `600` file permissions, writing empty placeholders for `AGENT_TEMPERATURE` and `AGENT_TOP_P`.

#### Scenario: Rerunning installer on an existing installation
- **WHEN** the installer is executed and a configuration file already exists in the user's config directory
- **THEN** it keeps the existing configuration file and does not overwrite it or prompt for existing fields.

#### Scenario: Migrating legacy configuration file
- **WHEN** the installer or agent runs, and a legacy `.env` file exists in the installation/repository root but no configuration file exists in the user's config directory
- **THEN** it SHALL load the legacy configuration, write it to the new configuration directory with secure `600` permissions, and remove or clear the legacy `.env` file to prevent plaintext secret exposure in the repository.

#### Scenario: Installer appends missing temperature and top_p placeholders to existing config
- **WHEN** the installer runs and an existing configuration file does not contain the keys `AGENT_TEMPERATURE` or `AGENT_TOP_P`
- **THEN** it appends them as empty string placeholders (e.g., `AGENT_TEMPERATURE=""` and `AGENT_TOP_P=""`) to the configuration file without prompting the user.

---

### Requirement: Idempotent Shell Profile Registration
The installer script SHALL append the sourcing statement for `bin/slash-agent.sh` (or `bin/slash-agent.fish` for Fish) to the user's appropriate shell profile file based on their active login shell and operating system. It SHALL check if the sourcing statement is already present to prevent duplicate entries.

#### Scenario: Installer runs in Zsh on macOS
- **WHEN** the installer runs on a macOS system and the user's login shell is Zsh
- **THEN** the installer appends the sourcing statement for `bin/slash-agent.sh` to `~/.zshrc` if not already present.

#### Scenario: Installer runs in Bash on macOS
- **WHEN** the installer runs on a macOS system and the user's login shell is Bash
- **THEN** the installer appends the sourcing statement for `bin/slash-agent.sh` to `~/.bash_profile` (or `~/.profile`) if not already present.

#### Scenario: Installer runs in Fish on Linux
- **WHEN** the installer runs on a Linux system and the user's login shell is Fish
- **THEN** the installer appends the sourcing statement for `bin/slash-agent.fish` to `~/.config/fish/config.fish` if not already present.

#### Scenario: Duplicate registration prevention
- **WHEN** the installer runs on a system where the appropriate shell profile already has the sourcing statement
- **THEN** it does not append duplicate lines to the profile.

---

### Requirement: Support Configure-Only Mode with Pre-populated Defaults
The installer script MUST support running with a `--configure` or `-c` flag. In this mode, the installer SHALL bypass setup checks and repository cloning, load existing configuration variables from the configuration file if available, and prompt the user to configure their settings, using the existing configurations as default choices.

The configuration wizard MUST support configuring OpenAI, Ollama, Azure OpenAI, Local OpenAI-Compatible APIs (such as llama.cpp, vLLM, SGLang, Xinference), and Dummy backends. When configuring a Local OpenAI-Compatible API:
1. The wizard SHALL prompt for a local API base URL, defaulting to `http://127.0.0.1:8080/v1` (llama.cpp default) or the existing configured endpoint.
2. If the user-supplied endpoint URL is missing the `/v1` suffix path, the wizard SHALL automatically append `/v1` to standardize base URL routing for the client.
3. The wizard SHALL attempt to query the `/v1/models` endpoint of the active service. If the server is online, it SHALL display the currently loaded models in a numbered list for user selection. If offline or no models are returned, it SHALL prompt the user to type a model alias manually, defaulting to `gemma4-27b`.
4. If no custom API key is present in the environment or configuration, the wizard SHALL default the `OPENAI_API_KEY` to `local-api-key` to bypass standard client SDK checks.

#### Scenario: Running configuration on an already installed setup
- **WHEN** the installer is invoked with the `--configure` or `-c` flag and the configuration file exists in the user's config directory
- **THEN** it skips virtual environment setup, clones, and prerequisite checks, loads existing configurations, uses them as defaults in interactive prompts, and writes updated values to the configuration file with secure `600` permissions.

#### Scenario: Configuring Local OpenAI API with endpoint suffix sanitization
- **WHEN** the user selects the Local OpenAI API option and enters `http://127.0.0.1:8000` (without `/v1`)
- **THEN** the wizard automatically sanitizes the URL to `http://127.0.0.1:8000/v1` before saving.

#### Scenario: Configuring Local OpenAI API with active model probing
- **WHEN** the user selects the Local OpenAI API option and the local server is online exposing active models
- **THEN** the wizard fetches the loaded models via the `/v1/models` API endpoint and presents them as numbered options for the user to select.

### Requirement: Configuration of Agent Thinking Level
The installer script MUST prompt the user for their desired thinking level during configuration and save it.

#### Scenario: User chooses a thinking level in the installer
- **WHEN** the user selects a thinking level (off, low, medium, or high) in the installer prompts
- **THEN** the value is stored in `.env` under the variable name `AGENT_THINKING_LEVEL`.

---

### Requirement: Local Probe Proxy Bypass
During the automated prerequisite check and configuration phase, the installer script SHALL bypass any configured system proxies when probing local service endpoints (specifically when checking Ollama models via `127.0.0.1:11434` or local OpenAI-compatible API models via local addresses).

#### Scenario: Probing local Ollama behind a proxy
- **WHEN** the installer is executed in an environment with `http_proxy` configured and attempts to fetch Ollama models from `http://127.0.0.1:11434`
- **THEN** it SHALL bypass all proxy handlers, query the local Ollama instance directly, and retrieve the model list successfully.

#### Scenario: Probing local OpenAI API behind a proxy
- **WHEN** the installer is executed in an environment with `http_proxy` configured and attempts to fetch local models from `http://127.0.0.1:8080/v1/models`
- **THEN** it SHALL bypass all proxy handlers, query the local API instance directly, and retrieve the model list successfully.

