## Why

Users currently must manually clone this repository, set up a Python virtual environment, install requirements, and manually update their `~/.bashrc` file. A single-command installer script, executable via `curl ... | sh`, automates this entire setup, making the tool instantly accessible to users.

## What Changes

- Add a new installer shell script `bin/installer.sh` to the repository.
- The script clones the repository to a local directory (default: `~/.agent-shell`).
- The script automatically checks for python3 and git, sets up a local `.venv` environment, installs requirements, and appends the `source` line to the user's `~/.bashrc`.
- Update `README.md` and `docs/documentation.md` to include instructions on using the single-command installer.

## Capabilities

### New Capabilities
- `simple-installer`: An automated installer script that handles directory setup, git cloning, python venv setup, python package installation, and `.bashrc` sourcing configuration.

### Modified Capabilities

## Impact

- Adds `bin/installer.sh` in the repository.
- Updates documentation files (`README.md` and `docs/documentation.md`) with the new quick-start installation commands.
- No impact on core python code or operational logic.
