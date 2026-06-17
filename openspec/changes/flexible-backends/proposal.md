## Why

Currently, the agent only supports Ollama as a hardcoded backend in `slash_agent/main.py`. Since `py-agent-core` supports other backends (like Azure OpenAI, Ollama, etc.) and most developers/frameworks use OpenAI API endpoints, we should support generic OpenAI API endpoints as the default, and make the backend configurable via environment variables (supporting `openai`, `ollama`, `azure_openai`, and `dummy`).

## What Changes

- Add configurable backend selection via a new environment variable `AGENT_BACKEND`.
- Change default backend to `openai` (previously hardcoded to Ollama).
- Update default model and endpoint environment variables to support standard OpenAI models and endpoints by default (e.g. `gpt-4o-mini`).
- Support configuring generic OpenAI API endpoints via `AsyncOpenAI` client in `slash_agent/main.py`.
- Support standard backends: `openai` (default), `ollama`, `azure_openai`, and `dummy`.
- Update `bin/installer.sh` to prompt/setup the default backend and settings (or preserve existing behavior but adapt defaults).

## Capabilities

### New Capabilities
- `multi-backend-support`: Support multiple LLM backends (OpenAI, Ollama, Azure OpenAI, Dummy) and make OpenAI the default.

### Modified Capabilities

## Impact

- `slash_agent/main.py`: Initialize backend based on `AGENT_BACKEND`, `AGENT_ENDPOINT`, and `AGENT_MODEL`.
- `bin/installer.sh`: Support configuring the default backend during setup.
