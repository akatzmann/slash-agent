## ADDED Requirements

### Requirement: WSL2 Host Network Integration Documentation
The documentation SHALL provide clear, concise guidelines for connecting `slash-agent` inside WSL2 to local LLM servers (like `llama.cpp` or `Ollama`) on the Windows host, documenting both Mirrored Networking and NAT Mode routing configurations.

#### Scenario: Windows developer reads about Mirrored Networking and NAT Mode configuration
- **WHEN** a developer checks the WSL2 host network integration guidelines in the technical documentation
- **THEN** they find:
  - Concise steps to configure Mirrored Networking (`networkingMode=mirrored`) inside `.wslconfig`.
  - A fallback configuration for NAT Mode routing using dynamic IP route resolution (`ip route show...`).
  - Security warnings explaining the implications of binding Windows-hosted LLM runners to `0.0.0.0`.
