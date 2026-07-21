## Context

`bin/installer.sh` offers 5 backend choices: OpenAI, Ollama, Local OpenAI API, Azure OpenAI, and Dummy. `bin/installer.ps1` previously skipped Option 3 (Local OpenAI API) and mapped Option 3 to Azure OpenAI. This caused Windows users to lack an interactive wizard for llama.cpp, vLLM, SGLang, and Xinference setups.

## Goals / Non-Goals

**Goals:**
* Add Option `[3] Local OpenAI API` to `bin/installer.ps1` to configure `local_openai`.
* Align menu numbers in `installer.ps1` to 1–5 to match `installer.sh`.
* Ensure `AGENT_BACKEND="local_openai"` is correctly saved and loaded in `.env`.

**Non-Goals:**
* Changing backend options or behavior in `slash_agent/main.py`.

## Decisions

### 1. Unified Backend Selection Menu in `bin/installer.ps1`
* **Menu Options:**
  - `[1] OpenAI`
  - `[2] Ollama (default)`
  - `[3] Local OpenAI API` (llama.cpp, vLLM, SGLang, Xinference, etc.)
  - `[4] Azure OpenAI`
  - `[5] Dummy`
* **`local_openai` Prompts:**
  - Endpoint URL [default: `http://127.0.0.1:8080/v1`]
  - Model name [default: `local-model`]
  - API Key (optional)

## Risks / Trade-offs

* **[Risk]** Existing PowerShell configuration scripts hardcoding Option 3 for Azure OpenAI.
  * *Mitigation:* The prompt explicitly states option labels and defaults to existing `$AgentBackend` when pre-configured.
