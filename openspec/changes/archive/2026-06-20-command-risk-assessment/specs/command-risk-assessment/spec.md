## ADDED Requirements

### Requirement: Tool Risk Parameters
The system SHALL accept `risk_level` and `risk_description` parameters on the `execute_command` tool. The `risk_description` parameter SHALL be optional for `safe` and `low` risk commands, but SHALL be required for `moderate` and `critical` commands.

#### Scenario: Tool receives risk parameters
- **WHEN** the agent calls the `execute_command` tool
- **THEN** it accepts and processes the `risk_level` and `risk_description` strings.

### Requirement: Python Safety Guardrails
The system SHALL override the agent's risk classification to `critical` if the proposed command matches high-risk administrative or filesystem destructive patterns.

#### Scenario: Dangerous command pattern override
- **WHEN** the command contains patterns like `rm -rf` or `sudo `
- **THEN** the system sets `risk_level` to `critical` and assigns an administrative warning as `risk_description` regardless of the LLM's input.

### Requirement: Auto-Confirm Safety Boundaries
The system SHALL halt and prompt the user for confirmation on `critical` commands when standard auto-confirm (`-y` / `--yes`) is enabled, unless `--unsafe-yes` is explicitly set.

#### Scenario: Standard auto-confirm halts on critical command
- **WHEN** standard auto-confirm is enabled and a `critical` command is proposed
- **THEN** the system halts and prompts the user for manual confirmation.

#### Scenario: Unsafe auto-confirm bypasses critical prompt
- **WHEN** unsafe auto-confirm (`--unsafe-yes`) is enabled and a `critical` command is proposed
- **THEN** the system executes the command without prompting the user.

### Requirement: Color-Coded Risk Display
The system SHALL print the risk level and description below the proposed command in the confirmation prompt using safety-category-specific ANSI colors.

#### Scenario: Prompting user with risk level
- **WHEN** prompting the user for confirmation
- **THEN** the system displays the colored risk category (Safe in Green, Low in Cyan, Moderate in Yellow, Critical in Red) followed by the risk description.
