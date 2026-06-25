# command-risk-assessment Delta Spec

## MODIFIED Requirements

### Requirement: Auto-Confirm Safety Boundaries
The system SHALL apply a unified auto-confirm policy across both shell command execution and file operations (`read_file`, `write_file`, `edit_file`):
- Standard auto-confirm (`-y` / `--yes`) SHALL auto-confirm `low` and `moderate` risk operations, but SHALL halt and prompt the user for confirmation on all `critical` operations.
- Unsafe auto-confirm (`--unsafe-yes`) SHALL auto-confirm all operations (including `critical` ones), but for any `critical` operation, a countdown warning SHALL execute before proceeding (see Added Requirements below).

#### Scenario: Standard auto-confirm halts on critical command
- **WHEN** standard auto-confirm is enabled and a `critical` command or file operation is proposed
- **THEN** the system halts and prompts the user for manual confirmation

#### Scenario: Standard auto-confirm bypasses moderate-risk operations
- **WHEN** standard auto-confirm is enabled and a `moderate`-risk command or file operation is proposed
- **THEN** the system executes the operation without prompting the user

#### Scenario: Unsafe auto-confirm bypasses critical prompts with countdown
- **WHEN** unsafe auto-confirm (`--unsafe-yes`) is enabled and a `critical` command or file operation is proposed
- **THEN** the system executes the operation without prompting for input, but executes a countdown warning first

---

## ADDED Requirements

### Requirement: --unsafe-yes Countdown Warning for Critical Operations
When `--unsafe-yes` is active and a `critical`-classified operation (shell command, file read, file write, or file edit) is about to proceed, the system SHALL display a prominent warning and count down before executing. The countdown duration SHALL default to 5 seconds and SHALL be configurable via the `SLASH_AGENT_UNSAFE_DELAY` environment variable (non-negative integer; invalid values fall back to the default). The countdown SHALL be interruptible via Ctrl+C.

#### Scenario: Warning and countdown displayed before critical operation
- **WHEN** `--unsafe-yes` is active and a `critical`-classified operation is executing
- **THEN** the terminal shows a `[⚠ UNSAFE-YES]` warning with the target details (command line or file path) and a countdown before execution starts

#### Scenario: Countdown duration configurable
- **WHEN** `SLASH_AGENT_UNSAFE_DELAY=10` is set in the environment
- **THEN** the countdown runs for 10 seconds instead of the default 5

#### Scenario: Countdown is Ctrl+C interruptible
- **WHEN** the countdown is in progress and the user presses Ctrl+C
- **THEN** the operation is aborted and an abort message is displayed without running the command or modifying any file

### Requirement: Python Safety Guardrails for File Operations
The system SHALL maintain a hardcoded `SENSITIVE_READ_PATHS` list for `read_file` operations and a (superset) `SENSITIVE_WRITE_PATHS` list for `write_file` and `edit_file` operations. Paths SHALL be resolved via `os.path.realpath()` before matching. When the resolved path matches any entry, the system SHALL override the LLM-supplied risk to `critical`, analogous to the existing command pattern overrides for shell execution.

#### Scenario: Sensitive read path forced to critical
- **WHEN** `read_file` is called with a path resolving to a sensitive location (e.g. `/etc/shadow`, `~/.ssh/id_rsa`)
- **THEN** the system overrides `risk_level` to `critical` regardless of the LLM's input

#### Scenario: Sensitive write path forced to critical
- **WHEN** `write_file` or `edit_file` is called with a path resolving to a system location (e.g. `/etc/hosts`, `/usr/bin/mybin`)
- **THEN** the system overrides `risk_level` to `critical` regardless of the LLM's input
