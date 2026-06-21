## Why

In the current implementation, the plain-text `.env` configuration file containing sensitive secrets (like `OPENAI_API_KEY`) is stored inside the installation repository root. This exposes user keys to accidental leakage or disclosure when recursive search tools (e.g. `grep -R`) are run within code workspaces or parent directories.

## What Changes

* **Relocation of Configuration**: Move the active configuration file from the repository root (`.env`) to the standard user configuration directory (`~/.config/slash-agent/env` or matching `$XDG_CONFIG_HOME`/`$HOME` overrides) with secure file permissions (`chmod 600`).
* **Update Config Loading**: Update the Python runner to resolve and load environment variables from the new relocated configuration path, keeping repository directories clean.
* **Update Installer Logic**: Update the installer script (`bin/installer.sh`) to read from and write configuration changes to the relocated configuration path.

## Capabilities

### New Capabilities

*None*

### Modified Capabilities

- `simple-installer`: Configuration management is updated to locate the environment configuration file at the user's XDG-compliant config directory instead of the repository/install root.
- `shell-agent`: The shell agent loading mechanism is updated to look up and load config variables from the XDG configuration path rather than the repository root.
- `github-documentation`: Configuration instructions in `README.md` and `docs/documentation.md` are updated to point to the new configuration location instead of the repository-root `.env`.

## Impact

* **Affected Code**: `bin/installer.sh`, `slash_agent/main.py`, `README.md`, `docs/documentation.md`
* **APIs & Dependencies**: No external API changes; preserves existing environment loading behavior.
* **System Integration**: Fully backwards compatible with the existing shell/bash integration and environment synchronization flow.

