## Context

Currently, `slash-agent` lacks a modular mechanism to teach the agent custom workflows (e.g., git conventions, packaging, or release pipelines) without modifying the Python source code. Introducing "agent skills" as files on disk allows users to dynamically extend the agent's procedural knowledge.

## Goals / Non-Goals

**Goals:**
- Enable discovery of skills from standard local directories (`.agent/skills/`, `.claude/skills/`, `.github/skills/`) and global configuration directories (`~/.config/slash-agent/skills/`, `~/.claude/skills/`, `~/.copilot/skills/`).
- Dynamically parse skill metadata (name, description) from `SKILL.md` files.
- Gracefully handle malformed or missing YAML frontmatter headers to ensure startup does not fail.
- Inject a clean skill index into the agent's startup `systemPrompt` (Recipe Sourcing model).
- Provide a silent, read-only tool to let the agent retrieve instructions on demand without prompting the user.

**Non-Goals:**
- Compiling dynamic Python wrapper tools at runtime.
- Implementing an MCP Client in this iteration.
- Restricting files to a custom YAML schema besides simple name/description headers.

## Decisions

### 1. Eager Prompt Indexing & On-Demand Reading Tool
We choose to inject only the **index of available skills** (names, descriptions, and file paths) into the baseline `systemPrompt`. The agent dynamically reads the full `SKILL.md` instructions when relevant.
* **Why**: This minimizes startup token cost.
* **Implementation**: We introduce a read-only, auto-confirmed tool named `read_skill_instructions(skill_path: str) -> str`. Because it is read-only, it returns the skill instructions directly to the agent without triggering the user's execution approval prompt (unlike `cat`), making the workflow completely seamless.

### 2. Standard-Library YAML Header Parsing & Fallbacks
We will parse YAML frontmatter headers in `SKILL.md` using a lightweight regex parser rather than adding third-party yaml parsing dependencies.
* **Fallback Strategy**: If parsing fails due to syntax errors, or if a required field like `name` or `description` is missing, the system will not crash. Instead:
  - The skill `name` will default to the directory name.
  - The `description` will default to a placeholder string (e.g., `"Custom skill from <directory_name>"`).

### 3. Project-Local Override Logic
If a skill with the same name exists in both global and project-local paths, the project-local skill overrides the global one.
* **Why**: This allows projects to define custom overrides for common tasks (like customized `git-commit` guidelines or test configurations).

## Risks / Trade-offs

- **[Risk]** The agent fails to read the skill instructions or executes incorrect paths.
  * **[Mitigation]** The system prompt index will provide absolute file paths to all discovered skills, ensuring the agent has direct, unambiguous paths to query `read_skill_instructions`.
- **[Risk]** The user modifies/deletes a skill file during a running session.
  * **[Mitigation]** Since the agent reads skills dynamically from the filesystem, it will always get the latest state of the file, which is an advantage.


