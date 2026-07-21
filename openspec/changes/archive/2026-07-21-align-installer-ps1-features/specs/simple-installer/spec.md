## ADDED Requirements

### Requirement: Cross-Platform Backend Selection Parity
The PowerShell installer (`installer.ps1`) SHALL provide identical backend configuration options to `installer.sh`, including Option `[3]` for `local_openai` (llama.cpp, vLLM, SGLang, Xinference) and matching menu numbering 1–5.

#### Scenario: User configures Local OpenAI API in PowerShell installer
- **WHEN** the user runs `installer.ps1` and selects option `[3]`
- **THEN** the script prompts for endpoint URL, model name, and API key, and saves `AGENT_BACKEND="local_openai"` into `.env`.
