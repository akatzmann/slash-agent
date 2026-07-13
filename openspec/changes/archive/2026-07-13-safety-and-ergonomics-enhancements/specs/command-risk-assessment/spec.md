## MODIFIED Requirements

### Requirement: Python Safety Guardrails
The system SHALL override the agent's risk classification to `critical` if the proposed command matches high-risk administrative or filesystem destructive patterns. When overriding, the system SHALL concatenate the hardcoded administrative warning with the agent's custom risk description to preserve context.

#### Scenario: Dangerous command pattern override
- **WHEN** the command contains patterns like `rm -rf` or `sudo `
- **THEN** the system sets `risk_level` to `critical` and concatenates the administrative warning with the agent's custom `risk_description` (if provided) to display to the user.

---

### Requirement: Python Safety Guardrails for File Operations
The system SHALL maintain a hardcoded `SENSITIVE_READ_PATHS` list for `read_file` operations and a (superset) `SENSITIVE_WRITE_PATHS` list for `write_file` and `edit_file` operations. Paths SHALL be resolved via `os.path.realpath()` before matching. When the resolved path matches any entry, the system SHALL override the LLM-supplied risk to `critical`, analogous to the existing command pattern overrides for shell execution. When overriding, the system SHALL concatenate the hardcoded path alert with the agent's custom risk description to preserve context.

#### Scenario: Sensitive read path forced to critical
- **WHEN** `read_file` is called with a path resolving to a sensitive location (e.g. `/etc/shadow`, `~/.ssh/id_rsa`)
- **THEN** the system overrides `risk_level` to `critical` and appends the agent's description to the sensitive path warning.

#### Scenario: Sensitive write path forced to critical
- **WHEN** `write_file` or `edit_file` is called with a path resolving to a system location (e.g. `/etc/hosts`, `/usr/bin/mybin`)
- **THEN** the system overrides `risk_level` to `critical` and appends the agent's description to the sensitive path warning.
