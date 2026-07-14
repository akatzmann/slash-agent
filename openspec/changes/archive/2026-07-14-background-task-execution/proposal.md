## Why

Currently, all command executions inside `slash-agent` are blocking and synchronous. If the agent starts a watcher (like `npm run dev`) or a background script, the entire agent session hangs indefinitely unless aborted by the user.

This change introduces asynchronous background process execution statefully tracked by a session-bound task manager, ensuring processes can be monitored and are automatically terminated on exit to prevent orphaned daemons.

## What Changes

* **Background Task Execution:** Add a `background` parameter to command execution, returning a `task_id` immediately.
* **Stateful Process Registry:** Track active background processes statefully in `session_state.active_tasks` to manage their lifecycles.
* **Orphan-Proof Cleanup Hooks:** Implement a cross-platform termination hook (using Python `atexit` / `try...finally` cleanups, OS process group signals on POSIX, and Job Objects on Windows) that forcefully reaps active background processes upon agent session exit.
* **Background Task Tools:** Introduce new tools (`list_background_tasks`, `get_task_logs`, `kill_background_task`, `wait_seconds`) to allow the model to manage and wait for services silently.

## Capabilities

### New Capabilities

*(None)*

### Modified Capabilities

- `shell-agent`: Add background task tracking, log querying, task termination tools, a native wait tool, and orphan-proof cleanup handlers.

## Impact

* **`slash_agent/tools.py`:** Create task execution wrappers and cleanup handles; add list, logs, kill, and wait tools.
* **`slash_agent/main.py`:** Register new task-management tools; update system prompts (directing wait usage) and setup process group flags.
