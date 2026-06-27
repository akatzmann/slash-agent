## MODIFIED Requirements

### Requirement: Absolute Path Enforcement
The `write_file` tool SHALL automatically resolve relative paths against the current working directory (`session_state.cwd`) instead of rejecting them. All user confirmation prompts and terminal output displays SHALL render the resolved absolute path.

#### Scenario: Relative path auto-resolved
- **WHEN** the agent calls `write_file` with a relative path (e.g. `docs/readme.md`)
- **THEN** the system resolves the path against `session_state.cwd` to an absolute path before processing the write operation

## ADDED Requirements

### Requirement: Workspace Boundary Safety Guardrail for Writes
Before executing a write, the system SHALL check if the resolved absolute target path falls outside the initial launching working directory (`session_state.initial_cwd`). If outside, the system SHALL automatically escalate the operation's `risk_level` to `critical`, requiring interactive user confirmation.

#### Scenario: Write outside initial working directory escalated to critical
- **WHEN** `write_file` resolves to a target path outside `session_state.initial_cwd`
- **THEN** the system sets `risk_level` to `critical` and prompts the user for interactive confirmation regardless of auto-confirm settings

### Requirement: Terminal Write Visualization
The event streaming loop in `main.py` SHALL intercept `ToolExecutionStartEvent` and `ToolExecutionEndEvent` for `write_file` calls to output real-time visual badges and execution summaries in the terminal.

#### Scenario: Real-time write badges and summary rendered
- **WHEN** `write_file` execution starts and ends
- **THEN** the terminal displays `📝 [Writing] /resolved/absolute/path` on start and a write summary (line count and preview) on completion
