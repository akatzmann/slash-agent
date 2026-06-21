## Context

In the current version of the system, LLM backend configurations and API keys are stored in a plaintext `.env` file located at the repository/installation root. This exposes secrets to user grep searches or recursive indexing engines. Moving the configuration to a secure user-specific folder outside code projects solves this issue completely.

## Goals / Non-Goals

**Goals:**
* Move the active configuration file to a secure, user-owned configuration path (`~/.config/slash-agent/env` by default, or respecting `$XDG_CONFIG_HOME`).
* Lock file permissions on the config file to `600` (read/write only by owner) to prevent unauthorized local read.
* Maintain complete backwards compatibility by migrating existing `.env` files automatically upon first run or installation run.
* Erase or delete the old `.env` file in the repo root once migrated successfully to prevent future leaks.

**Non-Goals:**
* Implementing cryptographic encryption (e.g. keyring or symmetric encryption) which is out of scope and undesirable due to portability/SSH constraints.
* Modifying the shell functions in `slash-agent.sh` / `slash-agent.fish` (which remain unchanged as they only execute python).

## Decisions

### Decision 1: Directory Path Resolution and Custom Override
We will support XDG specifications on Linux and macOS, with a fallback to `~/.config/slash-agent/env`. Additionally, users can override the configuration path via the environment variable `SLASH_AGENT_CONFIG_FILE`.

* **Rationale**: This is standard CLI convention (similar to `gh`, `npm`, etc.) and allows portability overrides.
* **Implementation (Python)**:
  ```python
  def get_config_path() -> str:
      custom_path = os.environ.get("SLASH_AGENT_CONFIG_FILE")
      if custom_path:
          return os.path.abspath(custom_path)
          
      xdg_config = os.environ.get("XDG_CONFIG_HOME")
      if xdg_config:
          config_dir = os.path.join(xdg_config, "slash-agent")
      else:
          home = os.environ.get("HOME")
          if home:
              config_dir = os.path.join(home, ".config", "slash-agent")
          else:
              # Fallback to repo root .env if HOME is undefined
              repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
              return os.path.join(repo_root, ".env")
              
      return os.path.join(config_dir, "env")
  ```
* **Implementation (Bash - `installer.sh`)**:
  ```bash
  get_config_path() {
      if [ -n "$SLASH_AGENT_CONFIG_FILE" ]; then
          echo "$SLASH_AGENT_CONFIG_FILE"
          return
      fi
      local xdg_config="${XDG_CONFIG_HOME:-$HOME/.config}"
      if [ -n "$HOME" ]; then
          echo "$xdg_config/slash-agent/env"
      else
          # Fallback to repo root .env
          echo ".env"
      fi
  }
  ```

### Decision 2: Automatic Migration and Conflict Resolution
If the user has an existing `.env` file in the installation/repository root, and the new XDG config file does not yet exist:
* The system reads variables from the legacy `.env`.
* If a config file already exists at the new XDG path, the system merges them, keeping values already set in the XDG file and filling in missing keys from the legacy `.env`.
* It writes the merged/migrated config to the XDG path.
* It deletes the legacy `.env` file from the disk.

### Decision 3: Permissions Enforcement
* **Configuration File**: The config file will be created with `600` permissions (owner read/write only).
* **Parent Directory**: The parent directory (`~/.config/slash-agent`) will use default permissions based on the system umask (typically `700` or `755`).

## Risks / Trade-offs

* **[Risk] Directory Creation Failure** → If the parent directory (`~/.config/slash-agent`) does not exist, writing to it will fail.
  * *Mitigation*: Ensure the code calls `mkdir -p` (in Bash) or `os.makedirs` (in Python) before attempting to write or create the file.
* **[Risk] Multiple Clones sharing home config** → If a user has multiple clones of the repository on the same machine, they will now share a single global configuration in `~/.config/slash-agent/env`.
  * *Mitigation*: This is standard behavior for CLI tools and generally desirable, as users do not want to configure their API keys separately for every clone of the tool.
