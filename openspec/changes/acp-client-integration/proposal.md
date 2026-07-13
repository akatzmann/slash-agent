## Why

Currently, `slash-agent` runs its own custom LLM backend direct-request orchestrator. While it supports Ollama and OpenAI-compatible endpoints, it cannot bridge external coding agents (like Claude Code or Copilot CLI) which use standard agent protocols.

This change integrates `slash-agent` as an ACP (Agent Client Protocol) Client, enabling it to act as the terminal shell harness (capturing local shell history, managing PTY processes, running safety prompts, and syncing parent shell environments) for any external ACP-compliant server agent via JSON-RPC 2.0.

## What Changes

* **ACP Client Orchestrator:** Implement an ACP client loop in `main.py` that spawns the external agent process and communicates via JSON-RPC 2.0 over standard streams.
* **Persistent Configuration:** Introduce `AGENT_ACP_SERVER_CMD` in configuration settings to define the default command to start the external agent (e.g., `claude --acp` or `copilot --acp`).
* **CLI Parameter:** Support the `--agent <command>` argument in `slash-agent` CLI to dynamically launch and wrap alternative external agents.
* **Tool Mapping:** Translate JSON-RPC tool calls from the external agent (such as file reads, writes, edits, and terminal execution) to local `slash-agent` tools, maintaining safety confirmation gates.

## Capabilities

### New Capabilities

*(None)*

### Modified Capabilities

- `shell-agent`: Integrate ACP Client mode, allowing the agent orchestrator to wrap external ACP servers via JSON-RPC over stdio.

## Impact

* **`slash_agent/main.py`:** Create ACP JSON-RPC protocol serialization and parsing; add `--agent` CLI parsing.
* **`slash_agent/tools.py`:** Connect tool execution callbacks to JSON-RPC request-response handlers.
* **Configuration:** Add `AGENT_ACP_SERVER_CMD` environment variable support.
