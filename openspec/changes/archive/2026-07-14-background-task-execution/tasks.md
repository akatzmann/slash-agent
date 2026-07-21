## 1. Background Task Spawning & Registry

- [x] 1.1 Add `background` boolean parameter to `execute_command` inside `slash_agent/tools.py`.
- [x] 1.2 Setup log redirection to `tempfile.gettempdir() + "/slash-agent/tasks/task_<id>.log"` when spawning background processes.
- [x] 1.3 Maintain `session_state.active_tasks` dictionary mapped by a unique `task_id` containing the process metadata and objects.
- [x] 1.4 Update the docstring description of `execute_command` to explicitly guide the model on when to set `background=true`.

## 2. Cross-Platform Process Cleanup

- [x] 2.1 Register global cleanup handlers via Python `atexit` and `try...finally` to terminate all background subprocesses on exit.
- [x] 2.2 Implement POSIX process group configuration (`os.setpgrp`) and group signaling (`os.killpg`) to kill the process trees safely.
- [x] 2.3 Implement Windows Job Object creation and binding using `win32job` to propagate termination signals.
- [x] 2.4 Integrate Linux/WSL2 conditional `prctl(PR_SET_PDEATHSIG)` handler for subprocess spawning.

## 3. Task Management Tools & Documentation

- [x] 3.1 Implement `list_background_tasks` tool returning active tasks and statuses.
- [x] 3.2 Implement `get_task_logs` tool returning a tail slice of the transient task log.
- [x] 3.3 Implement `kill_background_task` tool to terminate task process groups statefully.
- [x] 3.4 Register the new tools in `slash_agent/main.py`.
- [x] 3.5 Update system prompt instructions in `slash_agent/main.py` directing the model to set `background=true` for persistent operations (dev servers, watchers, infinite streams).
- [x] 3.6 Update technical documentation in `docs/documentation.md` describing the background task manager architecture, parameters, and cleanup guarantees.
- [x] 3.7 Implement native `wait_seconds` tool, register it, and instruct the model to use the lowest reasonable time.

## 4. Verification

- [x] 4.1 Write unit tests validating cleanup loops and process terminations.
- [x] 4.2 Validate manual termination by spawning long-running background tasks and checking system processes on exit.
- [x] 4.3 Write unit tests for `wait_seconds`.
