## Context

Synchronous blocking execution prevents the agent from running background servers, continuous linters, or watchers while it works. However, launching background tasks natively can easily cause orphaned processes if the orchestrator crashes or exits. This design establishes a session-bound process manager to handle these background tasks safely.

## Goals / Non-Goals

**Goals:**
* Allow asynchronous execution of shell commands via `background=True`.
* Track background process handles statefully inside the active session.
* Clean up all spawned subprocesses on exit to prevent resource leaks and orphans on POSIX and Windows (including WSL2).
* Provide dedicated status, logs, and termination tools to the agent.

**Non-Goals:**
* Supporting shell job control features (like `fg` / `bg` swapping) natively in the user's host shell shell context.
* Creating persistent background daemons that survive beyond the agent's active execution loop.

## Decisions

### 1. Process Spawning & Registry
We will update `slash_agent/tools.py` to maintain a global process registry `session_state.active_tasks = {}`.
When a command is called with `background=True`:
* Spawns using `subprocess.Popen(..., preexec_fn=os.setpgrp)` on POSIX to establish a new process group.
* Assigns a unique ID (`task_1`, `task_2`, etc.) and stores the `Popen` instance in `active_tasks`.

### 2. Cross-Platform Safe Cleanup
We will implement conditional OS binding inside a `teardown_tasks()` handler called via python's `atexit` module and the core orchestrator's `finally` block:
* **POSIX/Linux/WSL2:** Use `os.killpg(os.getpgid(proc.pid), signal.SIGTERM)` to kill the process group. If the process is still running after a 3-second delay, send `SIGKILL`.
* **Linux/WSL2 Special Override:** Use `ctypes` to invoke `prctl(PR_SET_PDEATHSIG, SIGTERM)` inside the child process spawn pipeline. This guarantees OS-level reaping if the parent Python program is killed with a `SIGKILL` (where `atexit` would fail to run).
* **Windows:** Use the `win32job` module to construct a Job Object. Attach each spawned subprocess to the Job Object. When the parent process terminates, Windows automatically terminates all processes in the job.

### 3. Management Tools
Register four new tool definitions:
* `list_background_tasks()`: Scans `active_tasks`, queries process statuses, and returns names/IDs.
* `get_task_logs(task_id, tail_lines=100)`: Reads the log file buffer on disk (redirected during spawning) and returns the requested tail slice.
* `kill_background_task(task_id)`: Terminates the process group statefully and removes it from `active_tasks`.
* `wait_seconds(seconds)`: Pauses agent loop via `asyncio.sleep` to let background tasks progress, avoiding shell prompt confirmation.

## Risks / Trade-offs

* **[Risk]** Platform compatibility of Windows Job Objects and Linux `prctl`.
  * *Mitigation:* The registry handles these conditionally using `sys.platform` checks. On systems where special bindings fail, the process manager falls back gracefully to standard `atexit` process termination checks.
* **[Risk]** Large background log buffers consuming disk space.
  * *Mitigation:* Redirect task outputs to `tempfile.gettempdir() + "/slash-agent/tasks/task_<id>.log"`, ensuring clean volatile storage.
