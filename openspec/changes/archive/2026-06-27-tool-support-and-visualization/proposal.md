## Why

The current tool execution framework in `slash-agent` exhibits poor visualization and path resolution friction. File operations (`read_file`, `write_file`, `edit_file`) fail when passed relative paths, while tool calls (including skill reading and file operations) execute with incomplete or missing terminal visualization in auto-confirm mode. These changes improve tool usability, enforce strict workspace safety boundaries, and unify terminal output visualization across all agent tools.

## What Changes

- **Tool Registration & Priority**: Re-order tool array registration in `slash_agent/main.py` so native file tools (`read_file`, `write_file`, `edit_file`) precede shell command execution (`execute_command`), and update system prompts to reinforce native tool selection over shell builtins (`cat`, `echo`, `sed`).
- **Path Auto-Resolution**: Automatically resolve relative paths against `session_state.cwd` for all tools, eliminating strict absolute path rejection errors while ensuring user confirmation prompts display the resolved absolute path.
- **Workspace Boundary Safety**: Escalate risk level for `write_file` and `edit_file` to `critical` (mandatory user confirmation) if the target path resolves outside the initial launching directory (`session_state.initial_cwd`).
- **Unified Terminal Visualization**: Intercept `ToolExecutionStartEvent` and `ToolExecutionEndEvent` centrally in `slash_agent/main.py` to display real-time badges (`[Reading]`, `[Writing]`, `[Editing]`, `[Skill]`, `[Running]`) and deterministic completion results (including unified diffs for file edits and write summaries for file writes).

## Capabilities

### New Capabilities
- None

### Modified Capabilities
- `file-read`: Support automatic resolution of relative paths against working directory and central start/completion visualization.
- `file-write`: Support automatic resolution of relative paths, automatic risk escalation for targets outside initial working directory, and write summary visualization upon completion.
- `file-edit`: Support automatic resolution of relative paths, automatic risk escalation for targets outside initial working directory, and colored unified diff rendering upon completion.
- `agent-skills`: Visualize skill reading actions (`read_skill_instructions`) in the terminal output stream.
- `shell-agent`: Re-order tool schema definitions, record initial workspace boundary (`initial_cwd`), and centralize tool execution stream events in `main.py`.

## Impact

- `slash_agent/main.py`: Updated tool registration order, system prompt alignment, initial working directory recording, and streaming loop event handlers.
- `slash_agent/tools.py`: Updated path resolution, risk escalation checks against initial working directory, and coordination with central visualization.
