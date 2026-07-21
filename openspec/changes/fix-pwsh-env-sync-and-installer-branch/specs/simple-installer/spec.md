## ADDED Requirements

### Requirement: Branch-Aware Installation and Updates
The installation scripts (`installer.sh` and `installer.ps1`) SHALL inspect the `BRANCH` (or `$env:BRANCH`) environment variable and perform branch-specific git cloning and checking out when specified.

#### Scenario: User installs or updates slash-agent from a specific branch
- **WHEN** the user executes `installer.sh` or `installer.ps1` with `BRANCH` or `$env:BRANCH` set
- **THEN** the script clones or checks out the specified branch during setup.
