## 1. Automated Prerequisites & Windows Installer Enhancement

- [x] 1.1 Update `bin/installer.ps1` with functional Python validation (`python -c "import sys"`) to bypass Microsoft Store App Execution Alias false-positives.
- [x] 1.2 Add automated `winget` installation prompts for missing Git (`Git.Git`) and Python (`Python.Python.3.12`) in `bin/installer.ps1`, with live `$env:Path` process environment refresh.
- [x] 1.3 Add `Unblock-File` call and `ExecutionPolicy` detection/configuration (`RemoteSigned -Scope CurrentUser`) to `bin/installer.ps1`.
- [x] 1.4 Add non-interactive CI guard (`$env:NONINTERACTIVE`, `$env:CI`) and current-session dot-sourcing activation notices to `bin/installer.ps1`.

## 2. Anti-AMSI Documentation & Quickstart Sync

- [x] 2.1 Update `README.md` and `docs/documentation.md` quickstart installation snippets to use disk-backed Download-and-Run (`iwr ... -OutFile $env:TEMP\installer.ps1`) and `git clone` options.
- [x] 2.2 Standardize all raw GitHub URLs from `/master/` to `/main/` across documentation and installer scripts.
- [x] 2.3 Verify full feature parity and raw URL consistency between `bin/installer.ps1` and `bin/installer.sh` (supporting Bash, Zsh, Ksh, and Fish).

## 3. Verification

- [x] 3.1 Verify static script syntax and execution policy handling in `bin/installer.ps1` and `bin/installer.sh`.
- [x] 3.2 Run test suite `.venv/bin/python3 -m unittest discover tests` to ensure zero regressions.
