## Context

The agent shell requires multiple setup steps: cloning, setting up a Python virtual environment, installing dependencies (including the custom `py-agent-core` from GitHub), and configuring the shell's `.bashrc`. An installer script hosted on GitHub can automate this via a piping pipeline: `curl -fsSL <github_path>/bin/installer.sh | sh`.

## Goals / Non-Goals

**Goals:**
- Provide a robust, self-contained shell script `bin/installer.sh`.
- Automatically verify prerequisites (`git`, `python3`, `pip`).
- Clone the repository to the destination directory (defaulting to `~/.agent-shell`, configurable via `INSTALL_DIR`).
- Initialize a python virtual environment (`.venv`) and install dependencies from `requirements.txt`.
- Append the source command `source ~/.agent-shell/bin/agent-shell.sh` to `~/.bashrc` safely (idempotent, checking if already exists).

**Non-Goals:**
- Install system-level packages like Python itself or Git (the installer will check and error out if not present).
- Support Windows-native Command Prompt/PowerShell environments.

## Decisions

### Decision 1: Repository source URL
The installer needs to know where to clone the repo from.
- **Option A (Chosen):** Use the public repository URL `https://github.com/akatzmann/AgentShell.git` (assumed location or configurable via `REPO_URL`).
  - *Rationale:* Allows standard clone. If the repo is renamed, the user can override it.

### Decision 2: Safe modification of shell profile (`~/.bashrc`)
Modifying configuration files can be risky if done blindly.
- **Option A (Chosen):** Ensure the addition is idempotent by checking `grep` for the wrapper source command in `~/.bashrc` before appending.
  - *Rationale:* Prevents cluttering the user's profile with multiple identical lines upon rerun.

### Decision 3: Fallback for missing `venv` package
On many Debian-based systems, `python3` is installed but `python3-venv` is a separate package.
- **Option A (Chosen):** Check if `python3 -m venv` fails. If it does, check for `virtualenv`. If both fail, print a helpful error message asking the user to install `python3-venv` or `virtualenv` using their system package manager.
  - *Rationale:* Improves user experience and prevents silent failure inside virtualenvs.

## Risks / Trade-offs

- **[Risk]** Running arbitrary scripts directly from curl (`curl ... | sh`) has security implications.
  - *Mitigation:* Ensure the script is clean, concise, and easy to inspect. Keep instructions simple.
