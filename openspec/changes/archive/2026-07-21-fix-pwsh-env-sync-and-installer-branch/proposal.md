## Why

PowerShell executions fail at the end of every response with a `ParserError: $env:` because Windows internal drive variables (e.g., `=C:=C:\Users\...`) create empty environment keys (`""`) during PTY parsing, leading to malformed `$env: = '...'` statements in temporary `.ps1` sync files. Additionally, the installation scripts (`installer.sh` and `installer.ps1`) do not support branch-specific installation or updating, forcing contributors to manually switch branches after cloning.

## What Changes

* **Environment Variable Sync Filtering:** Exclude empty variable names and internal keys starting with `=` during PTY output parsing (`tools.py`) and shell diff generation (`main.py`).
* **Branch-Aware Installers:** Add support for an optional `BRANCH` / `$env:BRANCH` environment variable in `installer.sh` and `installer.ps1` to allow cloning and checking out specific branches directly during installation or updates.

## Capabilities

### New Capabilities

*(None)*

### Modified Capabilities

- `shell-agent`: Exclude invalid/internal environment keys during state synchronization parsing and generation.
- `simple-installer`: Support optional branch selection during installation and updates via the `BRANCH` environment variable.

## Impact

* **`slash_agent/tools.py`**: Filter empty keys and keys starting with `=` in `parse_pty_result`.
* **`slash_agent/main.py`**: Filter empty keys and keys starting with `=` in `get_env_diff`.
* **`bin/installer.sh`**: Inspect `BRANCH` and pass `-b $BRANCH` to `git clone` or run `git checkout $BRANCH` during updates.
* **`bin/installer.ps1`**: Inspect `$env:BRANCH` and pass `-b $Branch` to `git clone` or run `git checkout $Branch` during updates.
