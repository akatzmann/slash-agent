## Why

The agent currently has no native way to read or write files — it must shell out to `cat`, `tee`, or `echo >>` to do so, which is harder to audit, bypass-able, and inconsistent with the command-risk confirmation model already in place. Adding dedicated `read_file`, `write_file`, and `edit_file` tools closes this capability gap and brings file operations under the same safety model as shell execution.

## What Changes

- **New tool**: `read_file(path, risk_level, risk_description)` — reads a file and returns its contents, with LLM-assessed and Python-override-enforced risk gating; auto-confirmed reads print a one-liner `[Agent Reading] /path` rather than running silently
- **New tool**: `write_file(path, content, risk_level, risk_description)` — writes content to a file (create or overwrite), prompting for confirmation with a content preview; parent directories are auto-created; standard `-y` auto-confirms `low` and `moderate` risk writes; `--unsafe-yes` additionally auto-confirms `critical` risk writes subject to a 5-second countdown delay
- **New tool**: `edit_file(path, old_str, new_str, risk_level, risk_description)` — targeted replacement within an existing file using exact-match with uniqueness validation; confirmation shows a unified diff; inherits the same risk model as `write_file`
- **New behavior**: Absolute-path enforcement on all three tools — relative paths are rejected with a descriptive error
- **New behavior**: Sensitive-path pattern matching layer (analogous to the existing `critical_patterns` in `execute_command`) that overrides the LLM's risk assessment to `critical` for known-sensitive file system locations (e.g. `/etc/shadow`, `/.ssh/`, `/.aws/credentials`), using symlink resolution to prevent bypass
- **New behavior**: `--unsafe-yes` triggers a configurable countdown (default 5 s, via `SLASH_AGENT_UNSAFE_DELAY`) with a warning before any `critical`-classified operation (shell command or file read/write/edit) executes, giving the user a Ctrl+C abort window
- **New behavior**: Dry-run mode (`-n`) suppresses file writes and edits (reads are unaffected)
- **Modified behavior**: Unified auto-confirm semantics — standard `-y` auto-confirms `low` and `moderate` risk operations (both shell commands and file operations); `--unsafe-yes` additionally auto-confirms `critical` operations subject to a countdown warning.

## Capabilities

### New Capabilities

- `file-read`: Secure file reading with absolute-path enforcement, LLM risk assessment, Python-level sensitive-path overrides, and unified auto-confirm behavior
- `file-write`: Secure file writing with the same safety model as `file-read`, plus unified confirmation (low/moderate auto with `-y` or `--unsafe-yes`, critical auto with `--unsafe-yes` + countdown), content preview at confirmation, and dry-run suppression
- `file-edit`: Targeted in-file replacement via exact-match + uniqueness check, with unified diff shown at confirmation; inherits write semantics for risk gating

### Modified Capabilities

- `command-risk-assessment`: The risk-assessment model (LLM-provided fields + Python safeguard overrides + auto-confirm tiers) is extended to cover file operations in addition to shell commands. The `--unsafe-yes` flag is unified to auto-confirm all critical operations (shell commands and file reads/writes/edits) subject to a configurable countdown warning (default 5 s via `SLASH_AGENT_UNSAFE_DELAY`), allowing Ctrl+C abort. Standard `-y` auto-confirms both low and moderate risk operations.

## Impact

- `slash_agent/tools.py`: three new `@tool` functions (`read_file`, `write_file`, `edit_file`), new helpers for sensitive-path detection, countdown-delay, and file confirmation prompt
- `slash_agent/main.py`: register all three tools in the agent tools list; update system prompt guidelines to instruct the LLM to use native file tools instead of shell-based file I/O and to always supply absolute paths
- `openspec/specs/command-risk-assessment/spec.md`: delta required for `--unsafe-yes` countdown behaviour (including `SLASH_AGENT_UNSAFE_DELAY`) and extension to file operations
- No new dependencies — stdlib `os`, `time`, `difflib` are sufficient
