## ADDED Requirements

### Requirement: Cross-Platform Execution and Logging
The system SHALL support execution of shell commands on POSIX and Windows systems, returning exit code, output preview, and log file path in a unified 3-tuple (`exit_code`, `output`, `log_path`).

#### Scenario: Windows command execution logging
- **WHEN** a command is executed on Windows via `run_command_windows`
- **THEN** output is logged to `/tmp/slash-agent/cmd_<run_id>.log` and a 3-tuple `(exit_code, output, log_path)` is returned.
