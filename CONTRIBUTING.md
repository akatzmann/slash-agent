# Contributing to slash-agent

Thank you for your interest in contributing to `slash-agent`! We welcome bug fixes, shell integration improvements, documentation updates, and new agent skills.

Please follow these guidelines to make the contribution process smooth and efficient.

---

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please report any unacceptable behavior to project maintainer `@akatzmann`.

---

## Local Development Setup

To set up a local development environment:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/akatzmann/slash-agent.git
   cd slash-agent
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows/WSL2: source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   Copy `.env.template` to `.env` (or set user environment variables) to configure your local LLM endpoint or API keys:
   ```bash
   cp .env.template .env
   ```

---

## Testing Local CLI Execution

You can run the core Python agent loop directly without sourcing shell wrappers:

```bash
python3 -m slash_agent.main "List files in the current directory"
```

### Dry-Run & Safe Verification
To test agent reasoning and tool call generation without modifying your system or executing live terminal commands, use dry-run mode:
```bash
python3 -m slash_agent.main -n "Create a test file"
```

---

## Verifying Shell Integrations

`slash-agent` operates by syncing subshell execution state (environment exports and working directory `cd`) back to parent shell sessions.

When modifying wrapper scripts in `bin/`, verify behavior across supported shells:

* **POSIX Shells (Bash / Zsh)**:
  Source the wrapper script directly in a test terminal session:
  ```bash
  source bin/slash-agent.sh
  /agent "Check current directory"
  ```
* **Fish Shell**:
  Source the Fish wrapper in a `fish` shell session:
  ```fish
  source bin/slash-agent.fish
  /agent "Check current directory"
  ```
* **Installer Script**:
  Verify modifications to `bin/installer.sh` in a disposable test environment or container.

---

## Spec-Driven Development (OpenSpec)

`slash-agent` follows **Spec-Driven Development** using [OpenSpec](https://github.com/Fission-AI/openspec). All feature additions, capability modifications, and core architectural changes are designed and verified against specifications (located under `openspec/`) before implementation.

### Core Concepts
* **Main Specifications (`openspec/specs/`)**: Define normative requirements (`SHALL`/`MUST`) and scenario tests (`WHEN`/`THEN`) for core capabilities such as shell wrappers, file tools, and backend adapters.
* **Change Artifacts (`openspec/changes/`)**: Each non-trivial modification is structured as an OpenSpec change containing a proposal (`proposal.md`), technical design (`design.md`), delta specs (`specs/**/*.md`), and task tracking (`tasks.md`).

### Contributing Spec Changes
1. **Explore Existing Specs**: Check `openspec/specs/` to understand current requirements before proposing architectural changes.
2. **Propose & Design**: Create an OpenSpec change (e.g. `openspec new change <change-name>`) and document the technical design and delta specifications.
3. **Implement & Verify**: Complete implementation tasks linked to the change specifications before submitting your pull request. When developing with `slash-agent`, interactive agent workflows (`/opsx-explore`, `/opsx-propose`, `/opsx-apply`) assist in managing OpenSpec changes.

---

## Agent Skills & Extensions

`slash-agent` supports drop-in agent skills placed in `.agent/skills/`, `.claude/skills/`, `.github/skills/`, or global paths (`~/.gemini/config/skills/`).

If you are contributing new skills or modifying skill execution behavior:
* Consult [`docs/skills-guide.md`](docs/skills-guide.md) for skill formatting rules and `SKILL.md` specifications.
* Ensure skill instructions remain modular and self-contained.

---

## Submitting Pull Requests

1. Create a descriptive feature branch (`git checkout -b feature/my-cool-fix`).
2. Ensure code is clean, well-commented, and preserves existing function docstrings.
3. Verify that manual dry-run tests and shell script sourcings pass without errors.
4. Push your branch and open a Pull Request against `main`.
