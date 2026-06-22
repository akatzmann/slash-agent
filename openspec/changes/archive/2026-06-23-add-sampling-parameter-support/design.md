## Context

The `slash-agent` codebase delegates LLM streaming completions to the `py-agent-core` package. In standard operations, no `temperature` or `top_p` parameters are specified, defaulting to `0.7` (Ollama) or `1.0` (OpenAI). In certain coding or strict tool-use workflows, users benefit from more deterministic sampling. However, OpenAI's o-series reasoning models (such as `o1`/`o3`) throw API validation errors when custom sampling parameters are included. 

`py-agent-core` was recently reinstalled to support `temperature` and `top_p` in backend constructors. If these arguments are `None`, they are omitted from API requests, allowing both reasoning models and standard models to function correctly. This design integrates support for configuring these parameters in `slash-agent`.

## Goals / Non-Goals

**Goals:**
- Load `AGENT_TEMPERATURE` and `AGENT_TOP_P` from the configuration environment and forward them to the `py-agent-core` backend initialization calls in `slash_agent/main.py`.
- Keep the interactive configuration prompts inside `bin/installer.sh` clean and simple by automatically registering placeholders without interactive prompts (Option A).
- Document the parameters and their compatibility constraints in `.env.template`.

**Non-Goals:**
- Interactive prompts for temperature or top_p in the `bin/installer.sh` setup wizard.
- Dynamic error catching or retry logic in `slash-agent` (which is a concern of the client/backend library).

## Decisions

### 1. Silent Configuration Integration
* **Choice**: Option A (silent placeholders). Add `AGENT_TEMPERATURE` and `AGENT_TOP_P` to the installer's file verification loop and write them as empty placeholders.
* **Rationale**: Bypasses interactive prompts to keep the configuration wizard simple, while still ensuring the keys are visible and editable in the user's config file (`~/.config/slash-agent/env`).

### 2. Float Parsing with None Fallback
* **Choice**: Retrieve variables using `os.environ.get()` and parse them to floats only if they are not empty/None.
* **Rationale**: Empty strings or unset environment variables default to `None` in python, ensuring that the parameters are cleanly omitted from the payload for compatibility with OpenAI o-series reasoning models.

## Risks / Trade-offs

- **[Risk]** A user configures a global `AGENT_TEMPERATURE=0.2` and later runs a reasoning model (like an o-series model such as `o1`/`o3`), leading to a `400 Bad Request` API error.
  * **[Mitigation]** We will add explicit comments in `.env.template` warning users that configuring these parameters will cause API calls to fail on OpenAI o-series reasoning models that do not support custom temperature values.
