## Why

To support external open-source contributors and maintain security and community standards, `slash-agent` needs standard repository governance documentation and issue templates. Currently, the repository lacks a `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, and GitHub issue forms.

## What Changes

- Add `CONTRIBUTING.md` detailing virtualenv setup, local CLI execution, multi-shell script verification (Bash/Zsh/Fish), Spec-Driven Development (OpenSpec) workflows, and custom skills development.
- Add `CODE_OF_CONDUCT.md` based on the Contributor Covenant standards.
- Add `SECURITY.md` outlining supported versions (`v0.1.x`) and reporting security issues privately to maintainers (`@akatzmann`).
- Add `.github/ISSUE_TEMPLATE/bug_report.yml` requesting specific environment details including Shell Type (Bash/Zsh/Fish/tmux) and LLM Backend (Ollama/OpenAI/Azure OpenAI).
- Add `.github/ISSUE_TEMPLATE/feature_request.yml` for requesting CLI capabilities or agent skill enhancements.

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `github-documentation`: Update the github-documentation specification to mandate standard repository community standards, security reporting policies, contributor guidelines, and structured GitHub issue templates.

## Impact

- Repository root community documentation (`CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`).
- GitHub repository configuration (`.github/ISSUE_TEMPLATE/`).
