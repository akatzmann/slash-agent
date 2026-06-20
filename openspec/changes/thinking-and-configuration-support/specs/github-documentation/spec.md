## ADDED Requirements

### Requirement: Documentation for Thinking Mode and Re-configuration
The system documentation MUST include detailed instructions for configuring, using, and updating the agent's thinking level and running the re-configuration wizard.

#### Scenario: User reviews updated README.md or docs/documentation.md
- **WHEN** the user reads `README.md` or `docs/documentation.md`
- **THEN** they find:
  - Explanations of `AGENT_THINKING_LEVEL` and how different levels map to backend implementations (OpenAI reasoning effort, Ollama think parameters).
  - Explanations and visual examples of the live reasoning stream formatting in the terminal.
  - Instructions on using `/agent --configure` or `/agent -c` to update their local backend settings, endpoints, and variables interactively.
