## Context

In `slash-agent`, file tools (`read_file`, `write_file`, `edit_file`) enforce strict absolute path checking (`if not os.path.isabs(path)`), causing tools to fail when relative paths are supplied. Furthermore, `execute_command` is currently positioned first in the tool schema registration array, leading LLMs to favor shell commands (`cat`, `echo`, `sed`) over native file operations. Finally, event streaming in `slash_agent/main.py` ignores tool execution events emitted by `py_agent_core` (`ToolExecutionStartEvent`, `ToolExecutionEndEvent`), causing tool executions to run with incomplete or missing terminal visualization in auto-confirm mode.

## Goals / Non-Goals

**Goals:**
- Enable seamless auto-resolution of relative paths against `session_state.cwd` for all tools.
- Enforce mandatory user confirmation (escalation to `critical`) when write/edit tools target files outside the agent's launching directory (`session_state.initial_cwd`).
- Re-order tool schema definitions in `main.py` so native file tools precede shell execution.
- Intercept tool lifecycle events in `main.py` to provide consistent, real-time visual badges (`[Reading]`, `[Writing]`, `[Editing]`, `[Skill]`, `[Running]`) and deterministic completion output (including unified diffs for file edits).

**Non-Goals:**
- Fuzzy or lenient string matching for `edit_file` (strict exact-string replacement with uniqueness validation will be preserved).
- Dumping complete file read contents or skill markdown into the terminal output stream (visualizations will be concise headers and execution summaries).

## Decisions

### Decision 1: Centralized Event Stream Interception in `main.py`
We will capture `ToolExecutionStartEvent` and `ToolExecutionEndEvent` directly within the `async for event in agent.prompt_stream()` loop in `slash_agent/main.py`.
- *Rationale*: Keeps UI rendering logic cleanly separated from tool execution logic in `tools.py`, preventing duplicate print statements and ensuring a consistent terminal design.
- *Alternatives Considered*: Scattered print statements inside individual tool functions in `tools.py`. Rejected to maintain architectural clean separation.

### Decision 2: Session Initial Working Directory Tracking
We will introduce `session_state.initial_cwd` initialized at startup (`os.getcwd()`). For `write_file` and `edit_file`, after resolving the absolute path, the system compares the resolved path against `session_state.initial_cwd`. If the resolved path is outside this boundary, `risk_level` is automatically set to `critical`.
- *Rationale*: Protects the user's system by ensuring modifications outside the project/launch directory require explicit human approval.
- *Alternatives Considered*: Using project git root. Rejected because users may launch the shell in a specific subfolder or non-git directory.

### Decision 3: Tool Schema Registration Re-ordering
The tool array registered with `Agent` in `main.py` will be re-ordered to: `[read_file, write_file, edit_file, execute_command, request_user_input, read_skill_instructions]`.
- *Rationale*: Counteracts LLM positional bias towards early tools, making native file tools more prominent in function calling choices.

## Risks / Trade-offs

- **[Risk] Terminal ANSI Output Noise**: Streaming execution events alongside thinking deltas and PTY command output could lead to visual interleaving if formatting is inconsistent.
  - *Mitigation*: Ensure text deltas and tool event badges print clean line breaks (`\n`) and reset terminal formatting colors properly.
- **[Risk] Path Traversal via Symlinks**: Relative paths resolving outside `initial_cwd` via symlinks might bypass basic prefix checks.
  - *Mitigation*: Always run `os.path.realpath` before comparing against `session_state.initial_cwd`.
