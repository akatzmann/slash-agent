## Why

`bin/installer.ps1` currently omits the `local_openai` backend option (llama.cpp, vLLM, SGLang, Xinference) and has backend menu numbering mismatches compared to `bin/installer.sh`. Aligning `installer.ps1` with `installer.sh` ensures feature parity and a consistent interactive configuration experience across Linux/macOS and Windows hosts.

## What Changes

* **Local OpenAI API Support in PowerShell Installer:** Add Option `[3] Local OpenAI API` to `bin/installer.ps1` to configure `local_openai` backend endpoints, models, and API keys.
* **Unified Backend Menu Numbering:** Align PowerShell backend menu numbers with `installer.sh` (`[1] OpenAI`, `[2] Ollama`, `[3] Local OpenAI API`, `[4] Azure OpenAI`, `[5] Dummy`).
* **Interactive Parameters:** Add optional temperature and top-p prompts to `installer.ps1` to match `installer.sh`.

## Capabilities

### New Capabilities

*(None)*

### Modified Capabilities

- `simple-installer`: Align `installer.ps1` backend options and numbering with `installer.sh`.

## Impact

* **`bin/installer.ps1`**: Add `local_openai` configuration branch, update menu prompts, and save `AGENT_BACKEND="local_openai"`.
