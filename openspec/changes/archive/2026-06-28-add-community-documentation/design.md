## Context

`slash-agent` currently lacks formal open-source community guidelines, security policies, and issue templates. While code documentation exists under `docs/`, contributors need clear standards on setup, testing across supported shells, reporting security issues, and submitting bugs or features via GitHub.

## Goals / Non-Goals

**Goals:**
- Provide clear setup and testing instructions tailored specifically to `slash-agent` in `CONTRIBUTING.md`.
- Implement standard Contributor Covenant standards in `CODE_OF_CONDUCT.md`.
- Establish a clear security reporting policy in `SECURITY.md` pointing maintainer contact to `@akatzmann` and GitHub Private Vulnerability Reporting.
- Provide structured GitHub issue templates under `.github/ISSUE_TEMPLATE/` for bug reports and feature requests.

**Non-Goals:**
- Creating automated pytest test suites for `slash-agent` core in this change (manual shell verification instructions will be documented instead).
- Modifying existing core python or shell logic in `slash_agent/` or `bin/`.

## Decisions

- **Decision 1: Customize ISSUE_TEMPLATE for shell environment details**: Instead of generic environment inputs, `bug_report.yml` will explicitly request Shell Type (`Bash`, `Zsh`, `Fish`, `tmux`) and LLM Backend (`Ollama`, `OpenAI`, `Azure OpenAI`) to ensure faster issue triage.
- **Decision 2: Direct security reports to GitHub Private Vulnerability Reporting**: Rather than listing a personal email address, `SECURITY.md` directs security vulnerabilities to GitHub's private reporting feature and maintainer `@akatzmann`.
- **Decision 3: Highlight multi-shell verification in CONTRIBUTING.md**: Because `slash-agent` interacts with subshell environment syncing, `CONTRIBUTING.md` will explicitly outline how to test shell wrapper scripts in Bash, Zsh, and Fish.

## Risks / Trade-offs

- **[Risk]** Documentation drift if CLI options or shell parameters change. → **Mitigation**: Reference primary spec files (`docs/skills-guide.md`, `README.md`) rather than duplicating exact flag lists where possible.
