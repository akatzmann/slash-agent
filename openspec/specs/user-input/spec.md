# user-input Specification

## Purpose
Exposes a tool `request_user_input` to the LLM agent, allowing it to prompt the user directly in the terminal to ask clarifying questions or request additional details during task execution.

## Requirements

### Requirement: Expose User Input Tool
The system SHALL expose a tool to the agent that allows it to prompt the user for arbitrary string input.

#### Scenario: Tool is exposed to the agent
- **WHEN** the agent initialization begins
- **THEN** the `request_user_input` tool is registered alongside the `execute_command` tool in the agent's initial state.

---

### Requirement: Prompt User for Input
The system SHALL present the prompt to the user in the terminal and capture the response.

#### Scenario: Prompting user successfully
- **WHEN** the agent calls `request_user_input` with a query
- **THEN** the system displays the query formatted in cyan as `[Agent Question] <query>` and waits for a line of text starting with a green `> ` prompt, returning the entered string back to the agent.

---

### Requirement: Handle Input Abort
The system SHALL handle user interrupts during input gracefully.

#### Scenario: User aborts the input prompt
- **WHEN** the user presses Ctrl+C or sends EOF (Ctrl+D) while the input prompt is active
- **THEN** the system terminates the prompt, prints a cancellation message, and raises `KeyboardInterrupt` to abort the agent execution.
