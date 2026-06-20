## Why

When the agent proposes shell commands for execution, it can be difficult for the user to understand the potential safety risks and criticality of complex or destructive commands. Introducing an automated, LLM-driven and rule-guided risk assessment printed right inside the confirmation dialogue prevents accidental system damage and improves developer oversight.

## What Changes

- **Command Risk Parameters**: Extend the `execute_command` tool signature with `risk_level` and `risk_description` parameters.
- **Python Guardrail Overrides**: Implement hardcoded safety overrides in Python to auto-promote known dangerous commands (like `rm -rf`, `sudo`, `chmod -R`) to critical risk level, guarding against LLM hallucinations.
- **Color-coded UI Display**: Output the risk assessment in distinct ANSI colors (Safe, Low, Moderate, Critical) right below the proposed command in the confirmation prompt.
- **`--unsafe-yes` Command-line Option**: Auto-confirming critical commands via `-y` / `--yes` will be disabled by default. A new flag `--unsafe-yes` must be supplied to bypass manual confirmation for critical-risk commands.
- **Documentation Updates**: Update `README.md` and `docs/documentation.md` to document the risk levels and the new override flag.

## Capabilities

### New Capabilities
- `command-risk-assessment`: Expose risk evaluation for proposed shell commands and enforce manual confirmation of critical actions unless overridden by a flag.

### Modified Capabilities

## Impact

- `slash_agent/tools.py`: Update `execute_command` and `prompt_user_confirmation` to process and print risk assessment details.
- `slash_agent/main.py`: Parse the new `--unsafe-yes` flag, pass confirmation flags to tools/session state, and update the system prompt to guide the LLM's self-assessment.
- `README.md`, `docs/documentation.md`: Add references for risk categories and `--unsafe-yes`.
