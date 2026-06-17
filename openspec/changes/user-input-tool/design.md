## Context

The `slash-agent` orchestrator currently exposes only one tool to the LLM agent: `execute_command`. While this allows the agent to execute shell commands statefully, it has no way to ask the user clarifying questions when the requested task is unclear or ambiguous. Currently, the agent either fails or makes incorrect assumptions in such situations. Since command execution already requires explicit user confirmation, we only need a mechanism for the agent to request clarification when the initial task itself is underspecified.

## Goals / Non-Goals

**Goals:**
- Implement a new tool `request_user_input` for the agent.
- Allow the agent to interactively ask the user questions and receive string responses from the terminal.
- Support standard terminal line editing features (using Python's `input()` which hooks into `readline`).
- Gracefully handle user interrupts (Ctrl+C / EOF).
- Update the system prompt to guide the agent on when to ask questions.

**Non-Goals:**
- Supporting GUI prompts or multi-field forms.
- Re-implementing command validation or shell history within the input tool.

## Decisions

### 1. Synchronous Input inside Asyncio Executor
To avoid blocking the main asyncio event loop while waiting for user keystrokes, and to take full advantage of Python's built-in `input()` (which natively handles readline, arrow keys, and backspace on TTYs), we will run the input prompt inside a thread pool using `loop.run_in_executor`.

### 2. Styling and Coloring
To keep the visual presentation coherent with existing agent styling, the question will be prefaced with a cyan label `[Agent Question]` and the user input prompt will use a green `> ` indicator.
- Question formatting: `\033[1;36m[Agent Question] <prompt>\033[0m`
- Input indicator: `\033[1;32m> \033[0m`

### 3. Graceful Abort / Interrupt Handling
If the user types Ctrl+C or EOF (Ctrl+D) while being prompted, it should raise a `KeyboardInterrupt` or `EOFError`. We will catch this inside the executor/tool, print an abort message, and propagate a `KeyboardInterrupt` to abort the entire agent task execution immediately.

### 4. System Prompt Guidance
We will append explicit rules to the system prompt in `slash_agent/main.py` informing the agent that it can use `request_user_input` ONLY if the overall task is unclear or ambiguous (e.g., missing critical information needed to proceed). It MUST NOT use this tool to ask for permission to run commands or confirm individual steps, as those are already handled by the system's command confirmation prompt.

## Risks / Trade-offs

- **Risk**: The agent could end up in an infinite loop of asking questions.
  - **Mitigation**: Instruct the agent in the system prompt to use the tool sparingly and only when it cannot proceed on its own or when requirements are clearly missing.
- **Risk**: Terminal conflicts when running inside a PTY command execution or other interactive states.
  - **Mitigation**: The input tool will only be executed between command execution states (when the agent is deciding on its next action), so terminal ownership will be clean.
