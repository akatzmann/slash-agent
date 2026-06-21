## Why

When users run `/agent -c` (which invokes `bin/installer.sh --configure`), the wizard is supposed to load the existing configurations from `.env` and use them as default options. However, due to a bug in the script, the variables `AGENT_ENDPOINT` and `AGENT_MODEL` are reset to empty strings right before the interactive prompts begin. This prevents the user's previously configured backend endpoint and model deployment name from being displayed as the default choices.

## What Changes

- Modify `bin/installer.sh` to preserve the values of `AGENT_ENDPOINT` and `AGENT_MODEL` when the user retains their current backend.
- Reset `AGENT_ENDPOINT` and `AGENT_MODEL` only if the user decides to switch to a different backend during the configuration flow.

## Capabilities

### New Capabilities
<!-- Leave empty as no new capabilities are being introduced -->

### Modified Capabilities
<!-- Leave empty as this is a bug fix to align the implementation with the existing "Support Configure-Only Mode with Pre-populated Defaults" requirement in the simple-installer spec -->

## Impact

- **Affected files**: `bin/installer.sh`
- **Behavioral impact**: The interactive configuration wizard (`/agent -c` or `bin/installer.sh --configure`) will correctly pre-populate the current values of `AGENT_ENDPOINT` and `AGENT_MODEL` as prompt defaults when keeping the same backend, ensuring a seamless re-configuration experience.
