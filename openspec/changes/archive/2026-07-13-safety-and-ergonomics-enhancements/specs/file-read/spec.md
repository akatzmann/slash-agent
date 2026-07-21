## ADDED Requirements

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
