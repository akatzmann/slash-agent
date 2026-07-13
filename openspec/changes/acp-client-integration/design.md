## Context

To make `slash-agent` a universal terminal harness, we can implement support for the Agent Client Protocol (ACP) standard. In this model, `slash-agent` acts as an ACP Client that launches external ACP Server agents (such as Claude Code) and handles local safety prompts, environment state syncs, and terminal scrollback captures, while delegating core LLM reasoning to the external process.

## Goals / Non-Goals

**Goals:**
* Support execution of external agents via standard JSON-RPC 2.0 over standard I/O (stdin/stdout).
* Allow configuration of the agent command via environment variables (`AGENT_ACP_SERVER_CMD`) or CLI parameter (`--agent`).
* Intercept all file and terminal tools to ensure the local user confirmation prompt gates execution.
* Retain state sync protocol (PWD/Env variables updates) and context capture on agent exit.

**Non-Goals:**
* Implementing an ACP Server model (having editor plugins connect to `slash-agent`).
* Modifying external agent CLI code.

## Decisions

### 1. Process Wrapping & Execution
When running in ACP Client mode (triggered when `--agent` is passed or `AGENT_ACP_SERVER_CMD` is set):
* `main.py` spawns the external executable via `subprocess.Popen(shlex.split(cmd), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=sys.stderr, bufsize=0, text=True)`.
* It redirects standard error to the parent terminal directly so console messages are readable, but intercepts stdout and stdin.

### 2. JSON-RPC 2.0 Marshalling
A lightweight JSON-RPC loop is run in `main.py`:
* Reads lines from the subprocess stdout.
* Parses JSON-RPC request objects (e.g. `initialize`, `session/prompt`, `tool/call`).
* Maps incoming `tool/call` requests to the corresponding tools registered in `slash_agent/tools.py`.
* Runs the standard safety prompts and executes tools locally.
* Writes JSON-RPC response objects back to the subprocess stdin.

### 3. Safety Gating Integration
Because the external agent will request tasks (like `execute_command` or `write_file`) via JSON-RPC, `slash-agent` intercepts these calls before execution and invokes `prompt_user_confirmation` or `prompt_file_confirmation`. This ensures that even if wrapping an external agent, the user remains in absolute control of their local system.

## Risks / Trade-offs

* **[Risk]** Bidirectional tool dependencies or custom tool schemas.
  * *Mitigation:* The ACP client wrapper maps the protocol's standard tool calls to local commands. If the external agent demands a tool not present in `slash-agent`'s local tool set, the system replies with a standard JSON-RPC Method Not Found error.
* **[Risk]** Stdout/stderr pollution of JSON-RPC streams.
  * *Mitigation:* We use separate pipes for stdin/stdout, and print errors directly to the parent process's stderr stream to isolate JSON-RPC lines from diagnostic statements.
