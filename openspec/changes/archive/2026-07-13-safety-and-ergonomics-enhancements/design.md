## Context

The current iteration of `slash-agent` has some developer ergonomics and safety context issues:
1. Automated safety checks override the agent's descriptive reasons in prompts.
2. Large files read by `read_file` flood the LLM context window because there is no native way to fetch a subset of lines.
3. Long or verbose command outputs clutter the user's screen and cause token bloat.

This design addresses these issues through a set of integrated improvements in output streaming, command logging, and line-bounded file reads.

## Goals / Non-Goals

**Goals:**
* Conserve the LLM context window by truncating files/command logs and providing line-range parameters.
* Improve terminal readability during verbose operations.
* Support a fully silent terminal execution mode for scripting.
* Preserve model descriptions alongside automated safety alerts.
* Store logs in a temporary cross-platform directory using `tempfile.gettempdir()`.

**Non-Goals:**
* Standardizing a separate tool for reading command logs (re-use `read_file` instead).
* Restructuring the main agent execution loop or state-synchronization protocol.
* Supporting separate stdout/stderr logs for PTY executions (multiplexing is kept as default).

## Decisions

### 1. Risk Augmentation
In `tools.py`, instead of doing `desc = "[system warning]"`, the wrapper functions (`execute_command`, `read_file`, `write_file`, `edit_file`) will concatenate the warnings:
```python
if risk_description.strip():
    desc = f"[System Alert] {system_warn} | [Model Reason] {risk_description.strip()}"
else:
    desc = f"[System Alert] {system_warn}"
```

### 2. Line-Bounded File Reads
Add `start_line` and `end_line` optional arguments to `read_file` in `tools.py`.
* Under the hood, the file will be read line-by-line, and only the requested window (1-indexed, inclusive) is returned.
* Display the requested line range parameters (e.g., `(Lines 10-15)`) directly next to the file path in the user confirmation prompt, so the user knows exactly what segment is being accessed.
* If parameters are absent and the file contains more than 800 lines:
  * Read the first 800 lines.
  * Append a warning notification specifying the exact line range read, total line count of the file, and syntax guide for line ranges:
    `[File Truncated: Read lines 1-800 of {total} total lines. Use read_file with start_line and end_line parameters to read remaining segments, e.g. start_line=801, end_line=1600.]`

### 3. Unified Transient Command Logging
* Every command run in `execute_command` will capture output and write it to `tempfile.gettempdir() + "/slash-agent/cmd_<run_id>.log"`.
* If output is large (>=20KB or >=200 lines):
  * Do not return the full text in the tool output.
  * Instead, return:
    `[Output Truncated: Size {size}KB. Full logs written to {log_path}. Showing last 100 lines: \n{tail_preview}\n Use the read_file tool with start_line/end_line to inspect specific segments of the log file.]`
* To prevent disk clutter during active use, the orchestrator tracks all log paths created during the session and registers a clean exit hook to delete them upon clean session exit, preserving them only if an abnormal termination or crash occurs.

### 4. Selective Terminal Streaming and `--silent` Flag
* Add a `--silent` flag to `main.py` arguments. If set, redirect command execution stdout prints to a null target, except on failure.
* For standard runs, if streaming exceeds 500 lines or 50KB, collapse terminal output to a status spinner. If the command crashes, dump the buffer to stdout/stderr.

## Risks / Trade-offs

* **[Risk]** The model might not know a file is truncated.
  * *Mitigation:* The truncation warning appended to the tool result is highly descriptive and explicitly instructs the model on how to query the remaining blocks.
* **[Risk]** Subprocess execution stdout/stderr multiplexing.
  * *Mitigation:* While separate streams would be useful, PTY execution naturally combines stdout and stderr. Since `slash-agent` simulates a real interactive shell, this combined output is what users expect. We preserve this simplicity.
