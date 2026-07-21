## Context

Currently, connecting `slash-agent` to local OpenAI-compatible runners (such as `llama-server`, `vLLM`, `SGLang`, or `Xinference`) requires selecting the general `OpenAI` cloud backend in the wizard and manually supplying cloud-centric parameters. This design defines how the wizard handles local-compatible endpoints, defaults, model probing, and base URL sanitization.

## Goals / Non-Goals

**Goals:**
- Add a dedicated "Local OpenAI-Compatible API" option to `/agent --configure` to simplify setup.
- Enable automatic fallback keys, endpoint suffix sanitization, and automated loaded-model autocompletion.
- Standardize local LLM documentation under a unified section in `docs/documentation.md`.

**Non-Goals:**
- Do not write any new Python backend classes (leverage the existing `OpenAIBackend`).
- Do not automate the starting or provisioning of local backend server processes (e.g., we do not run docker containers or CLI server scripts for the user).

## Decisions

### Decision 1: Setup Wizard Option Mapping
- **Option A (Chosen):** Map the new local provider option directly to the standard Python `openai` client.
  - *Rationale:* Since all local runners implement the standard `/v1/chat/completions` API protocol, standard client calls are completely identical. This avoids codebase fragmentation.
- **Option B:** Create a separate Python backend wrapper for `llamacpp` or `vllm`.
  - *Rationale:* Rejected because it introduces redundant client initialization logic.

### Decision 2: API Key Configuration
- **Option A (Chosen):** Automatically write a dummy string (`local-api-key`) in the configuration file if no custom key is provided.
  - *Rationale:* Bypasses mandatory OpenAI Python SDK client parameter verification checks without manual user input.

### Decision 3: Suffix Sanitization
- **Option A (Chosen):** Inspect the user-supplied local API URL and append `/v1` if missing.
  - *Rationale:* Standard client SDKs append `/chat/completions` directly to the base URL, which fails (returning a `404`) if the base URL lacks `/v1`. Auto-appending this suffix prevents routing crashes.

### Decision 4: Dynamic Model Probing
- **Option A (Chosen):** Probe the local endpoint using python's `urllib.request` library.
  - *Rationale:* Provides a seamless autocompletion menu matching the active state of the user's running local server. Bypasses proxy handlers to ensure local connectivity.

## Risks / Trade-offs

- **[Risk]** The local server is offline during configuration.
  - *Mitigation:* The probing logic catches connection errors and timeouts gracefully, printing a warning and prompting the user for manual configuration (defaulting to `gemma4-27b`).
- **[Risk]** Proxy environment variables block localhost connections.
  - *Mitigation:* The probe code explicitly disables system proxy handlers during local queries.
