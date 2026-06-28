## ADDED Requirements

### Requirement: Community Governance and Contribution Documentation
The repository MUST provide comprehensive contributor documentation (`CONTRIBUTING.md`), code of conduct standards (`CODE_OF_CONDUCT.md`), and security vulnerability reporting procedures (`SECURITY.md`).

#### Scenario: Contributor reviews community documentation
- **WHEN** a contributor visits the repository on GitHub or locally inspects repository governance files
- **THEN** they find clear setup steps in `CONTRIBUTING.md`, community behavior standards in `CODE_OF_CONDUCT.md`, and private vulnerability reporting instructions to `@akatzmann` in `SECURITY.md`.

---

### Requirement: GitHub Issue Forms for Bugs and Features
The repository MUST provide structured GitHub issue templates (`.github/ISSUE_TEMPLATE/bug_report.yml` and `.github/ISSUE_TEMPLATE/feature_request.yml`) to capture detailed reports.

#### Scenario: User submits a bug report via GitHub
- **WHEN** a user opens a new issue using the bug report template
- **THEN** the form prompts them for detailed environment info including Shell Type (Bash/Zsh/Fish/tmux) and LLM Backend (Ollama/OpenAI/Azure OpenAI).
