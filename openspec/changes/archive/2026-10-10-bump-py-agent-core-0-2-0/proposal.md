## Why

When using reasoning models like `gpt-6.1-sol` via Azure OpenAI and OpenAI on `/v1/chat/completions`, previous versions of `py-agent-core` (<0.2.0) failed with HTTP 400 errors because function tools could not be combined with server-default reasoning effort. `py-agent-core` 0.2.0 has been released with automatic reasoning fallback and caching. Updating `slash-agent` to require `py-agent-core` v0.2.0 and modernizing default OpenAI and Azure OpenAI model settings to `gpt-6.1-sol` resolves this issue and brings default configurations in line with current standards.

## What Changes

- **Upgrade `py-agent-core` dependency**: Bump pinned git dependency in `requirements.txt` from `v0.1.2` to `v0.2.0`.
- **Modernize OpenAI/Azure model defaults in code**: Update `slash_agent/main.py` default model resolution for `openai` and `azure_openai` from `gpt-5.4-nano` to `gpt-6.1-sol`.
- **Modernize configuration template**: Update `.env.template` model descriptions and comments to reference `gpt-6.1-sol` for `openai` and `azure_openai`.
- **Update installer scripts**: Update default model configuration prompts and values in `bin/installer.sh` and `bin/installer.ps1`.
- **Update documentation**: Update `docs/documentation.md` and `README.md` to reflect `gpt-6.1-sol` as the default model for `openai` and `azure_openai`.

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `multi-backend-support`: Update the default model identifier for `openai` and `azure_openai` backends from `gpt-5.4-nano` to `gpt-6.1-sol`.

## Impact

- **Affected code**: `requirements.txt`, `slash_agent/main.py`, `.env.template`, `bin/installer.sh`, `bin/installer.ps1`, `docs/documentation.md`, `README.md`.
- **APIs**: Upgrades `py-agent-core` runtime engine to 0.2.0. Resolves 400 BadRequestErrors when running agentic queries with `gpt-6.1-sol`.
- **Dependencies**: Bumps `py-agent-core` from `v0.1.2` to `v0.2.0`.
