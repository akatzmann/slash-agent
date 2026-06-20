## Context

The current `bin/installer.sh` is designed primarily for a fresh installation. When run in an environment where `INSTALL_DIR` already exists:
1. It prints "Installing slash-agent" instead of indicating that it is performing an update.
2. It runs `git pull` which can fail/crash the script if there are local modifications or divergent branches.
3. It completely overwrites the existing `.env` configuration file, requiring the user to re-enter Ollama endpoints and model configurations.

## Goals / Non-Goals

**Goals:**
- Detect whether `INSTALL_DIR` already exists and enter "Update Mode".
- In "Update Mode", print clear headers indicating that an update is in progress.
- Safely update the repository using `git pull` (handling errors gracefully without crashing the installer).
- Preserve any existing `.env` files in the installation directory, skipping interactive configuration prompts.

**Non-Goals:**
- Rewriting the virtual environment setup logic if it is already functional.
- Changing the shell integration sourcing logic (already idempotent).

## Decisions

### 1. Update Detection and Header Display
- **Decision**: Add an `UPDATE_MODE` boolean variable set to `true` if `$INSTALL_DIR` exists.
- **Rationale**: This allows us to conditionally print "Updating slash-agent" and adjust downstream prompt/configuration steps.

### 2. Graceful Git Update
- **Decision**: Wrap the `git pull` in a conditional block that verifies `.git` exists, and handle failures gracefully by displaying a warning instead of exiting.
- **Rationale**: If the user is in a development environment or has local changes, a hard crash on `git pull` is disruptive. Warning the user and continuing allows dependencies and environment settings to still be configured/checked.

### 3. Preserving `.env` files
- **Decision**: Check if `$INSTALL_DIR/.env` exists. If it does, skip the LLM config probing/prompting steps and display a message stating that the existing configuration is preserved.
- **Rationale**: This makes updating non-interactive and keeps the user's custom agent endpoints/models intact.

## Risks / Trade-offs

- **Risk**: The user might have a corrupt or incomplete `.env` file.
- **Mitigation**: If they want to reconfigure, they can delete the `.env` file or run a separate configuration command, or we can print the location of the `.env` file so they know how to edit it.
