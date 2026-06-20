## ADDED Requirements

### Requirement: Support Configure-Only Mode with Pre-populated Defaults
The installer script MUST support running with a `--configure` or `-c` flag. In this mode, the installer SHALL bypass setup checks and repository cloning, load existing configuration variables from `.env` if available, and prompt the user to configure their settings, using the existing configurations as default choices.

#### Scenario: Running configuration on an already installed setup
- **WHEN** the installer is invoked with the `--configure` or `-c` flag and `.env` exists
- **THEN** it skips virtual environment setup, clones, and prerequisite checks, loads existing configurations, uses them as defaults in interactive prompts, and writes updated values to `.env`.

### Requirement: Configuration of Agent Thinking Level
The installer script MUST prompt the user for their desired thinking level during configuration and save it.

#### Scenario: User chooses a thinking level in the installer
- **WHEN** the user selects a thinking level (off, low, medium, or high) in the installer prompts
- **THEN** the value is stored in `.env` under the variable name `AGENT_THINKING_LEVEL`.
