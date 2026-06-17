## Why

Currently, running the installer script in an environment where the agent is already installed (i.e. the installation directory exists) can crash if the remote tracking branch or git status is not set up perfectly for a clean `git pull`. Additionally, running the installer completely overwrites the existing `.env` configuration file rather than preserving it. We need a robust, update-compatible install script that detects existing installations, prints a clean update notification instead of a fresh install notice, preserves the existing `.env` configuration files, and gracefully updates the repository.

## What Changes

- Modify installer behavior when `INSTALL_DIR` already exists:
  - Detect existing installation and output an "Updating..." status instead of "Installing..." message.
  - Perform the repository update safely without failing if `git pull` has issues (or do git fetch and reset/pull carefully, and handle failures cleanly, or use a fallback mechanism).
  - Check if `.env` exists in `INSTALL_DIR`. If it does, preserve existing `.env` files, only prompting/updating configuration if variables are missing or if the user requests it. Specifically, keep existing configuration by default.
- Ensure the script is a single install/update-compatible script.

## Capabilities

### New Capabilities

### Modified Capabilities
- `simple-installer`: Add update compatibility, including safe repository pulling/updating and preservation of the `.env` configuration file when the installer is rerun on an existing installation.

## Impact

- `bin/installer.sh`: Main script modified to support update mode, safe git updates, and `.env` preservation.
