## Why

Testing `slash-agent` on a fresh Windows installation revealed several critical user experience and security friction points:
1. **Immediate Exit on Missing Prerequisite**: The installer prints a manual `winget` suggestion for Git/Python and exits, forcing the user to manually run multiple commands.
2. **Windows Defender / AMSI False Positives**: Piping raw web streams directly into `Invoke-Expression` (`irm ... | iex`) triggers AMSI heuristic flags (`Trojan:PowerShell/Command`) on Windows Defender.
3. **Microsoft Store App Alias False Positives**: `Get-Command python` matches zero-byte App Execution Aliases on Windows, leading to subsequent virtualenv creation failures.
4. **Execution Policy Blocking**: Default `ExecutionPolicy Restricted` blocks sourcing `slash-agent.ps1` from `$PROFILE` on new PowerShell sessions.
5. **Branch & Raw Link Misalignment**: Documentation and installation snippets referenced `/master/` instead of `main` or custom `$env:BRANCH` overrides.

Resolving these issues while ensuring total feature parity across PowerShell, Bash, Zsh, Ksh, and Fish installers will provide a seamless, 5-second onboarding experience on all operating systems.

## What Changes

* **Automated Prerequisite Installation (`installer.ps1`)**:
  * Prompt users to automatically install missing `git` or `Python.Python.3` via `winget`.
  * Refresh `$env:Path` in the running PowerShell process immediately after `winget` installation so prerequisites are available without restarting the shell.
  * Respect non-interactive CI/CD execution (`$env:NONINTERACTIVE`, `$env:CI`, `[Environment]::UserInteractive`).
* **AMSI & Windows Defender Prevention (`README.md` & `documentation.md`)**:
  * Replace memory-pipe `irm ... | iex` installation snippets with disk-backed Download-and-Run (`iwr ... -OutFile $env:TEMP\installer.ps1; & $env:TEMP\installer.ps1`) and `git clone` snippets.
  * Standardize raw GitHub URLs from `/master/` to `/main/`.
* **Python App Execution Alias Verification**:
  * Test functional execution (`python -c "import sys"`) rather than `Get-Command` to detect 0-byte Windows Store redirect stubs.
* **ExecutionPolicy & Profile Activation**:
  * Call `Unblock-File` on `slash-agent.ps1` to remove NTFS Zone.Identifier streams ("Downloaded from Internet").
  * Check `Get-ExecutionPolicy -Scope CurrentUser` and offer to set `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force`.
  * Print current-session dot-sourcing activation instructions at installer conclusion (`. "$HOME\.slash-agent\bin\slash-agent.ps1"`).
* **Cross-Shell Synchronization**:
  * Maintain exact functional parity and documentation sync across PowerShell (`installer.ps1`), Bash/Zsh/Ksh/Fish (`installer.sh`), and markdown documentation.

## Capabilities

### New Capabilities

*(None)*

### Modified Capabilities

- `simple-installer`: Add `winget` auto-installer with live path refresh, MS Store alias detection, AMSI-safe installation snippet guidelines, `Unblock-File` execution policy management, and cross-shell parity across PS/Bash/Zsh/Ksh/Fish.

## Impact

* **`bin/installer.ps1`**: Automated `winget` installation, live path refresh, functional python check, `Unblock-File`, and ExecutionPolicy helper.
* **`bin/installer.sh`**: Parity check for prerequisite installation hints across Linux/macOS package managers.
* **`README.md` & `docs/documentation.md`**: Updated installation snippets, AMSI Defender recommendations, and branch references.
