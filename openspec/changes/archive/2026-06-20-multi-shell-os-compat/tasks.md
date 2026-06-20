## 1. Shell Wrapper Implementation

- [x] 1.1 Update `bin/slash-agent.sh` with Zsh detection and dynamic script path resolution
- [x] 1.2 Implement Zsh history fallback capture in `bin/slash-agent.sh` using `fc -ln`
- [x] 1.3 Ensure ksh93 script path resolution works in `bin/slash-agent.sh`
- [x] 1.4 Create `bin/slash-agent.fish` to implement a native wrapper function for the Fish shell

## 2. Installer Script Upgrades

- [x] 2.1 Update `bin/installer.sh` to detect user login shell using the `$SHELL` environment variable
- [x] 2.2 Implement profile registration in `bin/installer.sh` for Zsh (`~/.zshrc`) and Ksh (`~/.kshrc` / `~/.profile`)
- [x] 2.3 Implement profile registration in `bin/installer.sh` for Fish (`~/.config/fish/config.fish`)
- [x] 2.4 Implement macOS-specific profile overrides in `bin/installer.sh` (`~/.bash_profile` or `~/.profile` for Bash)

## 3. Python Orchestrator and Temp Files

- [x] 3.1 Update `bin/slash-agent.sh` and `bin/slash-agent.fish` to create temporary files using POSIX-standard path templates
- [x] 3.2 Add `--shell` parameter support in `slash_agent/main.py`
- [x] 3.3 Implement Fish-compatible environment variable serialization in `slash_agent/main.py` when `--shell fish` is specified

## 4. Documentation & Verification

- [x] 4.1 Update `docs/documentation.md` to cover Zsh, Ksh, and Fish wrappers, environment synchronization, and installation profiles
- [x] 4.2 Update `README.md` to document Windows WSL2 compatibility and multi-shell quick-start setup
- [x] 4.3 Verify Bash, Zsh, Ksh, and Fish integrations execute tasks, capture tmux/history context, and synchronize parent shell states successfully
