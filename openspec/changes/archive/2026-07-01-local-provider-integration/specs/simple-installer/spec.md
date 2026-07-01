## MODIFIED Requirements

### Requirement: Support Configure-Only Mode with Pre-populated Defaults
The installer script MUST support running with a `--configure` or `-c` flag. In this mode, the installer SHALL bypass setup checks and repository cloning, load existing configuration variables from the configuration file if available, and prompt the user to configure their settings, using the existing configurations as default choices.

The configuration wizard MUST support configuring OpenAI, Ollama, Azure OpenAI, Local OpenAI-Compatible APIs (such as llama.cpp, vLLM, SGLang, Xinference), and Dummy backends. When configuring a Local OpenAI-Compatible API:
1. The wizard SHALL prompt for a local API base URL, defaulting to `http://127.0.0.1:8080/v1` (llama.cpp default) or the existing configured endpoint.
2. If the user-supplied endpoint URL is missing the `/v1` suffix path, the wizard SHALL automatically append `/v1` to standardize base URL routing for the client.
3. The wizard SHALL attempt to query the `/v1/models` endpoint of the active service. If the server is online, it SHALL display the currently loaded models in a numbered list for user selection. If offline or no models are returned, it SHALL prompt the user to type a model alias manually, defaulting to `gemma4-27b`.
4. If no custom API key is present in the environment or configuration, the wizard SHALL default the `OPENAI_API_KEY` to `local-api-key` to bypass standard client SDK checks.

#### Scenario: Running configuration on an already installed setup
- **WHEN** the installer is invoked with the `--configure` or `-c` flag and the configuration file exists in the user's config directory
- **THEN** it skips virtual environment setup, clones, and prerequisite checks, loads existing configurations, uses them as defaults in interactive prompts, and writes updated values to the configuration file with secure `600` permissions.

#### Scenario: Configuring Local OpenAI API with endpoint suffix sanitization
- **WHEN** the user selects the Local OpenAI API option and enters `http://127.0.0.1:8000` (without `/v1`)
- **THEN** the wizard automatically sanitizes the URL to `http://127.0.0.1:8000/v1` before saving.

#### Scenario: Configuring Local OpenAI API with active model probing
- **WHEN** the user selects the Local OpenAI API option and the local server is online exposing active models
- **THEN** the wizard fetches the loaded models via the `/v1/models` API endpoint and presents them as numbered options for the user to select.

---

### Requirement: Local Probe Proxy Bypass
During the automated prerequisite check and configuration phase, the installer script SHALL bypass any configured system proxies when probing local service endpoints (specifically when checking Ollama models via `127.0.0.1:11434` or local OpenAI-compatible API models via local addresses).

#### Scenario: Probing local Ollama behind a proxy
- **WHEN** the installer is executed in an environment with `http_proxy` configured and attempts to fetch Ollama models from `http://127.0.0.1:11434`
- **THEN** it SHALL bypass all proxy handlers, query the local Ollama instance directly, and retrieve the model list successfully.

#### Scenario: Probing local OpenAI API behind a proxy
- **WHEN** the installer is executed in an environment with `http_proxy` configured and attempts to fetch local models from `http://127.0.0.1:8080/v1/models`
- **THEN** it SHALL bypass all proxy handlers, query the local API instance directly, and retrieve the model list successfully.
