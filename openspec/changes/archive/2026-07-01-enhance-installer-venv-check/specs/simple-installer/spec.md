## MODIFIED Requirements

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
