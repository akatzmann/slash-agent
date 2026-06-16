## Context

The repository provides a native shell agent integration. Currently, the code has detailed inline comments and a basic README, but lacks a concise technical developer/user document describing the internals (PTY bridge, environment syncing, shell hooks, and terminal scrollback extraction). To make the project accessible on GitHub, we need to design a concise technical overview document.

## Goals / Non-Goals

**Goals:**
- Add a new technical documentation file at `docs/documentation.md`.
- Describe the key architectural blocks (Bash hooks, tmux/history buffer context capture, Ollama backend, PTY fork/bridge, and environment variables/cwd state synchronization).
- Provide a summary of standard configuration options.

**Non-Goals:**
- Modify or change the executable behavior or command-line interface of the agent.
- Replace the main landing `README.md`.

## Decisions

### Decision 1: Separate file under `docs/documentation.md`
- **Option A (Chosen):** Create a separate, dedicated `docs/documentation.md` file.
  - *Rationale:* Keeps the root `README.md` focused on quick setup and features, while leaving detailed technical explanations to the documentation file.
- **Option B:** Inline everything into the main `README.md`.
  - *Rationale:* Would make the `README.md` excessively long and harder to digest for first-time visitors.

### Decision 2: Include detailed communication protocol specifications
- **Option A (Chosen):** Document the precise format of the synchronization token (`___AGENT_SHELL_STATE___`) and env dump protocol (`env -0`).
  - *Rationale:* Essential for developers who want to extend the project or port the agent to other shells (e.g., Zsh, Fish).

## Risks / Trade-offs

- **[Risk]** The documentation might become out-of-sync with code modifications (e.g. state syncing protocol changes).
  - *Mitigation:* Ensure any future changes to `agent_shell/tools.py` or `bin/agent-shell.sh` update `docs/documentation.md` as a checklist item.
