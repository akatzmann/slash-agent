## ADDED Requirements

### Requirement: Local API Endpoint Compatibility
The agent backend system SHALL allow the standard `openai` backend to connect to any local OpenAI-compatible HTTP API service (such as `llama-server`, `vLLM`, `SGLang`, or `Xinference`) when `AGENT_ENDPOINT` is configured to point to a local URI. In this configuration, standard chat completion requests SHALL be dispatched to the local service's Chat Completions endpoint, and the client SHALL supply a non-empty `OPENAI_API_KEY` (which defaults to a placeholder key if none is set in the environment) to satisfy standard client SDK requirements.

#### Scenario: Running agent with local llama.cpp endpoint
- **WHEN** the agent starts and `AGENT_BACKEND` is set to `openai`, `AGENT_ENDPOINT` is set to `http://127.0.0.1:8080/v1`, and `OPENAI_API_KEY` is set to `local-api-key`
- **THEN** standard API requests are successfully routed to the local llama-server completions endpoint.
