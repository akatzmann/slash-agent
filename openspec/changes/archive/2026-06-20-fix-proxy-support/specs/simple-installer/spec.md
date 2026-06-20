## ADDED Requirements

### Requirement: Local Probe Proxy Bypass
During the automated prerequisite check and configuration phase, the installer script SHALL bypass any configured system proxies when probing local service endpoints (specifically when checking Ollama models via `127.0.0.1` or `localhost`).

#### Scenario: Probing local Ollama behind a proxy
- **WHEN** the installer is executed in an environment with `http_proxy` configured and attempts to fetch Ollama models from `http://127.0.0.1:11434`
- **THEN** it SHALL bypass all proxy handlers, query the local Ollama instance directly, and retrieve the model list successfully.
