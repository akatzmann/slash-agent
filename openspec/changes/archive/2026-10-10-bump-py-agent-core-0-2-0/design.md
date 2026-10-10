## Context

See `proposal.md` for background and motivation. `slash-agent` previously pinned `py-agent-core` to `v0.1.2`, which lacked automatic `reasoning_effort="none"` fallback on `/v1/chat/completions` when function tools are attached. In addition, defaults in documentation and code referenced older models (`gpt-5.4-nano`) rather than `gpt-6.1-sol`.

## Goals / Non-Goals

**Goals:**
- Update `requirements.txt` to point directly to the newly tagged release `git+https://github.com/akatzmann/py-agent-core.git@v0.2.0`.
- Update backend initialization in `slash_agent/main.py` so that unresolved model names default to `gpt-6.1-sol` when `AGENT_BACKEND` is `openai` or `azure_openai`.
- Update `.env.template`, `bin/installer.sh`, `bin/installer.ps1`, `docs/documentation.md`, and `README.md` to reflect `gpt-6.1-sol` as the standard default model for OpenAI and Azure OpenAI backends.
- Ensure all existing unit tests in `slash-agent` pass cleanly.

**Non-Goals:**
- Modifying Ollama model defaults (`gemma4:latest` remains unchanged).
- Redesigning the agent CLI loop or adding new slash commands.

## Decisions

### Decision 1: Pin `py-agent-core` to `@v0.2.0` release tag
- **Rationale**: Pinned git tags ensure reproducible builds and avoid unexpected upstream breakages, while incorporating the reasoning fallback fixes in 0.2.0.
- **Alternatives Considered**: Using an unpinned branch like `@main` (rejected: risky for production/installer environments).

### Decision 2: Set `gpt-6.1-sol` as default for `openai` and `azure_openai`
- **Rationale**: `gpt-6.1-sol` is OpenAI's 2026 agentic workhorse model. With `py-agent-core` 0.2.0 handling tool-conflict fallback cleanly, `gpt-6.1-sol` works smoothly out of the box.
- **Alternatives Considered**: Keeping `gpt-5.4-nano` (rejected: older mid/nano model; user explicitly requested modernizing to current OpenAI models).

## Risks / Trade-offs

- **[Risk] Existing `.env` configurations might still specify `AGENT_MODEL="gpt-5.4-nano"`**:
  - *Mitigation*: Existing explicit user settings in `.env` continue to be respected as overrides; only defaults and setup templates change.
- **[Risk] Slower token generation on heavy reasoning queries**:
  - *Mitigation*: The `py-agent-core` 0.2.0 fallback forces `reasoning_effort="none"` during chat completion tool calling, keeping latency responsive during tool execution.
