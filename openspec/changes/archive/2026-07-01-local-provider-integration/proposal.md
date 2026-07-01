## Why

Local LLM runtimes (like `llama.cpp`'s `llama-server`, `vLLM`, `SGLang`, and `Xinference`) are standard tools for offline and private AI inference. Currently, users of `slash-agent` must manually configure these runtimes using the general `OpenAI` backend, which introduces friction because it requires manually setting dummy API keys, typing out custom ports, and manually configuring model identifiers without autocompletion or validation.

Natively supporting local OpenAI-compatible APIs in the configuration wizard and user documentation lowers the getting-started barrier and simplifies configuration for the entire local LLM ecosystem.

## What Changes

- Add a distinct "Local OpenAI-Compatible API" option directly in the interactive configuration wizard (`bin/installer.sh`).
- Automatically configure endpoint defaults, base URL suffix sanitization (auto-appending `/v1` if missing), and automatically populate dummy API keys.
- Probe the local service at setup time using its `/v1/models` endpoint to query and present loaded models for selection.
- Update the Technical Documentation (`docs/documentation.md`) and the Project Readme (`README.md`) to document configurations, default ports, and parameters (context size, threading, reasoning budget) for `llama.cpp`, `vLLM`, `SGLang`, and `Xinference`.

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `multi-backend-support`: Support configuring local OpenAI-compatible API providers natively, standardizing ports and model aliases under the same client backend.
- `simple-installer`: Modify the interactive configuration prompts to support Local OpenAI API option selection, local URL sanitization, and endpoint model autocompletion.

## Impact

- `bin/installer.sh`: Affected by the installer setup wizard menu additions, suffix sanitization, and model probing queries.
- `README.md` & `docs/documentation.md`: Updated to explain local OpenAI-compatible integrations and parameter matrices.
