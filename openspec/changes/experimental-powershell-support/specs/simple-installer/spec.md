## ADDED Requirements

### Requirement: PowerShell Prerequisite Verification
On Windows and PowerShell environments, the installer SHALL check for the presence of `git` and `python` (checking both `python` and `python3` in path). If either is missing, it SHALL recommend installation commands using the Windows Package Manager (e.g. `winget install Git.Git`, `winget install Python.Python.3`).

#### Scenario: Missing git on Windows
- **WHEN** git is not found on a Windows host
- **THEN** the installer exits with exit code 1 and prints the suggested winget command to install git.

### Requirement: PowerShell Repository Cloning and Setup
On Windows, the installer script SHALL clone the codebase from the project repository to a local installation folder. This folder SHALL default to `$env:USERPROFILE\.slash-agent` but can be overridden using the environment variable `INSTALL_DIR`. If the directory already exists, it SHALL perform a `git pull` update.

#### Scenario: Cloning to default directory on Windows
- **WHEN** the installer runs on Windows and `INSTALL_DIR` is not set
- **THEN** it clones the repository to `$env:USERPROFILE\.slash-agent`.

### Requirement: PowerShell Configuration Path and Setup
The installer script SHALL configure environment settings under the user's config directory, defaulting to `$env:USERPROFILE\.config\slash-agent\env`. If the configuration file already exists, the installer SHALL preserve the existing configuration instead of overwriting it.

#### Scenario: Creating new config file on Windows
- **WHEN** the installer is executed and no configuration file exists at `$env:USERPROFILE\.config\slash-agent\env`
- **THEN** it prompts the user for backend choices and writes a new configuration file.

### Requirement: PowerShell Virtual Environment and Dependency Setup
On Windows, the installer script SHALL initialize the Python virtual environment under `.venv\` and use `.venv\Scripts\pip.exe` to upgrade pip and install python packages specified in `requirements.txt`.

#### Scenario: Windows dependency installation
- **WHEN** the installer runs on Windows
- **THEN** it executes `.venv\Scripts\pip.exe install -r requirements.txt`.

### Requirement: PowerShell Profile Registration
The installer script SHALL automatically register the shell integration command by appending `. "$HOME\.slash-agent\bin\slash-agent.ps1"` to the active PowerShell profile `$PROFILE` on the host system, ensuring no duplicate entries are made.

#### Scenario: First-time registration in PowerShell Profile
- **WHEN** the installer runs under PowerShell and the sourcing command is not present in `$PROFILE`
- **THEN** it creates the profile file and directory if they do not exist, and appends the sourcing command.

#### Scenario: Profile registration idempotency
- **WHEN** the installer runs and `$PROFILE` already contains the sourcing command
- **THEN** it does not modify the profile file.
