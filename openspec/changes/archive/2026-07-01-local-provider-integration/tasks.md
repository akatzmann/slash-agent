## 1. Wizard Setup Updates

- [x] 1.1 Update the backend selection list in `bin/installer.sh` to include Option 3 for Local OpenAI API.
- [x] 1.2 Update the pre-population logic and choice mapping to map Option 3 to the standard `openai` backend.
- [x] 1.3 Implement prompts, suffix path sanitization (appending `/v1`), API key defaults, and model detection scripts for Option 3.

## 2. Documentation Updates

- [x] 2.1 Update `README.md`'s Privacy-First Advantage section to link to local provider documentation.
- [x] 2.2 Append the unified Local OpenAI-Compatible APIs integration section and comparison matrix to `docs/documentation.md`.

## 3. Verification

- [x] 3.1 Validate wizard Option 3 behaves correctly under both online (model probing) and offline (manual fallback) conditions.
- [x] 3.2 Validate suffix sanitization correctly appends `/v1` suffix.
- [x] 3.3 Verify generated config successfully dispatches completions using standard `openai` backend to local runners.
