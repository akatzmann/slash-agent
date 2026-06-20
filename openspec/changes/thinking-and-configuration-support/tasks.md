## 1. Environment & Python Core Implementation

- [x] 1.1 Add `AGENT_THINKING_LEVEL` configuration variable to `.env.template`
- [x] 1.2 Update `slash_agent/main.py` to read `AGENT_THINKING_LEVEL` from the environment, defaulting to `"off"`, and pass `"thinkingLevel"` to `Agent` initial state
- [x] 1.3 Update `slash_agent/main.py` event loop to detect and format `thinking_delta` events, wrapping them with visual headers `[Thinking...]` and `[Agent Response]` and styling them in ANSI italics and dim gray

## 2. Shell Integration Interception

- [x] 2.1 Modify `bin/slash-agent.sh` to intercept `--configure` and `-c` options and call `installer.sh --configure` directly
- [x] 2.2 Modify `bin/slash-agent.fish` to intercept `--configure` and `-c` options and call `installer.sh --configure` directly

## 3. Installer Updates

- [x] 3.1 Modify `bin/installer.sh` to support command-line argument parsing and identify `--configure` / `-c` flags
- [x] 3.2 Modify `bin/installer.sh` to source current `.env` configuration (if it exists) and pre-populate all interactive prompt default answers with existing values
- [x] 3.3 Modify `bin/installer.sh` to include a prompt selection for thinking level and write the selected value to `AGENT_THINKING_LEVEL` in `.env`
- [x] 3.4 Modify `bin/installer.sh` configuration mode logic to skip clone, virtual environment creation, pip installation, and profile registration when in configure-only mode

## 4. Documentation

- [x] 4.1 Update `README.md` to document the new `AGENT_THINKING_LEVEL` configuration variable and the `/agent --configure` (or `/agent -c`) command
- [x] 4.2 Update `docs/documentation.md` to explain thinking mode integration, live reasoning stream presentation, and re-configuration design details

## 5. Verification

- [x] 5.1 Verify `/agent --configure` and `/agent -c` intercept correctly in Bash/Zsh and load the configuration prompts
- [x] 5.2 Verify `agent --configure` and `agent -c` intercept correctly in Fish and load the configuration prompts
- [x] 5.3 Verify that configuration prompts display existing `.env` values as defaults, and that updating values overwrites `.env` correctly
- [x] 5.4 Verify that enabling `AGENT_THINKING_LEVEL` prints live reasoning streams visually separated with `[Thinking...]` headers in dim italics
- [x] 5.5 Verify that all documentation changes are complete and reflect the final implementation details

