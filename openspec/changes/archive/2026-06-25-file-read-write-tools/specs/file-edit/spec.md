# file-edit Specification

## Purpose
Provides the agent with a native, safety-gated tool for making targeted replacements within existing files via exact-match string substitution. Inherits the write risk model and shows a unified diff at confirmation so the user sees precisely what changes before approving.

## Requirements

### Requirement: Absolute Path Enforcement
The `edit_file` tool SHALL reject any path that is not absolute. If a relative path is supplied, the tool SHALL return an error string describing the requirement without modifying any file.

#### Scenario: Relative path rejected
- **WHEN** the agent calls `edit_file` with a path that does not begin with `/`
- **THEN** the tool returns an error message stating that an absolute path is required and no file is modified

---

### Requirement: File Must Exist
The `edit_file` tool SHALL return an error if the target file does not exist. Creating new files is the responsibility of `write_file`.

#### Scenario: Non-existent file returns error
- **WHEN** the agent calls `edit_file` with a path that does not point to an existing file
- **THEN** the tool returns an error message stating the file was not found

---

### Requirement: Exact-Match with Uniqueness Validation
The `old_str` argument SHALL be matched as a literal string (no regex, no fuzzy matching) against the file's contents. The system SHALL validate that `old_str` appears exactly once in the file before proceeding.
- If `old_str` is not found → return an error stating the string was not found
- If `old_str` appears more than once → return an error stating the match is ambiguous and instructing the agent to supply a more specific snippet

#### Scenario: Successful unique match
- **WHEN** `old_str` appears exactly once in the file
- **THEN** the system proceeds to confirmation with the proposed replacement

#### Scenario: String not found
- **WHEN** `old_str` does not appear in the file
- **THEN** the tool returns an error message stating the string was not found and no file is modified

#### Scenario: Ambiguous match rejected
- **WHEN** `old_str` appears more than once in the file
- **THEN** the tool returns an error message stating the match is ambiguous and asking the agent to include more surrounding context

---

### Requirement: Symlink-Safe Sensitive Path Detection for Edits
Before applying risk overrides, the system SHALL resolve the supplied path to its real path using the OS symlink-resolution facility. The resolved path SHALL be used for sensitive-path pattern matching, using the same `SENSITIVE_WRITE_PATHS` list as `write_file`.

#### Scenario: Edit via symlink to sensitive location treated as critical
- **WHEN** the agent calls `edit_file` with a path whose resolved location falls under a sensitive write path
- **THEN** the system sets `risk_level` to `critical` regardless of the LLM's supplied value

---

### Requirement: Tiered Auto-Confirm for Edits
`edit_file` SHALL follow the same auto-confirm tiers as `write_file`:
- `low` and `moderate` risk: auto-confirm when standard auto-confirm (`-y`) OR unsafe auto-confirm (`--unsafe-yes`) is enabled.
- `critical` risk: auto-confirm with countdown only when `--unsafe-yes` is enabled; prompt when only `-y` (or no flags) is set.

#### Scenario: Low-risk edit auto-confirmed with -y
- **WHEN** `-y` is active and `edit_file` is called with `risk_level` of `"low"`
- **THEN** the replacement is applied without prompting the user

#### Scenario: Moderate-risk edit auto-confirmed with -y
- **WHEN** `-y` is active and `edit_file` is called with `risk_level` of `"moderate"`
- **THEN** the replacement is applied without prompting the user

#### Scenario: Critical edit prompts under standard -y
- **WHEN** `-y` is active and `edit_file` is called with `risk_level` of `"critical"`
- **THEN** the system prompts the user for confirmation before applying the edit

#### Scenario: Critical edit auto-confirmed under --unsafe-yes with countdown
- **WHEN** `--unsafe-yes` is active and `edit_file` is called with `risk_level` of `"critical"`
- **THEN** the system executes a countdown warning before editing without prompting for input

---

### Requirement: Critical Edit Countdown Under --unsafe-yes
When `--unsafe-yes` is active and a `critical`-classified edit is about to execute, the system SHALL apply the same countdown behaviour as `write_file`, using the `SLASH_AGENT_UNSAFE_DELAY` environment variable.

#### Scenario: Countdown fires before critical edit executes
- **WHEN** `--unsafe-yes` is active and a `critical`-classified `edit_file` operation is about to execute
- **THEN** the system displays the `[⚠ UNSAFE-YES]` countdown before applying the edit

---

### Requirement: Edit Confirmation Displays Unified Diff
When prompting, the system SHALL display the operation type (`EDIT`), the resolved absolute path, a unified diff of the proposed change, the color-coded risk level, and the risk description. The prompt SHALL offer `[y]es`, `[n]o`, and `[c]omment` options.

#### Scenario: Confirmation shows unified diff
- **WHEN** the system prompts the user to confirm an `edit_file` operation
- **THEN** the terminal displays the operation label `EDIT`, the resolved path, a `difflib.unified_diff` of `old_str` → `new_str` in context, the colored risk level, the risk description, and the `[y]es / [n]o / [c]omment` prompt

#### Scenario: User provides comment feedback
- **WHEN** the user selects `[c]omment` at the edit confirmation prompt
- **THEN** the system collects the user's text and returns it as feedback to the agent without modifying the file

---

### Requirement: Dry-Run Suppression for Edits
When dry-run mode is active, `edit_file` SHALL print a simulation message showing the proposed diff but SHALL NOT modify any file.

#### Scenario: Dry-run suppresses edit
- **WHEN** `--dry-run` is active and `edit_file` is called
- **THEN** the tool prints a simulation notice with the diff and does not modify any file

---

### Requirement: Permission Error Handling for Edits
If the edit operation fails due to a filesystem permission error, the tool SHALL return a descriptive error message. The tool SHALL NOT propagate raw OS exceptions.

#### Scenario: Permission denied returns clear error
- **WHEN** `edit_file` is called on a file the process does not have write access to
- **THEN** the tool returns an error string describing the permission issue and no file is modified

---

### Requirement: Risk Parameters on edit_file
The `edit_file` tool SHALL accept `risk_level` and `risk_description` parameters from the LLM following the same semantics as `write_file`.

#### Scenario: Tool receives risk parameters
- **WHEN** the agent calls `edit_file` with `risk_level` and `risk_description`
- **THEN** the tool processes them, subject to Python-level override, before presenting any confirmation
