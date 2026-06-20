## 1. CLI and State Configuration Updates

- [x] 1.1 Add the `--unsafe-yes` option to the command-line argument parser in `slash_agent/main.py`.
- [x] 1.2 Add the `unsafe_confirm` attribute to the `ShellState` class in `slash_agent/tools.py`.
- [x] 1.3 Update the `system_prompt` in `slash_agent/main.py` with instructions for categorizing command risk levels and descriptions.

## 2. Core Tool Implementation

- [x] 2.1 Update the `execute_command` signature to accept `risk_level` and `risk_description`.
- [x] 2.2 Implement python-level pattern overrides in `execute_command` to set risk to critical for dangerous inputs (like `rm -rf`, `sudo`).
- [x] 2.3 Modify `prompt_user_confirmation` to render the risk classification using ANSI colors matching the safety categories.
- [x] 2.4 Integrate auto-confirm bypass logic to halt on critical commands even if `-y` is enabled, unless `--unsafe-yes` is present.

## 3. Documentation Updates

- [x] 3.1 Update `README.md` to document the new `--unsafe-yes` flag and command risk assessment display.
- [x] 3.2 Update `docs/documentation.md` to detail safety risk levels and confirmation overrides.

## 4. Verification

- [x] 4.1 Verify standard auto-confirm (`-y`) automatically runs low-risk commands but prompts for critical commands.
- [x] 4.2 Verify that `--unsafe-yes` bypasses confirmation prompts for critical commands.
- [x] 4.3 Verify that manual confirmation displays the correct colored risk headers and descriptions.
