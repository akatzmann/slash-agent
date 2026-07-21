## Context

When running shell commands under Windows, internal drive-specific environment variables (e.g. `=C:=C:\Users\...`) are returned in the environment block. During `parse_pty_result` parsing, splitting at `=` yields an empty key (`""`), which is stored in `session_state.env_vars`. When `get_env_diff` formats updates for PowerShell, it generates malformed `$env: = '...'` syntax that causes a `ParserError` when the temporary `.ps1` sync file is dot-sourced. Furthermore, users cannot install or test non-main branches directly using the installer scripts.

## Goals / Non-Goals

**Goals:**
* Filter out empty or internal environment key names starting with `=` during environment parsing and diff generation.
* Ensure PowerShell temporary `.ps1` sync files do not contain `$env:` syntax errors.
* Support an optional `BRANCH` / `$env:BRANCH` variable in `installer.sh` and `installer.ps1` to clone or check out specific git branches during installation and update.

**Non-Goals:**
* Implementing full git remote branch discovery or interactive branch selector UI inside installer scripts.

## Decisions

### 1. Robust Environment Key Sanitization
* **Key Validation:** In `slash_agent/tools.py` (`parse_pty_result`), check `k_str = k.decode("utf-8", errors="ignore").strip()`. If `not k_str or k_str.startswith("=")` skip inserting into `env_updates`.
* **Diff Generator Guard:** In `slash_agent/main.py` (`get_env_diff`), add `if not k or not k.strip() or k.startswith('='): continue` before appending any shell export/setter statements.

### 2. Branch Parameter Support in Installers
* **Bash Installer (`bin/installer.sh`)**:
  * Read `BRANCH="${BRANCH:-}"`.
  * If `$BRANCH` is non-empty, pass `-b "$BRANCH"` to `git clone`.
  * In update mode, if `$BRANCH` is non-empty, run `git checkout "$BRANCH"` before `git pull`.
* **PowerShell Installer (`bin/installer.ps1`)**:
  * Read `$Branch = if ($env:BRANCH) { $env:BRANCH } else { $null }`.
  * If `$Branch` is set, pass `-b $Branch` to `git clone`.
  * In update mode, if `$Branch` is set, run `git checkout $Branch` before `git pull`.

## Risks / Trade-offs

* **[Risk]** User specifies a non-existent branch name during installation.
  * *Mitigation:* The installer checks `git clone` / `git checkout` exit status codes and halts with a clear error message if the branch cannot be checked out.
