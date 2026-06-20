## Why

Currently, slash-agent runs exclusively with thinking/reasoning features disabled (thinkingLevel: "off"), which prevents developers from taking advantage of advanced reasoning models (like o1/o3-mini or deepseek-r1) that output a chain-of-thought. Furthermore, after the initial installation, there is no straightforward way to re-configure the backend, model, endpoint, or API keys without manually finding and editing the hidden `.env` file, which is an error-prone and suboptimal user experience.

## What Changes

- **Thinking/Reasoning Mode Support**: Add a configurable environment variable `AGENT_THINKING_LEVEL` (`off`, `low`, `medium`, `high`) and pass it to the underlying `py-agent-core` orchestrator.
- **Reasoning Live Stream**: Detect `thinking_delta` stream events in the Python runner and display them in a visually distinct, styled layout (ANSI italics and dim gray) to separate the agent's chain-of-thought from its final responses and command outputs.
- **Interactive Re-configuration Command**: Support running `/agent --configure` (and/or `agent --configure`) to trigger the configuration prompts again.
- **Shell-Level Interception**: Intercept the `--configure`/`-c` flags directly inside the sourceable shell scripts (`bin/slash-agent.sh`, `bin/slash-agent.fish`) to launch the installer in config mode, bypassing Python entirely. This ensures configuration is robust even if the Python virtualenv is broken, and avoids capturing terminal context files unnecessarily.
- **Smart Installer Configuration**: Update `bin/installer.sh` to accept a `--configure` flag, load existing configurations from `.env` to pre-populate prompt defaults, and prompt users to configure the thinking level.

## Capabilities

### New Capabilities
- `thinking-mode`: Expose the ability to configure and stream the reasoning/thinking process from chain-of-thought and reasoning models with a distinct visual layout.

### Modified Capabilities
- `simple-installer`: Add re-configuration support to the installer script, enabling users to re-run configuration prompts pre-populated with existing `.env` values, and select the agent's thinking level.
- `github-documentation`: Document the new configuration system, thinking levels, and the `--configure` re-configuration option.

## Impact

- `slash_agent/main.py`: Read `AGENT_THINKING_LEVEL`, pass it to `Agent`, and handle `thinking_delta` events with styled terminal outputs.
- `bin/slash-agent.sh` and `bin/slash-agent.fish`: Intercept `--configure`/`-c` arguments to call `installer.sh --configure` directly.
- `bin/installer.sh`: Parse the `--configure` argument, read current `.env` variables to seed defaults, add prompts for thinking level, and write `AGENT_THINKING_LEVEL` to `.env`.
- `.env.template`: Add `AGENT_THINKING_LEVEL` to list of environment variables.
