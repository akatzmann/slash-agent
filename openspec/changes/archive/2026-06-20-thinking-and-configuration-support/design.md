## Context

Currently, `slash-agent` has thinking level locked to `"off"`. Developers utilizing reasoning models (e.g., OpenAI o1/o3 or DeepSeek-R1) cannot see or use the agent's chain-of-thought. In addition, updating backend settings, models, or keys requires manual editing of `$INSTALL_DIR/.env`, which is undocumented and error-prone for most users.

## Goals / Non-Goals

**Goals:**
- Add support for `AGENT_THINKING_LEVEL` configuration via the environment and setup installer.
- Format `thinking_delta` stream events in the terminal UI with a dimmed, italicized style.
- Support interactive configuration via `/agent --configure` (or `/agent -c`).
- Intercept the configuration flag at the shell level in both Bash/Zsh and Fish integrations to run the configuration prompts directly, bypassing Python dependencies and context capture.
- Allow `installer.sh` to parse `--configure`, import existing `.env` values, and use them as prompt defaults.

**Non-Goals:**
- Supporting custom configuration TUIs beyond standard interactive terminal prompts in the installer script.
- Modifying `py-agent-core` backend library code.

## Decisions

### 1. Shell-Level Flag Interception for Re-configuration
- **Decision**: Intercept `--configure` and `-c` directly in the sourced shell scripts (`bin/slash-agent.sh`, `bin/slash-agent.fish`) rather than inside `slash_agent/main.py`.
- **Rationale**: If the virtual environment or python packages are broken, the user can still run `/agent --configure` to repair/fix their setup. Additionally, it skips writing temporary context files and capturing tmux screens which are unnecessary for configuration.
- **Alternatives Considered**: Python-level argument parsing (rejected due to dependency on Python working to run configuration).

### 2. Reuse `installer.sh` for Setup and Configuration
- **Decision**: Add a `--configure` flag to the main installer script rather than writing a separate configuration utility.
- **Rationale**: Keeps the codebase DRY. Model fetching, input validation, and `.env` writing logic are preserved in one place.
- **Alternatives Considered**: Writing a separate configuration shell script or Python utility.

### 3. Load Existing Config as Defaults
- **Decision**: Sourcing `.env` at the start of `installer.sh` if it exists, and using the loaded values to set default answers for all prompt questions.
- **Rationale**: Users should not have to re-enter API keys or endpoints just to toggle a model or thinking level. Sourced variables allow standard shell expansion default values: `$(prompt_user "..." "$EXISTING_VAL")`.
- **Alternatives Considered**: Always prompting with clean default values.

### 4. Separate Visual Streaming for Reasoning
- **Decision**: Track thinking state in `slash_agent/main.py` and format `thinking_delta` and `text_delta` with distinct terminal headers and escape codes:
  - Dimmed gray/italics (`\033[3;90m`) for the thinking stream.
  - Prefix with a bold `[Thinking...]` header.
  - Transit to normal output when a `text_delta` starts, preceded by `[Agent Response]`.
- **Rationale**: Clearly separates the chain-of-thought from the final text output and commands, resulting in a cleaner UI.
- **Alternatives Considered**: Merging reasoning and text outputs together, or hiding reasoning outputs entirely.

## Risks / Trade-offs

- **[Risk]** Enabling thinking level on unsupported models (e.g. `gpt-5.4-nano` on a non-reasoning endpoint) might cause API errors.
  - **Mitigation**: The `py-agent-core` backend library automatically falls back or logs warnings when invalid parameters like `reasoning_effort` are passed to unsupported models.
- **[Risk]** Overwriting `.env` on configure could erase custom user environment comments in `.env`.
  - **Mitigation**: This is acceptable for a configuration utility. The `.env` structure remains standard and simple.
