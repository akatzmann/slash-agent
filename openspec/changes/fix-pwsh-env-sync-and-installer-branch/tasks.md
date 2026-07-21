## 1. Environment Parsing & Diff Generation Sanitization

- [x] 1.1 Filter out empty keys and keys starting with `=` in `parse_pty_result` inside `slash_agent/tools.py`.
- [x] 1.2 Add empty and `=` key guard filters in `get_env_diff` inside `slash_agent/main.py`.

## 2. Installer Branch Support

- [x] 2.1 Add `BRANCH` variable support and git branch clone/checkout handling to `bin/installer.sh`.
- [x] 2.2 Add `$env:BRANCH` variable support and git branch clone/checkout handling to `bin/installer.ps1`.

## 3. Verification

- [x] 3.1 Verify environment sync file generation with internal `=` keys.
- [x] 3.2 Verify installer branch cloning logic.
