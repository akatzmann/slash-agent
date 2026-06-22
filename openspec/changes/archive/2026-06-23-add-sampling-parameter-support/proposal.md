## Why

Currently, `slash-agent` uses the underlying default model temperatures (typically `0.7` for Ollama and `1.0` for OpenAI). While standard models work well with these settings, these temperatures are unusually high for precise coding, syntax generation, and deterministic tool-calling workflows, leading to occasional hallucinations or validation errors. Furthermore, OpenAI's o-series reasoning models (such as o1/o3) do not support custom temperature parameters and crash with `400 Bad Request` errors if they are sent. Adding support for `AGENT_TEMPERATURE` and `AGENT_TOP_P` allows advanced users to configure lower, more precise temperatures for standard models, while leaving them blank (defaulting to `None`) avoids compatibility issues with o-series reasoning models.

## What Changes

- **Configure Sampling Parameters**: Retrieve and parse `AGENT_TEMPERATURE` and `AGENT_TOP_P` from the configuration/environment and pass them to backend constructor interfaces.
- **Verification Safeguards**: Ensure parameters are only passed if they are not `None` (omitting them entirely for OpenAI o-series reasoning models to prevent API errors).
- **Installer Integration (Option A)**: Automatically append `AGENT_TEMPERATURE` and `AGENT_TOP_P` as empty placeholder variables in the configuration file (`~/.config/slash-agent/env`), preserving them silently without forcing interactive prompting during setup.
- **Environment Template**: Update `.env.template` with documented placeholders explaining temperature and top_p.

## Capabilities

### New Capabilities
<!-- None, as we are modifying existing capabilities -->

### Modified Capabilities
- `multi-backend-support`: Add requirements for loading and applying `AGENT_TEMPERATURE` and `AGENT_TOP_P` options to standard backend configurations.
- `simple-installer`: Add requirements for appending, preserving, and writing `AGENT_TEMPERATURE` and `AGENT_TOP_P` configuration settings silently.

## Impact

- **Affected Code**: `slash_agent/main.py`, `bin/installer.sh`, `.env.template`.
- **APIs**: OpenAI/Azure OpenAI and Ollama backend client completions.
- **Dependencies**: Depends on the latest `py-agent-core` library which has been reinstalled to support `temperature` and `top_p` arguments in backend constructors.
