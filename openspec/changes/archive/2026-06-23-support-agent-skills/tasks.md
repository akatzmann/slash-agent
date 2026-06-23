## 1. Skill Discovery and Parsing

- [x] 1.1 Add helper function in `slash_agent/main.py` to locate global (`~/.config/slash-agent/`, `~/.claude/`, `~/.copilot/`) and project-local (`.agent/`, `.claude/`, `.github/`) skills directories.
- [x] 1.2 Implement lightweight YAML frontmatter parser in `slash_agent/main.py` to read name and description from `SKILL.md` files, incorporating folder-name and default description fallbacks for malformed/missing headers.
- [x] 1.3 Implement local override logic to deduplicate skills with the same name, prioritizing project-local paths over global paths.

## 2. System Prompt & Tool Integration

- [x] 2.1 Modify system prompt assembly in `slash_agent/main.py` to dynamically construct and append the `# Available Agent Skills` index section.
- [x] 2.2 Implement the `read_skill_instructions` tool in `slash_agent/tools.py` as an auto-confirmed, read-only tool that returns file content.
- [x] 2.3 Update prompt guidelines instructing the agent to call the `read_skill_instructions` tool to retrieve skill files silently.

## 3. Documentation & Verification

- [x] 3.1 Write `docs/skills-guide.md` outlining naming conventions and step-by-step layout for authoring or importing custom skills from Claude/Copilot formats.
- [x] 3.2 Set up test skills in `.agent/skills/` and `.claude/skills/`, including one with a malformed YAML header, to verify robust discovery.
- [x] 3.3 Run manual verification tests using dry-run mode (`/agent -n`) to verify that the skills index (including overrides and fallbacks) is correctly injected, and that the `read_skill_instructions` tool executes silently.


