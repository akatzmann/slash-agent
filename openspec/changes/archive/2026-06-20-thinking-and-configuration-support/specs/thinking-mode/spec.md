## ADDED Requirements

### Requirement: Configuration of Thinking Level via Environment
The slash-agent core Python module MUST read the thinking level from the `AGENT_THINKING_LEVEL` environment variable. The value SHALL default to `off` if not set. Valid values are `off`, `low`, `medium`, and `high`. This value MUST be passed to the `py-agent-core` initialization dictionary under the `thinkingLevel` key.

#### Scenario: Running slash-agent with default thinking level
- **WHEN** the agent starts and `AGENT_THINKING_LEVEL` is not set or empty
- **THEN** it initializes the Agent class with `thinkingLevel` set to `"off"`.

#### Scenario: Running slash-agent with custom thinking level
- **WHEN** the agent starts and `AGENT_THINKING_LEVEL` is set to `medium`
- **THEN** it initializes the Agent class with `thinkingLevel` set to `"medium"`.

### Requirement: Live Streaming of Thinking Phase
The slash-agent CLI interface MUST output thinking/reasoning deltas visually separated from the final text response. It MUST listen for `thinking_delta` assistant message updates and output them to stdout in a styled format.

#### Scenario: Agent streams reasoning tokens
- **WHEN** `slash_agent/main.py` receives a `message_update` event with type `thinking_delta`
- **THEN** it prefixes the thinking phase with a bold `[Thinking...]` header, prints the stream using ANSI dim italics (`\033[3;90m`), and closes the block with a bold green `[Agent Response]` header when regular text tokens begin.

### Requirement: Shell Interception for Configuration
The shell integration functions in `slash-agent.sh` and `slash-agent.fish` MUST intercept configuration arguments (`--configure` and `-c`). When intercepted, they SHALL bypass terminal context capture and Python execution, running the installer script in configure mode directly.

#### Scenario: Invoking agent with configure flag
- **WHEN** the user executes `/agent --configure` or `agent -c`
- **THEN** the shell function intercepts the flag, calls `installer.sh --configure`, and exits without invoking the python subprocess or writing context files.
