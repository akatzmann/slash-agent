# 🛠️ slash-agent: Skills Guide

This guide explains how to use, install, and author custom **Agent Skills** in `slash-agent`.

---

## 🧠 What is an Agent Skill?

An **Agent Skill** is a modular directory containing a `SKILL.md` file. It allows you to teach `slash-agent` complex workflows, design guides, or procedural tasks (such as git commit formatting rules, test guidelines, or system release checklists) without writing Python code or bloating the base LLM prompt.

### Progressive Recipe Sourcing
To keep token counts minimal and startup zero-latency, `slash-agent` only injects a small index of available skills into the initial system prompt. The agent dynamically queries and reads the full instructions of a skill on-demand during a task run.

---

## 📂 Folder Layout

Every skill must have a directory containing at least a `SKILL.md` file at the root:

```text
your-skill/
├── SKILL.md          # Required: YAML metadata frontmatter + Markdown body
├── scripts/          # Optional: Custom helper scripts executed by the agent
└── templates/        # Optional: File templates or boilerplate
```

### The `SKILL.md` File Format
`SKILL.md` uses standard YAML frontmatter for programmatic indexing and a standard Markdown body for agent instructions.

```markdown
---
name: git-commit-helper
description: Guidelines for generating conventional commits and auditing diffs.
---
# Git Commit Helper Instructions
When the user asks to commit their changes, you must:
1. Run `git status` to see what is modified.
2. Group changes logically into conventional categories (feat, fix, refactor).
3. Draft a commit message following the conventional commits spec.
```

* **`name`** (Optional): A unique identifier for the skill. If omitted, the system falls back to the parent folder name.
* **`description`** (Optional): A concise explanation of the skill. If omitted, defaults to a standard fallback description.

---

## 📦 Discovery Directories

`slash-agent` automatically scans the following locations at startup. Skills are read **in-place** — no copying or migration needed.

### 1. Project-Local Skills (Shared with Teams)
Skills stored inside the active git repository are picked up automatically:
* `.agent/skills/`
* `.claude/skills/`
* `.github/skills/`

### 2. Global Skills (Personal Machine)
Skills stored in your user configuration directories are picked up across all repositories:
* `~/.config/slash-agent/skills/`
* `~/.claude/skills/`
* `~/.copilot/skills/`
* `~/.gemini/config/skills/`

### 🔄 Local Override Rule
If a skill with the same name exists in both global and project-local paths, the project-local skill **always overrides** the global version. This allows individual codebases to customize standard behaviors.

---

## 🤝 Claude Code, GitHub Copilot & Gemini Compatibility

`slash-agent` uses the **standard open SKILL.md format** and scans the same directories as Claude Code, Copilot, and Gemini. If you already have skills installed for any of those tools, `slash-agent` picks them up automatically with no extra steps — they stay exactly where they are.
