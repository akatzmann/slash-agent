## ADDED Requirements

### Requirement: Selective Command Output Streaming
During command execution, if the accumulated output exceeds 50KB or 500 lines, the system SHALL collapse the live terminal output to a status indicator, and SHALL return a truncated preview (the first 50 and last 100 lines) to the agent.

#### Scenario: Verbose command triggers selective streaming collapse
- **WHEN** the agent runs a command that outputs 1500 lines of build logs
- **THEN** the system collapses the terminal output display to a status spinner and returns a truncated preview of the logs (first 50 and last 100 lines) with a truncation notice.

---

### Requirement: Silent Execution Mode
The system SHALL support a `--silent` command-line flag. When active, all command execution outputs SHALL be hidden from the user's terminal (excluding manual confirmation prompts). If a command fails (exit code != 0), the system SHALL automatically output the entire log buffer to the terminal.

#### Scenario: Silent command fails and dumps log
- **WHEN** `--silent` is enabled and a command fails
- **THEN** the system outputs the full captured log to the terminal for debugging.

---

### Requirement: Unified Transient Command Logging
The system SHALL write the full multiplexed stdout/stderr of every command execution to a unique transient log file stored inside the cross-platform system temporary directory (`tempfile.gettempdir()`). To prevent other local users from reading sensitive console output on shared environments, the system SHALL enforce owner-only read/write permissions (e.g. file mode `0o600` on POSIX systems or equivalent Windows ACLs) on the generated log files and their parent folders. If the command output is large (>=20KB), the tool completion message SHALL include the path of the log file, the size, the total number of lines, and a preview, allowing the agent to paginate the log using the `read_file` tool.

#### Scenario: Large output log path returned to agent
- **WHEN** a command executes and generates 250KB of output
- **THEN** the system writes the output to `<temp_dir>/slash-agent/cmd_<run_id>.log` with owner-only permissions and returns the log path and preview to the agent.
