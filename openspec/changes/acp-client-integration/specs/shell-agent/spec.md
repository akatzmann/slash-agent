## ADDED Requirements

### Requirement: ACP Client Mode Configuration
The system SHALL support launching in ACP client mode. It MUST support defining the external agent command using:
- The persistent `AGENT_ACP_SERVER_CMD` configuration/environment setting.
- The CLI parameter `--agent <command>` which overrides the configuration setting for the active session.

#### Scenario: Launching agent with a CLI command override
- **WHEN** the user executes `/agent --agent "claude --acp" "Fix this syntax error"`
- **THEN** the system launches in ACP Client mode, executing `claude --acp` to start the external agent.

---

### Requirement: External Agent Protocol Wrapper
When running in ACP client mode, the orchestrator in `main.py` SHALL:
1. Spawn the external agent as a child subprocess.
2. Communicate with the agent via standard I/O (stdin/stdout) using the JSON-RPC 2.0 protocol format.
3. Map incoming JSON-RPC tool/call requests from the external agent to the corresponding local python tools (`execute_command`, `read_file`, `write_file`, `edit_file`) to apply local safety confirmation gates.
4. Serialize tool execution outputs and return them to the external agent via JSON-RPC responses.

#### Scenario: External agent requests command execution
- **WHEN** the external agent requests a tool execution to run `git status` via JSON-RPC
- **THEN** the system intercepts the request, runs the local safety confirmation prompt, executes the command in the local PTY bridge, and returns the result back to the external agent.
