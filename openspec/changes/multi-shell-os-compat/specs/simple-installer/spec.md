## MODIFIED Requirements

### Requirement: Idempotent Shell Profile Registration
The installer script SHALL append the sourcing statement for `bin/slash-agent.sh` (or `bin/slash-agent.fish` for Fish) to the user's appropriate shell profile file based on their active login shell and operating system. It SHALL check if the sourcing statement is already present to prevent duplicate entries.

#### Scenario: Installer runs in Zsh on macOS
- **WHEN** the installer runs on a macOS system and the user's login shell is Zsh
- **THEN** the installer appends the sourcing statement for `bin/slash-agent.sh` to `~/.zshrc` if not already present.

#### Scenario: Installer runs in Bash on macOS
- **WHEN** the installer runs on a macOS system and the user's login shell is Bash
- **THEN** the installer appends the sourcing statement for `bin/slash-agent.sh` to `~/.bash_profile` (or `~/.profile`) if not already present.

#### Scenario: Installer runs in Fish on Linux
- **WHEN** the installer runs on a Linux system and the user's login shell is Fish
- **THEN** the installer appends the sourcing statement for `bin/slash-agent.fish` to `~/.config/fish/config.fish` if not already present.

#### Scenario: Duplicate registration prevention
- **WHEN** the installer runs on a system where the appropriate shell profile already has the sourcing statement
- **THEN** it does not append duplicate lines to the profile.
