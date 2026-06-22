## MODIFIED Requirements

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
