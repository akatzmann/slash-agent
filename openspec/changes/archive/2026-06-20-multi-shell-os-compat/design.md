## Context

`slash-agent` uses a hybrid bash-python architecture:
- Sourced shell scripts capture context, spawn Python, and source a state synchronization file.
- Python processes tasks and writes environment/directory changes to the state synchronization file.
- Currently, script paths, history-capture, temporary files, shell profile registration, and python state synchronization are hardcoded for Bash on Linux. 

To support Zsh, Ksh, Fish, macOS (BSD), and Windows (WSL2), we must modify both the wrapper scripts, the installer, and the Python serialization logic.

## Goals / Non-Goals

**Goals:**
- Natively support Bash, Zsh, Ksh, and Fish on Linux and macOS.
- Ensure the installer correctly configures shell integrations for login shells on macOS.
- Resolve BSD utility discrepancies (like `mktemp` and `sed`).
- Document Windows compatibility using WSL2.

**Non-Goals:**
- Native Windows command execution (CMD/PowerShell) support.
- Native tcsh/csh support.

## Decisions

### 1. Unified POSIX Wrapper (`bin/slash-agent.sh`) and Fish Wrapper (`bin/slash-agent.fish`)
- **Decision**: Use a single shell wrapper `bin/slash-agent.sh` for Bash, Zsh, and Ksh using dynamic shell detection, and create a standalone `bin/slash-agent.fish` for Fish.
- **Rationale**: Bash, Zsh, and Ksh share common Bourne shell syntax, making unified integration simple with minimal branching. Fish uses a completely different syntax (e.g. no POSIX functions, variable assignment via `set`), requiring its own clean wrapper.
- **Alternatives Considered**: Creating four distinct wrapper files. This was rejected due to high code duplication and maintenance overhead.

### 2. Python Orchestrator `--shell` Parameter
- **Decision**: Add a `--shell` argument to `slash_agent/main.py` (defaulting to `bash`). If `--shell fish` is specified, `get_env_diff()` will write variables in Fish syntax (`set -gx KEY "value"` and `set -e KEY`).
- **Rationale**: Python is the most robust place to determine serialization formats. Parsing bash statements inside a Fish wrapper is prone to string escape bugs.
- **Alternatives Considered**: Writing a POSIX-to-Fish shell translation function in Fish. Rejected due to complexity of parsing quoted variables.

### 3. Shell Profile Detection in Installer
- **Decision**: In `bin/installer.sh`, detect the user's active login shell via `$SHELL` and register the appropriate wrapper. For macOS (`Darwin`), default Bash profiles to `~/.bash_profile` (or `~/.profile`) to account for login-shell behavior.
- **Rationale**: On macOS, Terminal and iTerm2 open login shells, which do not load `~/.bashrc` automatically. Registering in the correct login profile prevents "command not found" errors after installation.
- **Alternatives Considered**: Prompting the user to select their shell profile. Rejected to keep the default installation non-interactive and fast.

### 4. POSIX Temp File Syntax
- **Decision**: Replace `mktemp -t prefix.XXXXXX` with POSIX-standard `mktemp "${TMPDIR:-/tmp}/prefix.XXXXXX"`.
- **Rationale**: BSD `mktemp` (macOS default) does not support `.XXXXXX` templates alongside the `-t` flag in the same way as GNU `mktemp`, throwing errors. The template path works on both systems.
- **Alternatives Considered**: Suffix checks and branching. Rejected as standard path templates are simpler and cleaner.

## Risks / Trade-offs

- **[Risk]**: Fish does not allow `/` in function names, so `/agent` cannot be registered as a native function in Fish.
  - *Mitigation*: Register the function as `agent` or `slash-agent` in Fish, or set up a Fish abbreviation/alias, and document this clearly in the README.
- **[Risk]**: Zsh and Bash history fallbacks have different formatting.
  - *Mitigation*: Branch history capture commands. Use `fc -ln` for Zsh, standard `history` parsing for Bash/Ksh, and Fish-native `history` command for Fish.
