## Why

Developers frequently need quick assistance or automation directly inside their active shell sessions. Conventional LLM tools require copying and pasting code, context, and error logs between the terminal and browser. A native shell agent integration allows the user to invoke an LLM directly in their active shell (e.g. `/agent Fix this issue`), diagnose errors using tmux pane capture or command history, and execute corrective commands interactively with native terminal features (like `sudo` passwords) intact.

## What Changes

- **Shell Integration Script (`bin/agent-shell.sh`):** Introduces a sourceable Bash script that defines a `/agent` function.
- **Context Capture:** Captures the recent terminal history (using `tmux capture-pane` if in tmux, falling back to Bash `history`).
- **Interactive PTY Execution Bridge:** Executes subprocess commands in a pseudo-terminal (PTY) to support interactive stdin (e.g. `sudo` prompts) while capturing stdout/stderr and stripping ANSI escape codes.
- **State Synchronization:** Automatically syncs directory changes (`cd`) and environment changes from the agent's subprocess back to the parent shell.
- **Interactive Confirmation UX (`y/n/e/c`):** Prompt the user before executing commands: Yes, No, Edit (inline editing), or Comment (provide steering feedback).
- **Options and Flags:** Support `-y` (auto-confirm) and `-n`/`--dry-run` (simulate execution).

## Capabilities

### New Capabilities
- `shell-agent`: Provides an interactive terminal command-execution environment powered by an LLM agent, utilizing PTY-bridged subprocess execution, contextual tmux/history parsing, and shell state synchronization.

### Modified Capabilities
<!-- None -->

## Impact

- Adds new Python package `slash_agent` in `slash_agent/` directory.
- Adds `bin/slash-agent.sh` script to be sourced.
- Does not modify any existing codebase files (clean addon).
- Requires the orchestrator package `py-agent-core` to be installed (e.g. from GitHub) in the virtualenv Python environment.
