# multi-backend-support Specification

## Purpose
Enables slash-agent to configure and run using different LLM backends (OpenAI, Azure OpenAI, Ollama, and offline Dummy mode) and custom models/endpoints dynamically based on environment configuration.

## Requirements

### Requirement: Configurable Backend Selection
The agent system SHALL support choosing the LLM backend dynamically via the environment variable `AGENT_BACKEND`. Supported backends SHALL include `openai`, `ollama`, `azure_openai`, and `dummy`. If `AGENT_BACKEND` is not set, it SHALL default to `openai`.

#### Scenario: Backend defaulting to openai
- **WHEN** the agent starts and `AGENT_BACKEND` is not set
- **THEN** the agent initializes using the generic OpenAI backend.

#### Scenario: Ollama backend selection
- **WHEN** the agent starts and `AGENT_BACKEND` is set to `ollama`
- **THEN** the agent initializes using the Ollama backend.

---

### Requirement: Flexible Environment Configuration
The agent system SHALL configure the chosen backend using the environment variables `AGENT_ENDPOINT`, `AGENT_MODEL`, and other backend-specific variables (like `OPENAI_API_KEY`, `AZURE_OPENAI_API_KEY`). If no endpoint or model is specified:
- For `openai`: `AGENT_MODEL` defaults to `gpt-5.4-nano`, and the endpoint defaults to OpenAI's official endpoint.
- For `ollama`: `AGENT_ENDPOINT` defaults to `http://127.0.0.1:11434`, and `AGENT_MODEL` defaults to `gemma4:latest`.
- For `azure_openai`: `AGENT_MODEL` defaults to `gpt-5.4-nano`.

#### Scenario: Defaulting configurations for OpenAI
- **WHEN** the agent starts with `AGENT_BACKEND` set to `openai` (or unset), and no model/endpoint environment variables are configured
- **THEN** the agent defaults to using the `gpt-5.4-nano` model with OpenAI standard client configuration.
