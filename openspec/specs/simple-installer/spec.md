# simple-installer Specification

## Purpose
TBD - created by archiving change simple-installer. Update Purpose after archive.
## Requirements
### Requirement: Automated Prerequisites Verification
The installer script SHALL verify the presence of `git`, `python3`, and a working virtual environment builder (`venv` or `virtualenv`) on the host system, exiting with a non-zero code if any are missing.

#### Scenario: Missing git on target host
- **WHEN** git is not found in the executable PATH
- **THEN** the installer exits with exit code 1 and prints an error message.

### Requirement: Repository Cloning and Setup
The installer script SHALL clone the codebase from the project repository to a local installation folder. This folder SHALL default to `~/.agent-shell`, but can be overridden using the environment variable `INSTALL_DIR`.

#### Scenario: Cloning to a custom target directory
- **WHEN** the installer runs and `INSTALL_DIR` is set to a custom path
- **THEN** it clones the repository to that custom path.

### Requirement: Virtual Environment and Dependency Setup
The installer script SHALL initialize a Python 3 virtual environment in the installation directory and install requirements using pip.

#### Scenario: Python dependencies installation
- **WHEN** the virtual environment is set up
- **THEN** pip is invoked to install all python packages specified in `requirements.txt`.

### Requirement: Idempotent Shell Profile Registration
The installer script SHALL append the sourcing statement for `bin/agent-shell.sh` to the user's `~/.bashrc` file. It SHALL check if the line is already present to prevent duplicate entries.

#### Scenario: Runner executes installer multiple times
- **WHEN** the installer runs on a system where `~/.bashrc` already has the sourcing statement
- **THEN** it does not append duplicate lines to `~/.bashrc`.

