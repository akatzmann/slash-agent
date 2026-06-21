## Context

The `slash-agent` project currently lacks direct, high-level developer positioning, scope definitions, and comparison tables. We will resolve this by placing the "10-Second Reality Check", "Privacy-First Advantage", and "Feature Comparison Matrix" into `README.md` and `docs/documentation.md`.

## Goals / Non-Goals

**Goals:**
- Provide clear expectations for developers regarding what `slash-agent` is and is not.
- Highlight the privacy advantages of standard BYOK and offline local-only configurations using Ollama.
- Provide a side-by-side comparison matrix showing where `slash-agent` stands in relation to other AI tools (Web UIs, Shell Copilots, Project Agents).
- Ensure references to supported shells (Zsh, Bash, Fish, Ksh) are accurate and fully integrated.

**Non-Goals:**
- Modifying any logic within the Python orchestrator or terminal hooks.
- Introducing new environment variables or installation steps.

## Decisions

### Decision 1: Text Copy Placement & Structure
- **Choice:** Format the "Reality Check" and "Feature Comparison" as clean markdown tables instead of long bullet points or paragraphs.
- **Rationale:** Tables are much easier to scan at a glance. They clearly separate the categories and align columns cleanly, giving a highly premium feel.
- **Alternatives Considered:** 
  - Plain bulleted lists (rejected as they feel generic and basic, failing to "wow" the developer at first glance).

### Decision 2: Location within README.md
- **Choice:**
  - "Reality Check" and "Privacy-First" go near the top of the README, directly after the main introductory block quote (line 15) and before the "Quick Start" section.
  - "Feature Comparison" goes right after the "Common Use Cases" section (line 80) and before "How it Works".
- **Rationale:** 
  - Placing the Reality Check and Privacy-First details at the top instantly sets developer expectations and addresses security/overhead concerns before they even read how to install it.
  - Placing the comparison matrix after use cases naturally answers the question: *"I see the use cases, but how does this tool compare to what I already use?"*

### Decision 3: Location within docs/documentation.md
- **Choice:** Place the Feature Comparison Matrix at the top of the technical documentation, directly after the first introductory paragraph (line 5) and before the "System Architecture" diagram.
- **Rationale:** Technical documentation is a key resource for deep dives. Providing the comparison matrix early gives technical readers immediate context on the system's role before explaining its internal architecture.

## Risks / Trade-offs

- **[Risk] Repetitive content between README.md and docs/documentation.md**
  - *Mitigation*: Keep the Comparison Matrix synchronized between both files but customize the surrounding text context. The README version points to use cases, while the technical documentation version leads directly into the system architecture explanation.
