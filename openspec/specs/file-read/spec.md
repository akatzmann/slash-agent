# file-read Specification

## Purpose
Provides the agent with a native, safety-gated tool for reading file contents, subject to absolute-path enforcement, LLM risk assessment, Python-level sensitive-path overrides, and tiered auto-confirm behaviour consistent with the command-risk-assessment model.
## Requirements
### Requirement: Absolute Path Enforcement
The `read_file` tool SHALL automatically resolve relative paths against the current working directory (`session_state.cwd`) instead of rejecting them. All confirmation prompts and terminal output displays SHALL render the resolved absolute path.

#### Scenario: Relative path auto-resolved
- **WHEN** the agent calls `read_file` with a relative path (e.g. `src/main.py`)
- **THEN** the system resolves the path against `session_state.cwd` to an absolute path before executing the read operation

### Requirement: Symlink-Safe Sensitive Path Detection
Before applying risk overrides, the system SHALL resolve the supplied path to its real path using the OS symlink-resolution facility. The resolved path SHALL be used for sensitive-path pattern matching, so that symlinks pointing into sensitive directories are treated as if the target path were supplied directly.

#### Scenario: Symlink to sensitive file treated as critical
- **WHEN** the agent calls `read_file` with a path that resolves via symlink to a sensitive location (e.g. `/etc/shadow`)
- **THEN** the system sets `risk_level` to `critical` regardless of the LLM's supplied value

---

### Requirement: Sensitive Read Path Override
The system SHALL override the LLM-supplied `risk_level` to `critical` when the resolved path matches any entry in the hardcoded sensitive-read-path list. The sensitive list SHALL include at minimum: `/etc/shadow`, `/etc/passwd`, `/etc/sudoers`, `/etc/ssh/`, `/.ssh/`, `/.gnupg/`, `/proc/`, `/sys/`, `/dev/`, `/.aws/credentials`, `/.aws/config`, `/.config/gcloud/`, `/.kube/config`.

#### Scenario: Shadow file read forced to critical
- **WHEN** the agent calls `read_file` with path `/etc/shadow` and `risk_level` of `"low"`
- **THEN** the system overrides risk to `critical` before presenting the confirmation prompt

---

### Requirement: Tiered Auto-Confirm for Reads
The system SHALL apply the following auto-confirm rules for `read_file`:
- `low` and `moderate` risk: auto-confirm when standard auto-confirm (`-y`) OR unsafe auto-confirm (`--unsafe-yes`) is enabled.
- `critical` risk: auto-confirm with countdown only when `--unsafe-yes` is enabled; prompt when only `-y` (or no flags) is set.

#### Scenario: Low-risk read auto-confirmed with -y
- **WHEN** `-y` is active and `read_file` is called with `risk_level` of `"low"`
- **THEN** the file is read and returned without prompting the user, and a one-liner `[Agent Reading] /resolved/path` is printed to the terminal

#### Scenario: Moderate-risk read auto-confirmed with -y
- **WHEN** `-y` is active and `read_file` is called with `risk_level` of `"moderate"`
- **THEN** the file is read and returned without prompting the user, and a one-liner `[Agent Reading] /resolved/path` is printed to the terminal

#### Scenario: Critical read prompts under standard -y
- **WHEN** `-y` is active and `read_file` is called with `risk_level` of `"critical"`
- **THEN** the system prompts the user for confirmation before reading

#### Scenario: Critical read auto-confirmed under --unsafe-yes with countdown
- **WHEN** `--unsafe-yes` is active and `read_file` is called with `risk_level` of `"critical"`
- **THEN** the system executes a 5-second countdown warning before reading the file without prompting for input

---

### Requirement: Auto-Confirm Verbosity for Reads
When `read_file` is auto-confirmed (not prompted), the system SHALL print a one-liner to the terminal indicating the path being read. The system SHALL NOT be fully silent for auto-confirmed reads.

#### Scenario: Auto-confirm prints one-liner
- **WHEN** `read_file` is auto-confirmed due to active `-y` or `--unsafe-yes` flags
- **THEN** the terminal displays `[Agent Reading] /resolved/absolute/path` before returning the file content

---

### Requirement: Read Confirmation Display
When prompting, the system SHALL display the operation type (`READ`), the resolved absolute path, the color-coded risk level, and the risk description. The prompt SHALL offer `[y]es`, `[n]o`, and `[c]omment` options.

#### Scenario: Confirmation prompt shows path and risk
- **WHEN** the system prompts the user to confirm a `read_file` operation
- **THEN** the terminal displays the operation label `READ`, the full resolved path, the colored risk level, the risk description, and the `[y]es / [n]o / [c]omment` prompt

#### Scenario: User provides comment feedback
- **WHEN** the user selects `[c]omment` at the file confirmation prompt
- **THEN** the system collects the user's text and returns it as feedback to the agent without reading the file

---

### Requirement: Risk Parameters on read_file
The `read_file` tool SHALL accept `risk_level` and `risk_description` parameters from the LLM, following the same semantics as `execute_command`: `risk_description` is optional for `safe`/`low` but required for `moderate`/`critical`.

#### Scenario: Tool receives risk parameters
- **WHEN** the agent calls `read_file` with `risk_level` and `risk_description`
- **THEN** the tool processes them, subject to Python-level override, before presenting any confirmation

### Requirement: Terminal Read Visualization
The event streaming loop in `main.py` SHALL intercept `ToolExecutionStartEvent` and `ToolExecutionEndEvent` for `read_file` calls to output real-time visual badges in the terminal.

#### Scenario: Real-time read badges rendered
- **WHEN** `read_file` execution starts and ends
- **THEN** the terminal displays `📖 [Reading] /resolved/absolute/path` on start and `✓ Read completed` on completion

### Requirement: Line-Bounded Reading
The `read_file` tool SHALL accept optional `start_line` and `end_line` (1-indexed, inclusive) parameters. If provided, the system SHALL only read and return the specified line range of the target file.

#### Scenario: Agent reads a specific line range
- **WHEN** the agent calls `read_file` with `start_line=10` and `end_line=20`
- **THEN** the system reads and returns only lines 10 through 20 of the target file.

---

### Requirement: Auto-Truncation Metadata
If `read_file` is called without line parameters on a file exceeding the reading limit, or if the range requested is larger than 1000 lines, the system SHALL automatically truncate the output (defaulting to the first N lines for unspecified reads) and append a clear metadata warning specifying the lines read, the total number of lines in the file, and instructions on how to use line ranges to read the rest.

#### Scenario: Unspecified read of a large file is truncated
- **WHEN** the agent calls `read_file` on a file containing 4500 lines without specifying `start_line` or `end_line`
- **THEN** the system returns only the first N lines (where N is the reading limit) and appends a message: `[File Truncated: Read lines 1-N of 4500 total lines. Use read_file with start_line and end_line parameters to read remaining segments, e.g. start_line=801, end_line=1600.]`

---

### Requirement: Configurable Line-Bounded Reading Limit
The default line-bounded reading and truncation threshold SHALL default to 800 lines and SHALL be configurable via the `AGENT_READ_LINE_LIMIT` environment variable. If an invalid or non-integer value is provided, it SHALL fall back to the default of 800.

#### Scenario: User overrides default read line limit
- **WHEN** `AGENT_READ_LINE_LIMIT=500` is set in the environment and a file of 700 lines is read without ranges
- **THEN** the system truncates the file output to the first 500 lines and displays the truncation metadata notice.

---

### Requirement: Interactive Gating Range Preview
When prompting the user for confirmation on a proposed read operation, the system SHALL display the target file path along with the requested line range (e.g., `(Lines 10-15)` or `(Lines 1-EOF)`) if ranges are specified.

#### Scenario: Gating displays line range bounds
- **WHEN** the agent proposes a read operation on `server.py` with `start_line=10` and `end_line=15`
- **THEN** the confirmation prompt displays `server.py (Lines 10-15)`

