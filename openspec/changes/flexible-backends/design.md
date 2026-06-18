## Context

The current `slash_agent/main.py` is hardcoded to use the `OllamaBackend` and `AsyncClient` from the `ollama` library. The `py_agent_core` library has now been updated to include an `OpenAIBackend` adapter (in `py_agent_core.backends.openai`) that wraps `AsyncOpenAI` and supports any OpenAI-compatible endpoint. To enable flexible backend configuration, the code needs to be refactored to:
1. Use the library's `OpenAIBackend` as the default backend.
2. Read a new environment variable `AGENT_BACKEND` (defaulting to `openai`).
3. Dynamically initialize the backend corresponding to the user's configuration: `openai` (default), `ollama`, `azure_openai`, or `dummy`.
- Update `bin/installer.sh` to prompt for backend type and configure the `.env` settings accordingly.
- Support safe upgrade migration of existing `.env` files when running installer script in update mode.
- Add `.env.template` showcasing all backend variables and options.
- Update `README.md` and `docs/documentation.md` to document all supported backends and environment configurations.

## Goals / Non-Goals

**Goals:**
- Implement `OpenAIBackend` adapter.
- Support configuring the backend using `AGENT_BACKEND` (choices: `openai`, `ollama`, `azure_openai`, `dummy`), defaulting to `openai`.
- Support standard OpenAI endpoint configuration using `AGENT_ENDPOINT` and `AGENT_MODEL` (defaulting to `gpt-4o-mini`).
- Update `bin/installer.sh` to prompt for backend type and configure the `.env` settings accordingly.
- Safely update existing `.env` files with new configuration keys on installer update.
- Create `.env.template` with configuration examples.
- Document multi-backend setup in README and technical documentation.

**Non-Goals:**
- Support backends outside of the four standard types (`openai`, `ollama`, `azure_openai`, `dummy`).
- Re-architecting the agent runtime tool execution logic.

## Decisions

### 1. Using `OpenAIBackend` from `py_agent_core`
- **Decision**: Import and use the `OpenAIBackend` from `py_agent_core.backends.openai`. It takes an optional `AsyncOpenAI` client (allowing custom `base_url`/`api_key`) and a model name.
- **Rationale**: The `py_agent_core` library now ships `OpenAIBackend` directly, supporting both the official OpenAI API and any compatible endpoint (Ollama in OpenAI mode, vLLM, LM Studio, etc.) via `AsyncOpenAI(base_url=..., api_key=...)`.

### 2. Dynamic Initialization of Client/Backend
- **Decision**: Move backend-specific client imports (like `AsyncClient` and `OllamaBackend`) inside their respective initialization branches in `slash_agent/main.py`.
- **Rationale**: This prevents dependency loading issues if a particular library or backend is unused, and allows local clean imports.

### 3. Installer Script Backend Selection and Upgrade Path
- **Decision**: Add a step to `bin/installer.sh` prompting the user to select their desired LLM backend. If an existing `.env` is detected, parse it and append missing keys (`AGENT_BACKEND`, API key variables) rather than skipping config completely. If `AGENT_BACKEND` is missing, infer it from the existing `AGENT_ENDPOINT` (e.g., set to `ollama` if endpoint contains `:11434`).
- **Decision**: For the OpenAI backend prompt in the installer, provide a numbered list of common models (`gpt-4o-mini`, `gpt-4o`, `o1-mini`, `o1-preview`) with a custom fallback option.
- **Decision**: When the installer runs in update mode (`UPDATE_MODE=true`), run `pip uninstall -y py-agent-core` before running `pip install -r requirements.txt`.
- **Rationale**: Since OpenAI is now the default, we should allow configuring OpenAI (requiring API Key and model defaults) or choosing Ollama / other backends. Amending the `.env` on upgrade preserves compatibility for existing installations. Numbered menus for OpenAI models improve UX. Uninstalling the git dependency before reinstalling forces pip to fetch the latest remote commits, bypassing pip's package satisfaction cache.

### 4. Create Configuration Template and Documentation
- **Decision**: Create a `.env.template` showing all configuration environment variables. Update the environment variable sections in `README.md` and `docs/documentation.md` to reflect multi-backend support.
- **Rationale**: Makes backend configuration self-documenting and user-friendly.

## Risks / Trade-offs

- **Risk**: User selects OpenAI backend but does not configure `OPENAI_API_KEY`.
- **Mitigation**: Warn the user during installation and check for `OPENAI_API_KEY` at startup or runtime when `openai` backend is selected.
