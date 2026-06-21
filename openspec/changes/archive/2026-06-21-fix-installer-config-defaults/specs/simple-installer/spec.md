## MODIFIED Requirements

### Requirement: Support Configure-Only Mode with Pre-populated Defaults
The installer script MUST support running with a `--configure` or `-c` flag. In this mode, the installer SHALL bypass setup checks and repository cloning, load existing configuration variables from `.env` if available, and prompt the user to configure their settings, using the existing configurations as default choices.

#### Scenario: Running configuration on an already installed setup
- **WHEN** the installer is invoked with the `--configure` or `-c` flag and `.env` exists
- **THEN** it skips virtual environment setup, clones, and prerequisite checks, loads existing configurations, uses them as defaults in interactive prompts, and writes updated values to `.env`.

#### Scenario: Preserving defaults for same backend
- **WHEN** the installer is invoked with the `--configure` or `-c` flag and the user retains their current backend
- **THEN** the existing AGENT_ENDPOINT and AGENT_MODEL configurations are preserved and presented as the defaults in the interactive prompts.
