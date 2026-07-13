## ADDED Requirements

### Requirement: Line-Bounded Reading
The `read_file` tool SHALL accept optional `start_line` and `end_line` (1-indexed, inclusive) parameters. If provided, the system SHALL only read and return the specified line range of the target file.

#### Scenario: Agent reads a specific line range
- **WHEN** the agent calls `read_file` with `start_line=10` and `end_line=20`
- **THEN** the system reads and returns only lines 10 through 20 of the target file.

---

### Requirement: Auto-Truncation Metadata
If `read_file` is called without line parameters on a file exceeding 800 lines, or if the range requested is larger than 1000 lines, the system SHALL automatically truncate the output (defaulting to the first 800 lines for unspecified reads) and append a clear metadata warning specifying the lines read, the total number of lines in the file, and instructions on how to use line ranges to read the rest.

#### Scenario: Unspecified read of a large file is truncated
- **WHEN** the agent calls `read_file` on a file containing 4500 lines without specifying `start_line` or `end_line`
- **THEN** the system returns only the first 800 lines and appends a message: `[File Truncated: Read lines 1-800 of 4500 total lines. Use read_file with start_line and end_line parameters to read remaining segments, e.g. start_line=801, end_line=1600.]`
