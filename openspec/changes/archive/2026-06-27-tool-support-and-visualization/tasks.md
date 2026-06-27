## 1. Core State & Path Resolution Updates

- [x] 1.1 Add `initial_cwd` field to `ShellState` in `slash_agent/tools.py` and initialize it on startup.
- [x] 1.2 Update `read_file`, `write_file`, and `edit_file` in `slash_agent/tools.py` to automatically resolve relative paths against `session_state.cwd`.
- [x] 1.3 Add workspace boundary safety check in `write_file` and `edit_file` to escalate `risk_level` to `critical` if resolved target path is outside `session_state.initial_cwd`.

## 2. Tool Registration & System Prompt Updates

- [x] 2.1 Re-order tools array registration in `slash_agent/main.py` to place native file tools (`read_file`, `write_file`, `edit_file`) before `execute_command`.
- [x] 2.2 Refine system prompt instructions in `slash_agent/main.py` to strongly prioritize native file operations over shell builtins.

## 3. Central Event Loop Visualization Engine

- [x] 3.1 Implement event handlers in `main_async()` within `slash_agent/main.py` to catch `tool_execution_start` and `tool_execution_end` events.
- [x] 3.2 Add badge and status formatting for `read_file`, `write_file`, `edit_file`, `read_skill_instructions`, and `execute_command`.
- [x] 3.3 Ensure colored unified diffs are rendered on `edit_file` completion and write previews/summaries on `write_file` completion.
- [x] 3.4 Clean up inline redundant logging in `slash_agent/tools.py` to prevent duplicate output.
