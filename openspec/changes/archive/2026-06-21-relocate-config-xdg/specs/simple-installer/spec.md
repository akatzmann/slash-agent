## MODIFIED Requirements

### Requirement: Configuration Preservation and Setup
The installer script SHALL configure the environment settings by creating or preserving the environment configuration file in the user's standard configuration directory (defaulting to `~/.config/slash-agent/env` or `$XDG_CONFIG_HOME/slash-agent/env` with secure `600` permissions). If the configuration file already exists, it SHALL preserve the existing configuration instead of overwriting it.

#### Scenario: Running installer for the first time
- **WHEN** the installer is executed and no configuration file exists in the user's config directory
- **THEN** it prompts the user or probes the environment to create a new configuration file with secure `600` file permissions.

#### Scenario: Rerunning installer on an existing installation
- **WHEN** the installer is executed and a configuration file already exists in the user's config directory
- **THEN** it keeps the existing configuration file and does not overwrite it or prompt for existing fields.

#### Scenario: Migrating legacy configuration file
- **WHEN** the installer or agent runs, and a legacy `.env` file exists in the installation/repository root but no configuration file exists in the user's config directory
- **THEN** it SHALL load the legacy configuration, write it to the new configuration directory with secure `600` permissions, and remove or clear the legacy `.env` file to prevent plaintext secret exposure in the repository.

---

### Requirement: Support Configure-Only Mode with Pre-populated Defaults
The installer script MUST support running with a `--configure` or `-c` flag. In this mode, the installer SHALL bypass setup checks and repository cloning, load existing configuration variables from the configuration file if available, and prompt the user to configure their settings, using the existing configurations as default choices.

#### Scenario: Running configuration on an already installed setup
- **WHEN** the installer is invoked with the `--configure` or `-c` flag and the configuration file exists in the user's config directory
- **THEN** it skips virtual environment setup, clones, and prerequisite checks, loads existing configurations, uses them as defaults in interactive prompts, and writes updated values to the configuration file with secure `600` permissions.
