## MODIFIED Requirements

### Requirement: Architecture and Component Documentation
The documentation SHALL describe the core components: the POSIX shell sourcing wrapper (supporting Bash, Zsh, Ksh), the Fish sourcing wrapper, the Python controller, and the PTY execution tool, explaining the complete execution lifecycle.

#### Scenario: Verification of component details
- **WHEN** the user reads the architecture section of `docs/documentation.md`
- **THEN** they find detailed descriptions of:
  - Sourcing `bin/slash-agent.sh` to inject the `/agent` wrapper function for Bash/Zsh/Ksh.
  - Sourcing `bin/slash-agent.fish` to inject the `/agent` wrapper function for Fish.
  - Sourcing temporary environment files to apply working directory updates (`cd`) and exports (utilizing standard Bourne export/unset or Fish-specific set commands).
  - The Python entrypoint `slash_agent/main.py` configuring client, backend, and LLM agent contexts.

---

## ADDED Requirements

### Requirement: Windows Compatibility Documentation
The documentation SHALL specify the compatibility requirements for Windows users, guiding them to use WSL2 (Windows Subsystem for Linux) as the supported environment.

#### Scenario: Windows developer reads compatibility guide
- **WHEN** a Windows developer checks the compatibility or installation section in `README.md`
- **THEN** they find clear documentation instructing them to use WSL2 (Ubuntu/Debian) to install and run the agent natively.
