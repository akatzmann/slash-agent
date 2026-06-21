## Why

Currently, the project lacks a clear, high-level comparative guide and positioning overview for developers. Developers looking at the repository need to quickly understand the boundaries of the tool (e.g. what it is vs. what it is not), its privacy-first model, and how it compares/coexists with other AI developer tools like browser Web UIs, shell copilots, and full-repo autonomous agents (e.g. Aider). 

## What Changes

We will introduce three new documentation and positioning sections:
1. **The 10-Second Reality Check**: A table outlining "What it IS" vs. "What it IS NOT" to set scope expectations immediately.
2. **The Privacy-First Advantage**: Outlining BYOK (Bring Your Own Key) and offline capabilities using local Ollama instances.
3. **Feature Comparison Matrix**: A detailed comparison matrix detailing how `slash-agent` compares against standard Web UIs, shell copilots, and project-level agents.

These sections will be placed:
- Near the top of `README.md` (for the Reality Check and Privacy-First sections)
- Within the middle of `README.md` and near the top of `docs/documentation.md` (for the Comparison Matrix)

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `github-documentation`: Requirements for both the repository README and technical documentation are updated to mandate project positioning, privacy features, and feature matrix comparisons.

## Impact

This change only modifies the documentation files (`README.md` and `docs/documentation.md`) and the relevant specification files. It has no functional impact on the Python orchestrator, shell hooks, or installer scripts.
