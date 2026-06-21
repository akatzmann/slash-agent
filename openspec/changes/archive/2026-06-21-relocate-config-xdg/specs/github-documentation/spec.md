## MODIFIED Requirements

### Requirement: Documentation for Thinking Mode and Re-configuration
The system documentation MUST include detailed instructions for configuring, using, and updating the agent's thinking level and running the re-configuration wizard. Additionally, all references to configuration parameters in `README.md` and `docs/documentation.md` SHALL guide the user to find and edit their settings in their XDG-standard user configuration directory (e.g. `~/.config/slash-agent/env`), explaining how custom path overrides (`SLASH_AGENT_CONFIG_FILE`) and fallback defaults operate.

#### Scenario: User reviews updated README.md or docs/documentation.md
- **WHEN** the user reads `README.md` or `docs/documentation.md`
- **THEN** they find:
  - Explanations of `AGENT_THINKING_LEVEL` and how different levels map to backend implementations (OpenAI reasoning effort, Ollama think parameters).
  - Explanations and visual examples of the live reasoning stream formatting in the terminal.
  - Instructions on using `/agent --configure` or `/agent -c` to update their local settings, endpoints, and variables interactively.
  - Explicit guidance pointing them to their user configuration file located at `~/.config/slash-agent/env` (or custom overrides) instead of the repository root `.env`.
