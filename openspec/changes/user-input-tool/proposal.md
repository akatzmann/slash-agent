## Why

Currently, the agent has no structured way to ask the user clarifying questions or prompt them for input (e.g., when a task has ambiguous details, missing parameters, or requires configuration decisions). When the agent runs into these situations, it must either guess or fail and exit. Introducing a dedicated tool for user input allows the agent to dynamically request and receive user input mid-task.

## What Changes

- **Add `request_user_input` tool**: Implement a new tool in the Python agent orchestrator that can prompt the user with a question/prompt in the terminal, block until they respond, and return the response to the agent.
- **Register the tool**: Add `request_user_input` to the agent's active tools in `slash_agent/main.py`.
- **System Prompt Guidelines**: Update the agent's system prompt instructions to clarify when it should use `request_user_input` instead of failing or making risky assumptions.

## Capabilities

### New Capabilities
- `user-input`: Allow the agent to interactively ask the user for information or clarification mid-run.

### Modified Capabilities

## Impact

- `slash_agent/tools.py`: A new `request_user_input` tool function decorated with `@tool`.
- `slash_agent/main.py`: The tool is registered in the list of available tools, and the system prompt is updated with instructions on using the user input tool.
