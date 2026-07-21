## 1. CLI & Launch Configuration

- [ ] 1.1 Support parsing the `--agent <command>` parameter in `slash_agent/main.py`.
- [ ] 1.2 Read the persistent `AGENT_ACP_SERVER_CMD` setting from config files.
- [ ] 1.3 Implement child subprocess launch routing using `subprocess.Popen` with separate stdin/stdout streams.

## 2. JSON-RPC 2.0 Client Loop

- [ ] 2.1 Write standard JSON-RPC 2.0 message parsers and response builders in `slash_agent/main.py`.
- [ ] 2.2 Implement the main input/output stream line reader loop to coordinate communication with the external agent.
- [ ] 2.3 Ensure error codes (e.g. Method Not Found, Invalid Request) are serialized in accordance with standard JSON-RPC specs.

## 3. Local Tool Gating & Response Routing

- [ ] 3.1 Map external JSON-RPC tool calls to local tools (`execute_command`, `read_file`, `write_file`, `edit_file`).
- [ ] 3.2 Ensure safety gating checks (risk classification and confirmation prompts) are executed before returning tool execution results.
- [ ] 3.3 Pipe tool completion results back to the external agent via JSON-RPC responses.

## 4. Verification

- [ ] 4.1 Write a mock ACP server script to validate JSON-RPC handshakes and tool executions.
- [ ] 4.2 Run integration tests wrapping an ACP agent and verify that local PTY prompts and parent shell state synchronizations occur normally.
