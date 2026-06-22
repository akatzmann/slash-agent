## MODIFIED Requirements

### Requirement: Flexible Environment Configuration
The agent system SHALL configure the chosen backend using the environment variables `AGENT_ENDPOINT`, `AGENT_MODEL`, `AGENT_TEMPERATURE`, `AGENT_TOP_P`, and other backend-specific variables (like `OPENAI_API_KEY`, `AZURE_OPENAI_API_KEY`). If no endpoint or model is specified:
- For `openai`: `AGENT_MODEL` defaults to `gpt-5.4-nano`, and the endpoint defaults to OpenAI's official endpoint.
- For `ollama`: `AGENT_ENDPOINT` defaults to `http://127.0.0.1:11434`, and `AGENT_MODEL` defaults to `gemma4:latest`.
- For `azure_openai`: `AGENT_MODEL` defaults to `gpt-5.4-nano`.
`AGENT_TEMPERATURE` and `AGENT_TOP_P` SHALL be parsed as floats if defined, and passed during construction of the standard LLM backend client instances. If not set or empty, they SHALL default to `None` and be completely omitted from the API request payloads to ensure compatibility with models that do not support custom sampling parameters (like o-series reasoning models).

#### Scenario: Defaulting configurations for Ollama
- **WHEN** the agent starts with `AGENT_BACKEND` set to `ollama` (or unset), and no model/endpoint environment variables are configured
- **THEN** the agent defaults to using the `gemma4:latest` model with `http://127.0.0.1:11434` endpoint.

#### Scenario: Backend initialization with temperature and top_p
- **WHEN** the agent starts and `AGENT_TEMPERATURE` is set to `0.2` and `AGENT_TOP_P` is set to `0.9`
- **THEN** it parses these values as floats and passes them to the backend client instance during construction.

#### Scenario: Backend initialization with empty temperature and top_p
- **WHEN** the agent starts and `AGENT_TEMPERATURE` and `AGENT_TOP_P` are unset or empty
- **THEN** they default to `None` and are omitted from the API request payloads.
