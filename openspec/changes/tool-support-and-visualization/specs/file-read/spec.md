## MODIFIED Requirements

### Requirement: Absolute Path Enforcement
The `read_file` tool SHALL automatically resolve relative paths against the current working directory (`session_state.cwd`) instead of rejecting them. All confirmation prompts and terminal output displays SHALL render the resolved absolute path.

#### Scenario: Relative path auto-resolved
- **WHEN** the agent calls `read_file` with a relative path (e.g. `src/main.py`)
- **THEN** the system resolves the path against `session_state.cwd` to an absolute path before executing the read operation

## ADDED Requirements

### Requirement: Terminal Read Visualization
The event streaming loop in `main.py` SHALL intercept `ToolExecutionStartEvent` and `ToolExecutionEndEvent` for `read_file` calls to output real-time visual badges in the terminal.

#### Scenario: Real-time read badges rendered
- **WHEN** `read_file` execution starts and ends
- **THEN** the terminal displays `📖 [Reading] /resolved/absolute/path` on start and `✓ Read completed` on completion
