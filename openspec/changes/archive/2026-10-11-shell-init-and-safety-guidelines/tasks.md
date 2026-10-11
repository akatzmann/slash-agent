## 1. Shell Init Implementation (TDD)

- [x] 1.1 Ensure isolated shell test environment (install `zsh`, `fish`, `mksh`) for real subshell execution
- [x] 1.2 Write test suite in `tests/test_shell_init.py` that executes generated initialization scripts inside real shell subprocesses (`bash`, `zsh`, `fish`, `mksh`) to verify syntax validity, function registration, `--cmd` aliases, and `--install` profile registration
- [x] 1.3 Create `slash_agent/shell_init.py` re-using proven context-capture mechanisms from `bin/slash-agent.sh`/`bin/slash-agent.fish` and profile resolution/registration logic from `bin/installer.sh`
- [x] 1.4 Integrate `init` subcommand into `slash_agent/main.py` CLI parser supporting optional `[shell]`, `--cmd`, and `--install` flags, ensuring all shell tests pass
- [x] 1.5 Add `--update` / `--upgrade` (`-u`) flag handling in shell wrappers and Python CLI to automatically trigger installation updates

## 2. Documentation & Disclaimers

- [x] 2.1 Reorganize `README.md` to place "Quick Start (5-Second Install)" directly below the AI pairing tip and right above the 10-Second Reality Check
- [x] 2.2 Add "🛡️ Best Practices & Responsible Usage" section to `README.md` covering token spend control, BYOK safety, and interactive execution
- [x] 2.3 Update `docs/documentation.md` and `docs/security_model.md` with explicit cost management guidelines and unattended execution precautions
- [x] 2.4 Update installation instructions in `README.md` to showcase `eval "$(slash-agent init bash)"` and `/agent --update`

## 3. Packaging & Distribution Setup

- [x] 3.1 Create `pyproject.toml` with `slash-agent` console script entry point and project metadata
- [x] 3.2 Verify package buildability via setuptools/wheel
- [x] 3.3 Configure PyPI Trusted Publishing workflow in `.github/workflows/publish.yml`
