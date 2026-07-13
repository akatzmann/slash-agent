## Why

The current safety, file-reading, and command-execution models of `slash-agent` have minor UX limitations. Specifically, automated safety overrides discard rich context explanations from the model, there is no native support for partial/linewise file reading (causing context window bloat), and verbose command execution can pollute the user's terminal scrollback and overwhelm the model's history. 

This change introduces risk description augmentation, smart selective streaming with auto-collapse, partial file read parameters, and transient file logging of command outputs to optimize developer experience, safety clarity, and context efficiency.

## What Changes

* **Risk Augmentation:** Safety warning prompts will concatenate the system's hardcoded safety alert with the model's custom context description, rather than discarding the latter.
* **Selective Command Output & Previews:** Subprocess executions will monitor output length. If output exceeds 500 lines or 50KB, the live terminal display collapses to a status indicator, and only a preview is returned to the model. An explicit `--silent` flag will hide command output entirely, auto-dumping logs only on execution failure.
* **Partial File Reading:** The `read_file` tool will support optional `start_line` and `end_line` parameters. If a large file is queried without ranges, the tool returns a truncated preview with metadata (total lines and size) to guide the model on paginating.
* **Unified Command Logging:** All command output is saved to transient files inside the platform-independent temporary directory. If command output is large, the agent returns a preview and points the model to the log file, which it can read using `read_file`.

## Capabilities

### New Capabilities

*(None)*

### Modified Capabilities

- `command-risk-assessment`: Risk warnings will concatenate automated alerts and model reasons.
- `file-read`: The tool will support partial file reading via optional line bounds and supply size metadata on truncation.
- `shell-agent`: Implement selective command output streaming, a `--silent` flag, and transient log file writing for large outputs.

## Impact

* **`slash_agent/tools.py`:** Update `read_file` tool signature, update execution log persistence, and adjust PTY bridge.
* **`slash_agent/main.py`:** Update system prompt instructions for output minimization and file read ranges.
* **Documentation:** Add `docs/security_model.md` to outline safety tiers and path limits; update `SECURITY.md` supported versions list to reflect `v0.2.x`.
