## ADDED Requirements

### Requirement: Initial Working Directory Recording
Upon agent startup in `slash_agent/main.py`, the system SHALL record `session_state.initial_cwd = os.getcwd()` to serve as the immutable workspace boundary anchor.

#### Scenario: Startup records initial working directory
- **WHEN** `slash-agent` is initialized
- **THEN** `session_state.initial_cwd` stores the current working directory path at launch time

### Requirement: Tool Registration Order
In `slash_agent/main.py`, the tools array supplied to `Agent` SHALL register native file tools (`read_file`, `write_file`, `edit_file`) before `execute_command`.

#### Scenario: Tool schemas ordered with native tools first
- **WHEN** `Agent` is instantiated in `main.py`
- **THEN** `read_file`, `write_file`, and `edit_file` are positioned at indices prior to `execute_command`

### Requirement: Central Event Streaming Handlers
The main async event loop in `main.py` SHALL handle `tool_execution_start` and `tool_execution_end` events from `agent.prompt_stream()` to render formatted terminal output badges for all tools.

#### Scenario: Central loop intercepts tool events
- **WHEN** any tool execution event fires during prompt streaming
- **THEN** `main.py` formats and prints the appropriate start badge and completion status directly to stdout
