# multi-backend-support Specification

## Purpose
Enables slash-agent to configure and run using different LLM backends (OpenAI, Azure OpenAI, Ollama, and offline Dummy mode) and custom models/endpoints dynamically based on environment configuration.

## Requirements

### Requirement: Configurable Backend Selection
The agent system SHALL support choosing the LLM backend dynamically via the environment variable `AGENT_BACKEND`. Supported backends SHALL include `openai`, `ollama`, `azure_openai`, and `dummy`. If `AGENT_BACKEND` is not set, it SHALL default to `ollama`.

#### Scenario: Backend defaulting to ollama
- **WHEN** the agent starts and `AGENT_BACKEND` is not set
- **THEN** the agent initializes using the Ollama backend.

#### Scenario: Ollama backend selection
- **WHEN** the agent starts and `AGENT_BACKEND` is set to `ollama`
- **THEN** the agent initializes using the Ollama backend.

---

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

---

### Requirement: Local API Endpoint Compatibility
The agent backend system SHALL allow the standard `openai` backend to connect to any local OpenAI-compatible HTTP API service (such as `llama-server`, `vLLM`, `SGLang`, or `Xinference`) when `AGENT_ENDPOINT` is configured to point to a local URI. In this configuration, standard chat completion requests SHALL be dispatched to the local service's Chat Completions endpoint, and the client SHALL supply a non-empty `OPENAI_API_KEY` (which defaults to a placeholder key if none is set in the environment) to satisfy standard client SDK requirements.

#### Scenario: Running agent with local llama.cpp endpoint
- **WHEN** the agent starts and `AGENT_BACKEND` is set to `openai`, `AGENT_ENDPOINT` is set to `http://127.0.0.1:8080/v1`, and `OPENAI_API_KEY` is set to `local-api-key`
- **THEN** standard API requests are successfully routed to the local llama-server completions endpoint.
