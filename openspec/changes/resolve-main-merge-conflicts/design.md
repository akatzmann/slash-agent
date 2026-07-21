## Context

Merging `origin/main` into `feature/experimental-powershell-support` caused conflict markers in `slash_agent/tools.py` and `openspec/specs/shell-agent/spec.md`. `origin/main` introduced a 3-tuple return signature `(exit_code, output, log_path)` for command logging and dynamic warning formatting, while `feature/experimental-powershell-support` introduced `run_command_windows` and Windows risk patterns.

## Goals / Non-Goals

**Goals:**
* Update `run_command_windows` to instantiate a command log file via `create_command_log_file()` and return `Tuple[int, str, str]` (`exit_code`, `output`, `log_path`).
* Combine Windows administrative patterns into `critical_patterns` in `slash_agent/tools.py` while applying dynamic warning concatenation.
* Consolidate requirement sections cleanly in `openspec/specs/shell-agent/spec.md`.

**Non-Goals:**
* Rewriting PTY or subprocess spawning architecture.

## Decisions

### 1. Unified 3-Tuple Return Signature for Windows Execution
* **`run_command_windows(command)`**:
  * Calls `log_file, log_path = create_command_log_file()`.
  * Redirects Windows `subprocess.Popen` stdout/stderr to `log_file`.
  * Returns `(exit_code, cleaned_output, log_path)`.

### 2. Risk Pattern Consolidation
* Combine Unix (`rm -rf`, `sudo`, `dd`) and Windows (`remove-item -recurse`, `remove-item -r`, `del /s`, `format `, `takeown`, `icacls`, `runas`) patterns into `critical_patterns`.
* Apply dynamic warning string formatting: `desc = f"[System Warning] {warning} | [Model Reason] {desc}" if desc else f"[System Warning] {warning}"`.

## Risks / Trade-offs

* **[Risk]** Log handle leakage on Windows subprocess exit.
  * *Mitigation:* Ensure `log_file.close()` is called safely after process spawn or completion.
