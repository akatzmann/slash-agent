# file-write Specification

## Purpose
Provides the agent with a native, safety-gated tool for writing file contents (create or overwrite), subject to absolute-path enforcement, LLM risk assessment, Python-level sensitive-path overrides, tiered auto-confirm behaviour, dry-run suppression, parent-directory auto-creation, and a configurable countdown delay for critical paths.
## Requirements
### Requirement: Absolute Path Enforcement
The `write_file` tool SHALL automatically resolve relative paths against the current working directory (`session_state.cwd`) instead of rejecting them. All user confirmation prompts and terminal output displays SHALL render the resolved absolute path.

#### Scenario: Relative path auto-resolved
- **WHEN** the agent calls `write_file` with a relative path (e.g. `docs/readme.md`)
- **THEN** the system resolves the path against `session_state.cwd` to an absolute path before processing the write operation

### Requirement: Symlink-Safe Sensitive Path Detection for Writes
Before applying risk overrides, the system SHALL resolve the supplied path to its real path. If the path does not yet exist, the system SHALL resolve its parent directory and construct the real path accordingly. The resolved path SHALL be used for sensitive-path pattern matching.

#### Scenario: Write via symlink to sensitive location treated as critical
- **WHEN** the agent calls `write_file` with a path whose resolved location falls under a sensitive write path (e.g. `/etc/hosts`)
- **THEN** the system sets `risk_level` to `critical` regardless of the LLM's supplied value

---

### Requirement: Sensitive Write Path Override
The system SHALL override the LLM-supplied `risk_level` to `critical` when the resolved path matches any entry in the hardcoded sensitive-write-path list. The sensitive write list SHALL be a superset of the sensitive read list and SHALL additionally include: `/etc/`, `/usr/`, `/bin/`, `/sbin/`, `/lib/`, `/lib64/`, `/boot/`.

#### Scenario: Write to /etc/ forced to critical
- **WHEN** the agent calls `write_file` with any path whose resolved location begins with `/etc/`
- **THEN** the system overrides risk to `critical` regardless of the LLM's input

---

### Requirement: Tiered Auto-Confirm for Writes
The system SHALL apply the following auto-confirm rules for `write_file`:
- `low` and `moderate` risk: auto-confirm when standard auto-confirm (`-y`) OR unsafe auto-confirm (`--unsafe-yes`) is enabled.
- `critical` risk: auto-confirm with countdown only when `--unsafe-yes` is enabled; prompt when only `-y` (or no flags) is set.

#### Scenario: Low-risk write auto-confirmed with -y
- **WHEN** `-y` is active and `write_file` is called with `risk_level` of `"low"`
- **THEN** the file is written without prompting the user

#### Scenario: Moderate-risk write auto-confirmed with -y
- **WHEN** `-y` is active and `write_file` is called with `risk_level` of `"moderate"`
- **THEN** the file is written without prompting the user

#### Scenario: Critical write prompts under standard -y
- **WHEN** `-y` is active and `write_file` is called with `risk_level` of `"critical"`
- **THEN** the system prompts the user for confirmation before writing

#### Scenario: Critical write auto-confirmed under --unsafe-yes with countdown
- **WHEN** `--unsafe-yes` is active and `write_file` is called with `risk_level` of `"critical"`
- **THEN** the system executes a countdown warning before writing without prompting for input

---

### Requirement: Critical Write Countdown Under --unsafe-yes
When `--unsafe-yes` is active and a `critical`-classified write is about to execute, the system SHALL display a warning message and count down before executing the write. The countdown duration SHALL default to 5 seconds and SHALL be overridable by the `SLASH_AGENT_UNSAFE_DELAY` environment variable (non-negative integer). The countdown SHALL be visible in the terminal one second at a time. If the user presses Ctrl+C during the countdown, the write SHALL be aborted.

#### Scenario: Countdown displayed before critical write
- **WHEN** `--unsafe-yes` is active and a `critical` write is about to execute
- **THEN** the terminal displays a `[⚠ UNSAFE-YES]` warning with the target path and counts down from the configured delay to 1 before proceeding

#### Scenario: Countdown duration respects SLASH_AGENT_UNSAFE_DELAY
- **WHEN** `SLASH_AGENT_UNSAFE_DELAY=10` is set in the environment
- **THEN** the countdown runs for 10 seconds instead of the default 5

#### Scenario: Ctrl+C aborts countdown
- **WHEN** the countdown is in progress and the user presses Ctrl+C
- **THEN** the write is aborted, an abort message is displayed, and the file is not modified

---

### Requirement: Write Confirmation Display
When prompting, the system SHALL display the operation type (`WRITE`), the resolved absolute path, a preview of the first 10 lines of the content to be written, the color-coded risk level, and the risk description. The prompt SHALL offer `[y]es`, `[n]o`, and `[c]omment` options.

#### Scenario: Confirmation shows content preview
- **WHEN** the system prompts the user to confirm a `write_file` operation
- **THEN** the terminal displays the operation label `WRITE`, the resolved path, a truncated content preview (up to 10 lines), the colored risk level, the risk description, and the `[y]es / [n]o / [c]omment` prompt

#### Scenario: User provides comment feedback
- **WHEN** the user selects `[c]omment` at the write confirmation prompt
- **THEN** the system collects the user's text and returns it as feedback to the agent without writing the file

---

### Requirement: Parent Directory Auto-Creation
When the target path's parent directory does not exist, `write_file` SHALL create all necessary intermediate directories before writing, equivalent to `mkdir -p`.

#### Scenario: Missing parent directories created
- **WHEN** `write_file` is called with a path whose parent directory does not exist
- **THEN** the system creates the full directory hierarchy and writes the file successfully

---

### Requirement: Dry-Run Suppression
When dry-run mode is active, `write_file` SHALL print a simulation message showing what would be written but SHALL NOT write any data to the filesystem.

#### Scenario: Dry-run suppresses write
- **WHEN** `--dry-run` is active and `write_file` is called
- **THEN** the tool prints a simulation notice including the target path and does not modify any file

---

### Requirement: Permission Error Handling
If the write operation fails due to a filesystem permission error, the tool SHALL return a descriptive error message to the LLM identifying the path and the permission problem. The tool SHALL NOT propagate raw OS exceptions.

#### Scenario: Permission denied returns clear error
- **WHEN** `write_file` is called on a path the process does not have write access to
- **THEN** the tool returns an error string describing the permission issue and no file is modified

---

### Requirement: Risk Parameters on write_file
The `write_file` tool SHALL accept `risk_level` and `risk_description` parameters from the LLM, following the same semantics as `execute_command`: `risk_description` is optional for `safe`/`low` but required for `moderate`/`critical`.

#### Scenario: Tool receives risk parameters
- **WHEN** the agent calls `write_file` with `risk_level` and `risk_description`
- **THEN** the tool processes them, subject to Python-level override, before presenting any confirmation

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

