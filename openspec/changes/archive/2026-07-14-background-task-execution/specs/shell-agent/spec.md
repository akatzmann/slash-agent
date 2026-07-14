## ADDED Requirements

### Requirement: Background Process Execution
The system SHALL support running commands asynchronously in the background when the agent calls `execute_command` with a `background=True` parameter. Upon spawning, the system SHALL immediately return a unique `task_id` string rather than blocking.

#### Scenario: Running a background server process
- **WHEN** the agent calls `execute_command` with `command="npm run dev"` and `background=True`
- **THEN** the system spawns the process asynchronously and returns a unique task identifier (e.g. `task_1`) immediately.

---

### Requirement: Session-Bound Task Manager
The system SHALL maintain a global session process registry mapping active background tasks. On agent session termination (whether clean, crashed, or aborted), the system SHALL execute a teardown handler that terminates all registered background subprocesses:
- On POSIX, the system SHALL spawn child subprocesses in separate process groups and send `SIGTERM` followed by `SIGKILL` (after a 3-second grace period) to the entire process group.
- On Windows, the system SHALL associate child processes with an OS Job Object to propagate parent exit terminations automatically.
- On Linux/WSL2, the system SHALL conditionally leverage `prctl(PR_SET_PDEATHSIG, SIGTERM)` on process spawn.

#### Scenario: Agent terminates and reaps active background tasks
- **WHEN** the agent session exits while background processes are running
- **THEN** the teardown handler runs and terminates all active background tasks, preventing orphaned processes.

---

### Requirement: Background Task Control Interfaces
The system SHALL register three new tools:
1. `list_background_tasks`: Returns a list of active tasks with their status.
2. `get_task_logs`: Takes a `task_id` and optional `tail_lines` and returns the recent log buffer.
3. `kill_background_task`: Takes a `task_id` and forcefully terminates that task.

#### Scenario: Agent kills a background task
- **WHEN** the agent calls `kill_background_task` with a valid active `task_id`
- **THEN** the system terminates the subprocess and returns confirmation.

---

### Requirement: Tool Parameters & System Prompts for Backgrounding
The `background` parameter on `execute_command` SHALL be documented in the tool schema docstring to specify that it must be set to `true` when spawning persistent processes (e.g., servers, watchers), when executing tasks in parallel (e.g., concurrent client/server executions), or when running long-running operations (e.g., slow builds, test suites) that the agent wants to inspect irregularly while continuing work. The model system prompt SHALL instruct the agent to apply this logic, leaving the parallel scheduling and backgrounding decision entirely to the model's discretion.

#### Scenario: Agent checks tool schema for parallel command execution
- **WHEN** the agent inspects the tool schemas to decide how to run a client/server test concurrently
- **THEN** it sets `background=true` based on the schema guidelines to run the server in the background before spawning the client.

---

### Requirement: Documentation Update for Background Tasks
The system technical documentation (`docs/documentation.md`) SHALL be updated to describe the background task manager architecture, active task management tools, platform-specific cleanup boundaries (Job Objects, process groups, `prctl`), and CLI command logging flows.

#### Scenario: User opens documentation to inspect background execution
- **WHEN** the user reads `docs/documentation.md`
- **THEN** they see sections explaining how the background executor operates and lists the active tool commands.

---

### Requirement: Native Pausing Tool
The system SHALL register a native `wait_seconds` tool accepting a `seconds` integer argument. This tool SHALL pause execution asynchronously using `asyncio.sleep` and SHALL NOT execute subprocess shell commands or prompt the user for confirmation. The system prompt SHALL instruct the model to use the lowest reasonable pause time to minimize user latency.

#### Scenario: Agent pauses execution natively
- **WHEN** the agent calls `wait_seconds` with `seconds=5`
- **THEN** the system pauses for 5 seconds without prompting the user and returns confirmation.
