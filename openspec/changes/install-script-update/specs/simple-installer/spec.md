## MODIFIED Requirements

### Requirement: Repository Cloning and Setup
The installer script SHALL clone the codebase from the project repository to a local installation folder. This folder SHALL default to `~/.agent-shell`, but can be overridden using the environment variable `INSTALL_DIR`.

#### Scenario: Cloning to a custom target directory
- **WHEN** the installer runs and `INSTALL_DIR` is set to a custom path
- **THEN** it clones the repository to that custom path.

#### Scenario: Updating an existing installation directory
- **WHEN** the installer runs and the target installation directory already exists
- **THEN** it performs a safe update from the repository, prints an updating status message instead of a fresh install message, and continues successfully.

## ADDED Requirements

### Requirement: Configuration Preservation and Setup
The installer script SHALL configure the environment settings by creating or preserving the `.env` file in the installation directory. If the `.env` file already exists, it SHALL preserve the existing configuration instead of overwriting it.

#### Scenario: Running installer for the first time
- **WHEN** the installer is executed and no `.env` file exists in the installation directory
- **THEN** it prompts the user or probes the environment to create a new `.env` configuration file.

#### Scenario: Rerunning installer on an existing installation
- **WHEN** the installer is executed and a `.env` file already exists in the installation directory
- **THEN** it keeps the existing `.env` file and does not overwrite it or prompt for existing fields.
