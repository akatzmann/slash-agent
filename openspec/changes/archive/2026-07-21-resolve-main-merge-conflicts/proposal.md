## Why

Merging `origin/main` into `feature/experimental-powershell-support` introduced conflict markers in `slash_agent/tools.py` and `openspec/specs/shell-agent/spec.md`. This change resolves those conflicts by adapting Windows command execution to match `main`'s 3-tuple command logging architecture, combining Windows administrative risk patterns with dynamic security warning merging, and consolidating capability specifications.

## What Changes

* **3-Tuple Windows Execution Signature:** Update `run_command_windows` in `slash_agent/tools.py` to return `Tuple[int, str, str]` (`exit_code`, `output`, `log_path`) and write Windows execution logs to transient log files inside `/tmp/slash-agent/`.
* **Combined Security Risk Patterns:** Merge Windows administrative patterns (`remove-item`, `del /s`, `format`, etc.) into `critical_patterns` in `slash_agent/tools.py` while preserving dynamic warning concatenation from `main`.
* **Consolidated Capability Specs:** Merge Windows requirements with Logging, Safety, and Background execution requirements in `openspec/specs/shell-agent/spec.md`.

## Capabilities

### New Capabilities

*(None)*

### Modified Capabilities

- `shell-agent`: Reconcile Windows execution bridge with unified command logging and dynamic warning formatting.

## Impact

* **`slash_agent/tools.py`**: Update `run_command_windows` return signature and combine risk patterns.
* **`openspec/specs/shell-agent/spec.md`**: Merge and deduplicate requirements.
