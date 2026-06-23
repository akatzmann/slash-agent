# Agent Skills Spec

## Purpose
Defines the agent skills discovery, parsing, and integration system that allows users to extend the agent's procedural knowledge via modular `SKILL.md` files on disk.

---

## Requirements

### Requirement: Skill Discovery
The system SHALL scan the following directories at startup to identify installed skills:
- Global: `~/.config/slash-agent/skills/*/SKILL.md`, `~/.claude/skills/*/SKILL.md`, `~/.copilot/skills/*/SKILL.md`, `~/.gemini/config/skills/*/SKILL.md`
- Local: `.agent/skills/*/SKILL.md`, `.claude/skills/*/SKILL.md`, `.github/skills/*/SKILL.md`

#### Scenario: Discovered skills are indexed
- **WHEN** the agent starts and valid skill directories exist with SKILL.md files containing YAML headers
- **THEN** it parses the name and description from the YAML frontmatter of each file

### Requirement: Frontmatter Parsing Fallback
The system SHALL handle missing, malformed, or incomplete YAML frontmatter in `SKILL.md` files gracefully without failing startup.

#### Scenario: Missing or malformed YAML header
- **WHEN** a discovered `SKILL.md` has invalid YAML syntax or lacks a name or description field
- **THEN** the system falls back to using the parent folder name as the skill name, and a default description value ("Custom skill from <folder_name>"), and continues execution

### Requirement: Local Override Logic
The system SHALL resolve skill name collisions by letting project-local skills override global skills with the same name.

#### Scenario: Project-local skill overrides global skill
- **WHEN** a skill with name `git-commit` exists in both a global directory and a project-local directory
- **THEN** the system only indexes the project-local skill in the prompt and discards the global one

### Requirement: System Prompt Injection
The system SHALL dynamically inject a markdown summary index of all discovered skills into the system prompt prior to commencing the agent loop.

#### Scenario: Splicing skill list into prompt
- **WHEN** the agent constructs the final system prompt block
- **THEN** it appends a "# Available Agent Skills" section detailing each skill's name, description, and absolute file path

### Requirement: Skill Reading Tool
The system SHALL expose a read-only, auto-confirmed tool named `read_skill_instructions` that accepts the absolute `skill_path` and returns the file contents.

#### Scenario: Executing tool silently without confirmation
- **WHEN** the agent invokes `read_skill_instructions` with a valid absolute path to a skill file
- **THEN** the system returns the file contents to the agent directly without prompting the user for approval or confirmation
