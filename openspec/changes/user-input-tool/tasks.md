## 1. Implement User Input Tool

- [x] 1.1 Implement the `request_user_input` tool function in `slash_agent/tools.py` with `@tool` decorator.
- [x] 1.2 Use asyncio executor threads to run the input query synchronously while keeping the event loop non-blocking.
- [x] 1.3 Add exception handling inside the tool to capture Ctrl+C/Ctrl+D (KeyboardInterrupt/EOFError) and propagate/raise KeyboardInterrupt.

## 2. Integration and System Prompt Updates

- [x] 2.1 Register `request_user_input` in the tools list in `slash_agent/main.py`.
- [x] 2.2 Update the `system_prompt` in `slash_agent/main.py` with specific guidelines on when the agent should request user input.

## 3. Verification

- [x] 3.1 Verify tool functionality by running the agent on an ambiguous task and confirming it prompts and receives input correctly.
