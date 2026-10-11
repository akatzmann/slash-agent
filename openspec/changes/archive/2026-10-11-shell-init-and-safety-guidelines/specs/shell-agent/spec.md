## ADDED Requirements

### Requirement: Shell Init Command
The CLI SHALL provide an `init` subcommand that outputs shell integration scripts to stdout for supported shells: `bash`, `zsh`, `ksh`, and `fish`. The emitted script SHALL define the `/agent` and `agent` functions (or custom alias specified by `--cmd`) that capture context, invoke `slash-agent`, and synchronize shell state.

#### Scenario: Generate Bash initialization script
- **WHEN** the user executes `slash-agent init bash`
- **THEN** the system SHALL output a sourceable Bash script defining the `/agent` and `agent` shell functions to stdout.

#### Scenario: Generate Zsh initialization script
- **WHEN** the user executes `slash-agent init zsh`
- **THEN** the system SHALL output a sourceable Zsh script using `fc -ln` for command history capture to stdout.

#### Scenario: Generate Fish initialization script
- **WHEN** the user executes `slash-agent init fish`
- **THEN** the system SHALL output a sourceable Fish script defining the `/agent` and `agent` functions to stdout.

#### Scenario: Generate Ksh initialization script
- **WHEN** the user executes `slash-agent init ksh`
- **THEN** the system SHALL output a sourceable Ksh script to stdout.

#### Scenario: Custom command alias
- **WHEN** the user executes `slash-agent init bash --cmd myagent`
- **THEN** the emitted script SHALL define `myagent` and `/myagent` as the function names instead of the default `agent` and `/agent`.

#### Scenario: Auto-detect active shell when omitted
- **WHEN** the user executes `slash-agent init` without specifying a shell name
- **THEN** the system SHALL detect the current shell from environment variables (`$SHELL`, `$ZSH_VERSION`) and output the corresponding integration script.

#### Scenario: Idempotent installation to shell configuration file
- **WHEN** the user executes `slash-agent init --install` (or `slash-agent init zsh --install`)
- **THEN** the system SHALL resolve the appropriate shell profile path (`~/.zshrc`, `~/.config/fish/config.fish`, `~/.kshrc`, `~/.bashrc`, or macOS `~/.bash_profile`) and append the initialization hook if not already present.

#### Scenario: Unsupported shell error
- **WHEN** the user executes `slash-agent init tcsh`
- **THEN** the system SHALL exit with a non-zero exit code and an error message indicating that `tcsh` is unsupported.

### Requirement: Self-Upgrade Command
The system SHALL support an `--update` / `--upgrade` (or `-u`) flag on `/agent` and `slash-agent` to upgrade the current installation.

#### Scenario: Upgrading git-based installation
- **WHEN** the user executes `/agent --update` or `slash-agent --update` in an environment installed via git clone
- **THEN** the system SHALL invoke the updater logic to pull latest changes and refresh dependencies.

#### Scenario: Upgrading package-based installation
- **WHEN** the user executes `slash-agent --update` in a pip or pipx environment
- **THEN** the system SHALL output instructions or invoke the package manager upgrade for `slash-agent`.
