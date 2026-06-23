## Why

Currently, `slash-agent` only supports a hardcoded set of tools (`execute_command` and `request_user_input`) and lacks the ability to load modular, procedural recipes (skills). This makes it difficult to extend the agent with domain-specific workflows (such as conventional git commits, spec management, or test pipelines) without modifying the core Python codebase.

## What Changes

- **Standard Skill Discovery**: The agent will scan standard project-local (`.agent/skills/`, `.claude/skills/`, `.github/skills/`) and global configuration (`~/.config/slash-agent/skills/`, `~/.claude/skills/`, `~/.copilot/skills/`) directories at startup for subdirectories containing a `SKILL.md` file, enabling compatibility with existing Claude Code and Copilot skills.
- **Robust Frontmatter Parsing**: The agent will parse YAML frontmatter from `SKILL.md`. If the header is missing, incomplete, or malformed, the agent will gracefully fall back to folder-name-based naming and default description tags instead of failing startup.
- **System Prompt Integration**: The agent's baseline system prompt will be dynamically appended with a registry of available skills (showing name, description, and file path).
- **On-Demand Recipe Sourcing**: The agent will be instructed to inspect skill markdown files dynamically when relevant to the current task using terminal commands (e.g. `cat`).

## Capabilities

### New Capabilities
- `agent-skills`: Discovers, indexes, and enables dynamic loading of file-based procedural skill guidelines (SKILL.md) following standard formats and discovery paths.

### Modified Capabilities
- None

## Impact

- `slash_agent/main.py`: Scans standard skill paths on startup, parses YAML frontmatter with error-tolerant fallbacks, and appends the skills registry to the system prompt.
- `docs/skills-guide.md`: A new guide explaining directory formats, naming, and importing existing Claude/Copilot skills.

