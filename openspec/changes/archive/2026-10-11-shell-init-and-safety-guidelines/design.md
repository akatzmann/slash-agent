## Context

Currently, `slash-agent` relies on sourcing relative scripts (`bin/slash-agent.sh` and `bin/slash-agent.fish`) which locate `.venv/bin/python3` relative to repo directories. To support package-based installation (`pip`, `pipx`, package managers) and multi-shell integration, the CLI must dynamically emit shell code targeting the installed `slash-agent` executable.

Furthermore, with wider public exposure, clear and reassuring safety and cost best practice guidelines must be documented without alarming prospective users.

## Goals / Non-Goals

**Goals:**
- Provide `slash-agent init [shell]` returning sourceable integration scripts for Bash, Zsh, Ksh, and Fish (auto-detecting active shell if omitted).
- Support `--install` flag to idempotently register the integration into the active shell's RC file by reusing the profile detection logic from `installer.sh`.
- Support `--cmd` flag to let users customize the shell alias/function name.
- Support `--update` / `--upgrade` (`-u`) flag to update the installation in place.
- Embed shell templates directly within the package so the installed CLI is completely self-contained.
- Reorganize `README.md` to position Quick Start immediately below the AI pairing tip and above the 10-Second Reality Check.
- Add clear, non-intrusive "Best Practices: Safety, Cost & Responsible Usage" sections to `README.md` and `docs/`.
- Provide `pyproject.toml` with console script entry point `slash-agent`.

**Non-Goals:**
- Modifying the underlying agent core loop or PTY bridge execution model.

## Decisions

### 1. Re-using Existing Shell & Installation Mechanisms
- **Decision:** Extract and re-use the exact shell integration mechanisms from `bin/slash-agent.sh` / `bin/slash-agent.fish`, as well as the shell profile resolution and idempotent registration logic from `bin/installer.sh` (lines 573-618).
- **Rationale:** `bin/installer.sh` already possesses robust, tested logic for identifying the active shell, determining OS differences (e.g. macOS `~/.bash_profile` vs Linux `~/.bashrc`, `~/.config/fish/config.fish`, `~/.kshrc`, `~/.zshrc`), and safely checking/appending lines via idempotent grep checks. Re-using this logic in `slash_agent/shell_init.py` ensures consistent behavior whether the user installed via `curl ... | bash` or via `pipx` followed by `slash-agent init --install`.

### 2. Isolated TDD with Actual Shell Binaries
- **Decision:** Test the emitted integration code directly against real shell interpreters (`bash`, `zsh`, `fish`, `mksh`) in isolated subshells via `pytest`.
- **Rationale:** Testing only string generation in Python is insufficient; we must execute `eval "$(<init>)"` inside actual shell processes to verify syntax validity, function registration, and parameter handling across all supported shell interpreters.

### 3. Documentation Flow and Best Practices Placement
- **Decision:** Move "Quick Start (5-Second Install)" directly below the AI pairing tip and right above the "10-Second Reality Check". Place the "🛡️ Best Practices & Responsible Usage" section directly under the Privacy & Security Model.
- **Rationale:** Visitors immediately see the copy-pasteable installation line before deciding whether to read deeper architecture comparisons. Framing token costs and command confirmations as "Best Practices" keeps it constructive and professional.

### 4. Self-Update / Self-Upgrade Handling
- **Decision:** Intercept `--update`, `--upgrade`, and `-u` both in the shell integration functions and inside Python `main.py`.
- **Rationale:** In git installations (e.g. `~/.slash-agent`), running `/agent --update` executes `installer.sh` (which pulls latest git commits and refreshes virtualenv requirements). In package installations (pipx), it provides the direct upgrade command (`pipx upgrade slash-agent`).

## Risks / Trade-offs

- **[Risk]** Shell escaping or subshell syntax differences across older bash/zsh versions.
  - **Mitigation:** Keep shell functions minimal and match existing tested logic from `bin/slash-agent.sh` and `bin/slash-agent.fish`.
- **[Risk]** User shells where `/` character is forbidden in function names.
  - **Mitigation:** Emitted scripts define both `/agent` and `agent` (or custom `--cmd`), falling back gracefully.
