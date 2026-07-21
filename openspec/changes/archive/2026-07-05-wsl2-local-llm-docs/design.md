## Context

When developers run local LLM runners (like `llama.cpp` or `Ollama`) natively on a Windows host and `slash-agent` inside WSL2, the default network isolation of WSL2 prevents connectivity to `localhost`. We need to document configurations to enable this connectivity while maintaining clean repo layout and clear security boundaries.

## Goals / Non-Goals

**Goals:**
- Provide clear, concise instructions for both Mirrored Networking and NAT Mode routing in `docs/documentation.md`.
- Keep the `README.md` clean by using a visually distinct note pointing to the main documentation.
- Maintain security awareness by explaining the trade-offs of both options (e.g. VPN issues for Mirrored mode, port exposure for NAT mode).

**Non-Goals:**
- Automate host-level or WSL-level configuration inside scripts or installer code.
- Provide general networking troubleshooting beyond connecting `slash-agent` to local LLM providers on Windows host.

## Decisions

### Decision 1: Neutral Presentation of Networking Modes
- **Option A**: Recommending Mirrored Networking as the primary choice.
- **Option B**: Presenting both Mirrored Networking and NAT Mode neutrally.
- **Chosen path**: Option B. Both options have distinct use cases. Mirrored networking is simple but has strict OS dependencies (Win 11) and can conflict with corporate VPNs. NAT mode is universally compatible but requires firewall configuration and exposing ports on `0.0.0.0`. Presenting both ensures developers choose the one fitting their constraints.

### Decision 2: Redirection Alert in README.md
- **Option A**: Write detailed instructions directly inside `README.md`.
- **Option B**: Keep `README.md` clean and link to `docs/documentation.md` using a GitHub Alert block (`> [!NOTE]`).
- **Chosen path**: Option B. This keeps the landing page uncluttered, avoids duplicating instructions (DRY principle), and targets only users seeking this capability.

### Decision 3: Concrete Port Examples
- **Option A**: Use generic placeholders like `<port>`.
- **Option B**: Use default ports (8080 for llama.cpp/local-openai, 11434 for Ollama) alongside brief explanations.
- **Chosen path**: Option B. This makes the commands copy-paste friendly and concrete, while keeping the explanations brief.

## Risks / Trade-offs

- **Risk**: User enables NAT mode and exposes local LLM servers to public/local LAN network interfaces.
  - *Mitigation*: Add an explicit security warning explaining the security implications of binding LLM servers to `0.0.0.0`.
- **Risk**: User enables Mirrored mode and their corporate VPN or local Kubernetes network stack breaks.
  - *Mitigation*: Clearly list the VPN conflict risk as a trade-off for Mirrored networking in the documentation.
