## Why

Currently, `slash-agent` is hardcoded to support only the Bash shell on Linux systems. 
- macOS has defaulted to Zsh since macOS Catalina, and many developers use Fish or Zsh on Linux.
- The installer is hardcoded to register the integration in `~/.bashrc`, which macOS terminal sessions (running login shells) do not load by default.
- The script path resolution, temporary file creation (`mktemp`), and history capture command are Linux/Bash specific, leading to errors on macOS/Zsh/Fish.
- Windows users lack a clear, documented path to run the agent.

Adding support for Zsh, Ksh, and Fish, along with BSD compatibility for macOS, ensures `slash-agent` is accessible to the vast majority of command-line developers.

## What Changes

- **Shell Compatibility**:
  - Update `bin/slash-agent.sh` to resolve package paths and retrieve command history compatibly in Bash and Zsh.
  - Make `bin/slash-agent.sh` compatible with Ksh.
  - Create a new native Fish wrapper `bin/slash-agent.fish`.
- **Installer Upgrades**:
  - Update `bin/installer.sh` to query the user's active login shell and register the appropriate wrapper script in `~/.bashrc`, `~/.zshrc`, `~/.kshrc`, or `~/.config/fish/config.fish`.
  - Update profile registration to account for macOS login shell behavior (registering in `~/.bash_profile` or `~/.profile` for Bash on macOS).
- **BSD Utility Compatibility**:
  - Update temporary file creation to use POSIX-compliant syntax compatible with BSD/macOS `mktemp`.
- **Python State Sync Expansion**:
  - Update `slash_agent/main.py` to output environment synchronization commands in Fish syntax (`set -gx` / `set -e`) if the shell wrapper specifies Fish.
- **Documentation**:
  - Update `README.md` to document Windows support via WSL2.

## Capabilities

### New Capabilities
- None

### Modified Capabilities
- `simple-installer`: Modify profile registration to support multiple shell profiles (`.zshrc`, `.kshrc`, `.bash_profile`, and `config.fish`) based on detected user shell and OS (Darwin vs Linux).
- `shell-agent`: Expand shell invocation, context capture, and environment state synchronization to support Bash, Zsh, Ksh, and Fish, and ensure BSD compatibility for temporary files.
- `github-documentation`: Document multi-shell support (Bash, Zsh, Ksh, Fish) and Windows (WSL2) compatibility in docs and README.md.

## Impact

- **Affected Files**:
  - `bin/installer.sh` (Installer logic and shell profile selection)
  - `bin/slash-agent.sh` (Bash/Zsh/Ksh wrapper path resolution and history capture)
  - `bin/slash-agent.fish` [NEW] (Fish wrapper script)
  - `slash_agent/main.py` (Shell parameter support and Fish-specific state serialization syntax)
  - `README.md` (WSL2 / Windows compatibility documentation)
- **External Dependencies**: No new external dependencies.
